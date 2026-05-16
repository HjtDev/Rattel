from django.utils.module_loading import import_string
from django.utils.decorators import method_decorator
from RattelBackend.mixins import ResponseBuilderMixin, GetDataMixin
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Transaction
from .serializers import TransactionSerializer
from RattelBackend.cache import drf_cached_response, invalidate_cache
from django.urls import reverse
from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status


_gateway_provider = None

def get_gateway_provider():
    global _gateway_provider
    if _gateway_provider is None:
        _gateway_provider = import_string(settings.GATEWAY_PROVIDER)
    return _gateway_provider
    

class PaymentStartView(APIView, ResponseBuilderMixin, GetDataMixin):
    """
    Starts a payment session using the gateway provider, and returns the gateway url if it was successful.
    Set GATEWAY_PROVIDER in settings.py
    """
    
    permission_classes = (IsAuthenticated,)  # Only authenticated users can access this endpoint
    throttle_scope = 'payment-start'  # 3 calls per minute
    
    def post(self, request):
        """
        Initiates the payment session.
        Expected payload: {
            amount: int ==> Bigger than 1000,
            success_url: str ==> The success_url is where transaction_id and identifier would be sent when the payment was successful.
            fail_url: str ==> The fail_url is where transaction_id and identifier would be sent when transaction fails.
            description: str ==> Description of the transaction,
            identifier: str ==> Transaction identifier(order_id, wallet_charge_id, ...)
        }
        """
        
        # Checks and validates the four requirements and extracts them from request.
        success, result = self.get_data(
            request,
            ('amount', lambda a: isinstance(a, int) or (isinstance(a, str) and a.isdigit())),  # in IRR
            ('success_url', self.is_url),  # Full URL to where transaction_id and identifier would be sent on success
            ('fail_url', self.is_url),  # Full URL to where transaction_id and identifier would be sent on fail
            'description',
            'identifier',
        )
        
        # Issue in the base four requirements.
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )
        
        extra_kwargs = {
            'allowed_cards': request.data.get('allowed_cards', None),
            'national_code': request.data.get('national_code', None),
            'check_mobile_with_cart': request.data.get('check_mobile_with_cart', None),
            'extra_info': {
                'success_url': result['success_url'],
                'fail_url': result['fail_url'],
                'user_id': request.user.id
            },
        }
        extra_kwargs = {key: value for key, value in extra_kwargs.items() if value is not None}
        
        gateway = get_gateway_provider()(settings.MERCHANT)  # Initializes the gateway provider
        
        # Attempts to create a gateway with the required amount and options
        try:
            success, result = gateway.start_payment(
                amount=int(result['amount']),
                callback_url=request.build_absolute_uri(reverse('payment:payment-callback')),
                description=result['description'],
                identifier=result['identifier'],
                phone=request.user.phone,
                reason=Transaction.TransactionReason.PAYMENT,
                **extra_kwargs  # allowed_cards, national_code, check_mobile_with_cart, extra_info(final_url)
            )
        
            if success:
                result = gateway.build_gateway_url(result)  # Creates a full URL to gateway if the session is started.
            else:
                return self.build_response(  # Failed to start a payment session.
                    success=success,
                    error=-2,
                    message=result
                )
        
            return self.build_response(  # Success
                success=success,  # True
                gateway=result,  # Full URL to gateway
                message='Session started.'
            )
        except (ValueError, TypeError) as e:
            return self.build_response(  # Provider rejected the data(arguments we passed to it)
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-3,
                message=str(e)
            )
        

class PaymentCallbackView(APIView, ResponseBuilderMixin, GetDataMixin):
    """
    Receives callback data from gateway and processes it.
    After processing the data and validating its integrity it tries to redirect user to their requested URL with transaction_id and identifier as query_params
    """
    
    permission_classes = (AllowAny,)  # Since this endpoint is called by the gateway we may not have the user available everytime
    throttle_scope = 'payment-callback'  # 600 calls per minute
    
    def get(self, request):
        """
        Processes the callback data, and redirects user to success_url
        Expected query params: {
            success: int | bool  ==> Indicates payment succession,
            trackId: int | str ==> Gateway track id to find the payment session,
            orderId: str ==> Identifier for the payment session that used in "payment-start" endpoint,
            status: int | str ==> Payment status(Paid, Canceled, Insufficient credit, ...)
        }
        """
        
        # Checks and validates the four requirements and extracts them from request.
        success, result = self.get_data(request, 'success', 'trackId', 'orderId', 'status')
        
        # Incomplete/Invalid callback data
        if not success:
            return self.build_response(
                status.HTTP_406_NOT_ACCEPTABLE,
                success=success,  # False
                errors=-1
            )
        
        gateway = get_gateway_provider()(settings.MERCHANT)  # Initializes the gateway provider
        
        # Saves device metadata to store them with transaction
        device_metadata = {
            'FORWARD_IP': request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0],
            'REMOTE_ADDR': request.META.get('REMOTE_ADDR', ''),
            'USER_AGENT': request.META.get('HTTP_USER_AGENT', ''),
            'REFERER': request.META.get('HTTP_REFERER', ''),  # Should be the official gateway provider URL
            'LANGUAGE': request.META.get('HTTP_LANGUAGE', ''),
        }
        
        # Checks the integrity of payment
        # metadata ==> transaction_id, extra_info, paid_at, masked_card_number, status, amount, reference_number, description, identifier, message(from gateway)
        payment_valid, metadata = gateway.validate_gateway_response(result, metadata=device_metadata)
        
        # Safe fallback for metadata
        if metadata is None:
            metadata = dict()
        
        # Extracts success_url and fail_url
        extra_info: dict | None = metadata.get('extra_info', None)
        
        if not extra_info or extra_info.get('fail_url') is None or extra_info.get('success_url') is None:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Transaction failed. Failed to extract payment redirect URLs.'
            )
        success_url: str = extra_info['success_url'].strip()
        fail_url: str = extra_info['fail_url'].strip()
        
        if not payment_valid:  # it should redirect to a Payment failed or canceled page
            if not fail_url.endswith('/'):
                fail_url += '/'
            return redirect(f'{fail_url}?identifier={metadata.get('identifier')}&transaction_id={metadata.get('transaction')}')
        
        
        # Adding / to final url to prevent issues with older devices
        if not success_url.endswith('/'):
            success_url += '/'

        # Invalidate Cached Transactions
        invalidate_cache('my_transactions', request)
        
        # Redirecting user to success_url with transaction_id and identifier
        return redirect(f'{success_url}?identifier={metadata.get('identifier')}&transaction_id={metadata.get('transaction')}')


class MyTransactionsView(APIView, ResponseBuilderMixin):
    """
    API endpoint for retrieving authenticated user's transaction history.
    
    Permissions:
        - Requires authentication
    
    Throttling:
        - Uses the `main-throttle` scope -> 500/min
    
    Caching:
        - TTL: 5 minutes (300 seconds)
        - Cache prefix: 'my_transactions'
        - User-aware caching
    """
    
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'
    
    @method_decorator(
        drf_cached_response(
            ttl=300,
            cache_prefix='my_transactions',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        """
        Retrieve the authenticated user's transaction history.
        
        Returns transactions ordered by creation date (newest first).
        
        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - transactions: List of serialized transaction data
        """
        # Get user's transactions ordered by newest first
        transactions = (
            Transaction.objects
            .filter(user=request.user)
            .order_by('-created_at')
        )
        
        # Serialize the transactions
        serializer = TransactionSerializer(transactions, many=True)
        
        # Return success response
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            transactions=serializer.data,
        )
    
