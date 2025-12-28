from .base import BaseProvider, GatewayResult
from urllib.parse import urlparse
from warnings import warn
from RattelBackend.mixins import GetDataMixin
from django.core.cache import cache
from typing import Any, Dict
from payment.models import Transaction
import logging, requests


logger = logging.getLogger(__name__)


class ZibalGateway(BaseProvider):
    """
    Using this model you can communicate with Zibal REST API to create and manage gateways(paywalls).
    """
    
    def __init__(self, merchant: str = 'zibal', cache_prefix: str = 'zibal'):
        """
            Initializes Zibal Gateway provider with merchant ID.
        """
        
        # Merchant is can be both number and string but the API always receives it in string form.
        if not isinstance(merchant, str):
            raise TypeError('merchant must be a string')
        if not merchant.strip():
            raise ValueError('Provide a valid merchant')
        
        self.merchant = merchant
        
        # Validating cache_prefix
        if not isinstance(cache_prefix, str):
            raise TypeError('cache_prefix must be a string.')
        if not cache_prefix.strip():
            raise ValueError('cache_prefix should not be an empty string.')
        
        # Setting cache prefix for different parts
        self.cache_prefix = cache_prefix
        self._start_cache_prefix = f'{self.cache_prefix}-started'
        
        # Updated Zibal API URL
        self.start_url = 'https://gateway.zibal.ir/v1/request/'
        self.gateway_url = 'https://gateway.zibal.ir/start/{}/'
        self.verify_url = 'https://gateway.zibal.ir/v1/verify/'
        
        
    def _check_gateway_starter_result(self, result: int) -> bool:
        """
        Receives the result code in "start gateway" and converts it to a boolean indicating if the request was accepted or not.
        
        Args:
            result: The result code from "start gateway"
            
        Returns:
            bool: True if the request was accepted. False otherwise.
        """
        match result:
            case 100:  # Request accepted
                return True
            case 102:
                logger.error('ZibalGateway: merchant was not found.')
            case 103:
                logger.error('ZibalGateway: merchant is disabled.')
            case 104:
                logger.error('ZibalGateway: merchant is invalid.')
            case 105:
                logger.error('ZibalGateway: amount must be greater than 1000.')
            case 106:
                logger.error('ZibalGateway: callback_url is invalid. Must start with http/https')
            case 113:
                logger.error('ZibalGateway: amount is bigger than the limit.')
            case 114:
                logger.error('ZibalGateway: national_code is invalid.')
            case 115:
                logger.error('ZibalGateway: Your IP is not registered.')
            case _:  # Unknow issue
                logger.error('ZibalGateway: Unknown error.')
        return False
    
    def _restore_gateway_data(self, identifier: str) -> dict[str, Any] | None:
        """
        Restores the starter data that was cached after a successful start request and removes it right away
        
        Args:
            identifier: Unique identifier that was used to start the gateway.
            
        Returns:
            Returns the cached data if it exists. None otherwise.
        """
        cache_key = f'{self._start_cache_prefix}-{self.merchant}-{identifier}'
        data = cache.get(cache_key)
        cache.delete(cache_key)
        return data
        
    def start_payment(
            self,
            amount: int,
            callback_url: str,
            description: str = None,
            identifier: str = None,
            phone: str = None,
            allowed_cards: list[str] = None,
            national_code: str = None,
            check_mobile_with_cart: bool = False,
            reason: Transaction.TransactionReason = Transaction.TransactionReason.PAYMENT
    ) -> tuple[bool, str]:
        """
        Initiates payment with the Zibal gateway provider.
        
        Args:
            amount: Payment amount
            callback_url: URL where gateway will send payment result
            description: Optional - Payment description. Will be visible in reports.
            identifier: Optional - Payment unique identifier. Will be visible in reports.
            phone: Optional - User phone number. Shows the saved cart numbers connected to this number in the gateway.
            allowed_cards: Optional - List of allowed cart numbers.
            national_code: Optional - User national code. Matched the national code with the cart number they enter in gateway and prevents the user from completing the payment if the national code didn't match the cart number.
            check_mobile_with_cart: Optional - Matches the user phone number with the cart number's owner phone number. If it didn't match it'll prevent the payment from being completed.
            reason: Optional - Transaction reason.
        Returns:
            tuple[bool, str]: (success status, track_id or error message)
        """
        
        # Amount must be an integer bigger or equal to 1000 IRR
        if not isinstance(amount, int):
            raise TypeError('amount must be an integer.')
        if amount < 1000:
            raise ValueError('amount must be greater than 1000.')
        
        # callback_url must be a valid url-string
        if not isinstance(callback_url, str):
            raise TypeError('callback_url must be a string.')
        result = urlparse(callback_url)
        if not all([result.scheme, result.netloc]):
            raise ValueError('Use a valid URL for callback_url.')
        
        # Optional description
        if description and not isinstance(description, str):
            raise TypeError('description must be a string.')
        
        # A unique identifier for this gateway
        if not isinstance(identifier, str):
            warn('In the newer versions of ZibalGateway, identifier is required.')
            raise TypeError('identifier must be a string.')
        
        # Validating user phone number with regex to make sure all gateway functionalities work
        if not isinstance(phone, str):
            warn('In the newer versions of ZibalGateway, phone is required.')
            raise TypeError('phone must be a string.')
        if not GetDataMixin.validate_phone(phone):
            raise ValueError('Use a valid Iranian phone number.')
        
        # Validating the allowed_cards
        if allowed_cards and not isinstance(allowed_cards, list):
            raise TypeError('allowed_cards must be a list.')
        
        # Validating the national_code
        if national_code and (not isinstance(national_code, str) or not GetDataMixin.NATIONAL_CODE_REGEX.match(national_code)):
            raise TypeError('national_code must be a string.')
        
        # Building request body
        request_body = {
            'merchant': self.merchant,
            'amount': amount,
            'callbackUrl': callback_url,
            'description': description,
            'orderId': identifier,
            'mobile': phone,
            'allowedCards': allowed_cards,
            'nationalCode': national_code,
            'checkMobileWithCart': check_mobile_with_cart,
        }
        request_body = {key: value for key, value in request_body.items() if value is not None}
        
        # Sending the information to get a track_id
        response = requests.post(
            url=self.start_url,
            json=request_body,
            headers={
                'Content-Type': 'application/json'
            }
        )
        
        # Zibal API only returns 200 code even when errors occur
        if response.status_code != 200:
            logger.error(f'ZibalGateway: Error sending data to start gateway. {response.status_code} - {response.json()}')
            return False, 'Could not connect to Zibal gateway.'
        
        data = response.json()
        
        # success/error code
        result = data.get('result')
        try:
            result = int(result)  # Tries to convert result to int
        except ValueError:
            return False, 'Could not convert result from Zibal gateway.'
        
        success = self._check_gateway_starter_result(result)  # Checks the result code to see if the request was accepted or not
        if not success:  # If we were rejected at this stage it means some of the arguments are invalid.
            return success, 'Invalid parameters were passed. Please try again.'
        
        # Tries to get track_id from response body
        track_id = data.get('trackId')
        if not track_id:
            return False, 'Could not get track ID from Zibal gateway.'
        
        # Stores the gateway metadata so it can match them in the callback_url results.
        cache.set(f'{self._start_cache_prefix}-{self.merchant}-{identifier}', {
            'track_id': track_id,
            'message': data.get('message'),
            'amount': amount,
            'callback_url': data.get('callbackUrl'),
            'reason': reason
        }, timeout=600)
        
        # True, track_id
        return success, track_id
    
    def build_gateway_url(self, track_id: int, **kwargs) -> str:
        """
        Builds the Zibal gateway URL.
        
        Args:
            track_id: The track_id that was received from Zibal gateway starter.
            
        Returns:
            A full url to Zibal gateway
        """
        return self.gateway_url.format(track_id)
    
    def validate_gateway_response(self, response_data: Dict[str, Any], **kwargs) -> tuple[bool, dict[str, Any] | None]:
        """
        Validates and processes the callback response from gateway provider.
        Double checks everything with cache and triple checks it with validate endpoint
        
        Args:
            response_data: Raw callback data from gateway (query params or POST data)
            **kwargs: Additional provider-specific parameters. A user instance must be passed -> user: AUTH_USER_MODEL
        """
        
        # Tries to get user instance
        user = kwargs.get('user')
        if user is None:
            raise RuntimeError('User must be set to create a transaction.')
        
        # Extracts all the required data from response body
        success = response_data.get('success')
        track_id = response_data.get('trackId')
        identifier = response_data.get('orderId')
        status = response_data.get('status')
        
        # Checking all the basic errors before processing the transaction
        if not success:
            logger.warning(f'ZibalGateway: Gateway payment failed with success: {success}')
            return False, None
        
        if track_id is None:
            logger.warning(f'ZibalGateway: Gateway payment failed with track_id: {track_id}')
            return False, None
        
        if identifier is None:
            logger.warning(f'ZibalGateway: Gateway payment failed with identifier: {identifier}')
            return False, {'track_id': track_id}
        
        try:
            status = int(status)
            if status not in (1, 2):  # status: 1 ==> Paid and Verified | 2 ==> Paid but not veified
                logger.warning(f'ZibalGateway: Gateway payment failed with status: {status}')
                success = False
        except ValueError:
            return False, {'track_id': track_id, 'identifier': identifier}
        
        # Restores all the data from cache
        starter_data = self._restore_gateway_data(identifier)
        
        # If there is no data cached it means that this request is either false or expired.
        if starter_data is None:
            logger.warning(f'ZibalGateway: Did not find any matching gateway starter in cache.')
            return False, None
        
        # Double-checking track_id with cache to make sure we are processing the right transaction
        # We convert them both to string to prevent any issue matching these two
        if int(starter_data.get('track_id')) != int(track_id):
            logger.error(f'ZibalGateway: track_id is not matching the gateway starter track_id: Starter track_id {starter_data['track_id']} != Gateway track_id {track_id}')
            return False, None
        
        # Verifying the transaction and extracting metadata
        success, metadata = self.verify_transaction(int(track_id))
        
        transaction: Transaction | None = None
        
        # Triple-Checking the data with identifier and status
        # We should have the same identifier from verify and callback
        # Status should be 1 before verification because we haven't fetched the verify endpoint yet, but after that the status must change to 2 unless it wasn't a successful transaction.
        logger.info(f'Status was this {metadata['status']=}')
        if not success or str(metadata.get('identifier')) != str(identifier) or str(metadata.get('status')) != '1':
            # Creating a transaction model with failed status
            transaction = Transaction.objects.create(
                user=user,
                amount=metadata.get('amount') or starter_data.get('amount'),
                currency=Transaction.CurrencyChoices.IRR,
                transaction_type=Transaction.TransactionTypes.GATEWAY,
                transaction_reason=starter_data.get('reason'),
                transaction_status=Transaction.TransactionStatus.FAILED,
                provider=self.__class__.__name__,
                tracking_id=track_id or starter_data.get('track_id'),
                provider_payload=metadata,
                metadata=kwargs.get('metadata', {}),
                description=kwargs.get('description', None),
            )
        else:
            # Creating a transaction model with success status
            transaction = Transaction.objects.create(
                user=user,
                amount=metadata.get('amount'),
                currency=Transaction.CurrencyChoices.IRR,
                transaction_type=Transaction.TransactionTypes.GATEWAY,
                transaction_reason=starter_data.get('reason'),
                transaction_status=Transaction.TransactionStatus.SUCCESS,
                provider=self.__class__.__name__,
                tracking_id=track_id,
                provider_payload=metadata,
                metadata=kwargs.get('metadata', {}),
                description=kwargs.get('description', None),
            )
            
        # Adding transaction uuid4 to metadata
        metadata.update({'transaction': transaction.id})
        return success, metadata
    
    def _validate_verify_result(self, result: int) -> bool:
        """
            Verifies the result code received from Zibal verify endpoint.
            
            Args:
                result: The result code from Zibal verify endpoint.
                
            Returns:
                bool: Whether the transaction was successful or not.
        """
        match result:
            case 100:
                return True
            case 102:
                logger.error('Invalid merchant.')
            case 103:
               logger.error('merchant is disabled.')
            case 104:
                logger.error('merchant invalid.')
            case 201:
                logger.warning('This transaction was already verified.')
            case 202:
                logger.error('This transaction was was not successful.')
            case 203:
                logger.error('Invalid track_id.')
            case _:
                logger.error('Unknown result.')
        return False
    
    def verify_transaction(self, track_id: int, **kwargs) -> tuple[bool, dict[str, Any] | None]:
        """
        Queries the gateway provider to verify payment status.
        
        Args:
            track_id: Payment tracking identifier
            **kwargs: Additional provider-specific parameters
        """
        
        # Validating track_id
        if not isinstance(track_id, int):
            raise ValueError('track_id must be an integer.')
        
        # Fetching verify_url
        response = requests.post(
            url=self.verify_url,
            json={
                'merchant': self.merchant,
                'trackId': track_id,
            },
            headers={
                'Content-Type': 'application/json',
            }
        )
        
        # Verify endpoint only returns 200 code even when an Error happens
        if response.status_code != 200:
            logger.error('Could not verify transaction. Probably connection issue.')
            return False, None
        
        data = response.json()
        
        # Extracting all the required data from response body
        paid_at = data.get('paidAt')  # ISO DateTime YYYY-MM-DDTHH:MM:SS.Microseconds
        masked_card_number = data.get('cardNumber')
        status = data.get('status')
        amount = data.get('amount')
        reference_number = data.get('refNumber')
        description = data.get('description')
        identifier = data.get('orderId')
        message = data.get('message')
        
        # Transaction result
        result = data.get('result')
        
        # Storing all the metadata in dictionary to store them in Transaction model later
        metadata = {
            'paid_at': paid_at,
            'masked_card_number': masked_card_number,
            'status': status,
            'amount': amount,
            'reference_number': reference_number,
            'description': description,
            'identifier': identifier,
            'message': message,
        }
        
        # Validates and checks the result code
        try:
            result = int(result)
            if not self._validate_verify_result(result):
                return False, metadata
        except ValueError:
            return False, metadata
        
        # We got some money
        return True, metadata