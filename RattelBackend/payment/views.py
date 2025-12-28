from django.utils.module_loading import import_string
from RattelBackend.mixins import ResponseBuilderMixin, GetDataMixin
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Transaction
from django.urls import reverse
from django.shortcuts import redirect
from django.conf import settings
from rest_framework import status


GATEWAY_PROVIDER = import_string(settings.GATEWAY_PROVIDER)

class PaymentStartView(APIView, ResponseBuilderMixin, GetDataMixin):
    """
    Starts a payment session using the gateway provider, and returns the gateway url if it was successful.
    Set GATEWAY_PROVIDER in settings.py
    """
    
    permission_classes = (IsAuthenticated,)  # Only authenticated users can access this endpoint
    throttle_rate = 'payment-start'  # 3 calls per minute
    
    def post(self, request):
        """
        Initiates the payment session.
        Expected payload: {
            amount: int ==> Bigger than 1000,
            final_url: str ==> The final url where transaction_id and identifier would be sent,
            description: str ==> Description of the transaction,
            identifier: str ==> Transaction identifier(order_id, wallet_charge_id, ...)
        }
        """
        
        # Checks and validates the four requirements and extracts them from request.
        success, result = self.get_data(
            request,
            ('amount', lambda a: isinstance(a, int) or (isinstance(a, str) and a.isdigit())),  # in IRR
            ('final_url', self.is_url),  # Full url to where transaction_id and identifier would be sent
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
            'extra_info': {'final_url': result['final_url']},
        }
        extra_kwargs = {key: value for key, value in extra_kwargs.items() if value is not None}
        
        gateway = GATEWAY_PROVIDER(settings.MERCHANT)  # Initializes the gateway provider
        
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
                    messsage=result
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
    
    permission_classes = (IsAuthenticated,)  # Only authenticated users can access this endpoint.
    throttle_rate = 'payment-callback'  # 600 calls per minute
    
    def get(self, request):
        """
        Processes the callback data, and redirects user to final_url
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
        
        gateway = GATEWAY_PROVIDER(settings.MERCHANT)  # Initializes the gateway provider
        
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
        payment_valid, metadata = gateway.validate_gateway_response(result, user=request.user, metadata=device_metadata)
        
        if not payment_valid:  # it should redirect to a Payment failed or canceled page
            return self.build_response(  # User canceled the payment, or it was invalidated by gateway provider.
                status.HTTP_406_NOT_ACCEPTABLE,
                success=payment_valid,
                error=-2,
                message=f'Could not validate the transaction. Transaction is saved in failed status.\nTransaction ID: {metadata.get('transaction')}\nIdentifier: {metadata.get('identifier')}'
            )
        
        # Extracts final_url
        extra_info: dict | None = metadata.get('extra_info', None)
        final_url: str = extra_info.get('final_url', '').strip()
        
        if not final_url:  # If there is no final_url even on successful payment we can't finalize the process, but the payment will be stored in success state unlocked
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,  # True,
                error=-3,
                message=f'Transaction was successful but we did not find any URL to redirect to. Please contact site administrators.\nTrack ID:{result['trackId']}\nIdentifier:{result['orderId']}'
            )
        
        # Adding / to final url to prevent issues with older devices
        if not final_url.endswith('/'):
            final_url += '/'
        
        # Redirecting user to final_url with transaction_id and identifier
        return redirect(f'{final_url}?identifier={metadata.get('identifier')}&transaction_id={metadata.get('transaction')}')
    