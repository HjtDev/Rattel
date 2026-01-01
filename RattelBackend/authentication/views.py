from typing import AnyStr, Any, Dict
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from users.utils.unique import check_user_uniqueness
from users.utils.create_account import register
from users.utils.login import login
from users.utils.find_user import get_user_by_dynamic_username
from .OTP.otp import OTP
from .OTP.session import start_otp_session_with_sms
from rest_framework import status
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


class RegisterView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Initiates an OTP session if user data was accepted.
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'register'  # 10/minute
    
    def post(self, request):
        """
        Verifies user data and checks for conflicts then starts an OTP session with action=register
        
        Expected payload: {
            username: A unique username matching the standards,
            name: At least 3 characters,
            phone: A unique phone number. 11 digits starting with 09,
            email: Optional - A valid email address.
        }
        """
        
        # Extracts the required data from request.data
        success, result = self.get_data(
            request,
            ('username', self.validate_username),
            ('name', self.validate_name),
            ('phone', self.validate_phone),
        )
        
        if not success:  # username/name/phone is missing/invalid
            logger.error(f'Incomplete registration data: {result}')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )
        
        if 'email' in request.data:  # Checking for email
            if self.validate_email(request.data['email']):  # If it exists and valid add it to result
                result['email'] = request.data['email']
            else:  # If it exists, but it is not a valid email address
                logger.error(f'Invalid email address: {request.data['email']}')
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False,
                    error=-2,
                    message='Invalid email address'
                )
            
        # Checking if any other user with the same username/phone/email(if passed) exists.
        already_exists, field = check_user_uniqueness(**result)
        if already_exists:
            logger.error(f'User with the same {field} already exists.')
            return self.build_response(
                status.HTTP_409_CONFLICT,
                success=False,
                error=-3,
                message=f'{field} already exists'
            )
        
        # Pre-Building otp_options
        otp_options = {
            'encrypted': True,
            'override': False,
            'user': result,
            'action': 'register'
        }
        
        # Starting OTP session with sending the token via SMSHandler
        return start_otp_session_with_sms(
            indicator=result['username'],
            phone=result['phone'],
            error_code_start=-4,
            **otp_options
        )
    

class LoginView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Processes username/phone then starts an OTP session with action=login
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'login'  # 10/minute
    
    def post(self, request):
        """
        Validates the input and checks if it is username or phone number then checks if user exists and finally starts an OTP session
        
        Expected payload: {
            username: username or phone number of the account you want to log in to
        }
        """
        
        # Extracting username/phone from request
        success, result = self.get_data(request, 'username')
        
        # username/phone is invalid
        if not success:
            logger.error('Incomplete login data.')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )
        
        username_type = self.username_type(result['username'])  # Returns username or phone if a valid username was detected, None if it couldn't match it with anything
        if username_type is None:  # Username is not a valid username/phone
            logger.warning(f'username: {result['username']} is not a valid username/phone number')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-2,
                message='Use username or phone number to login.'
            )
        
        # Get user instance with minor optimizations
        user = get_user_by_dynamic_username(result['username'], username_type, ['id', 'phone', 'is_active'])
        
        if user is None:  # User's account was not found
            logger.error(f'Could not find any matching user account for {result['username']}')
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Username/Phone does not exist.'
            )
            
        # User account is disabled and con not be accessed
        if not user.is_active:
            logger.error(f'User {result['username']} is inactive')
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-4,
                message='User account is disabled.'
            )
        
        result['id'] = user.id  # Saving user.id in result next to username/phone
        phone = user.phone  # Saving user.phone so we can send SMS to it later
        
        # Pre-Building OTP session options
        otp_options = {
            'encrypted': True,
            'override': False,
            'user': result,
            'action': 'login'
        }
        
        # Starting OTP session with sending the token via SMSHandler
        return start_otp_session_with_sms(
            indicator=f'login-{user.id}',
            phone=phone,
            error_code_start=-5,
            **otp_options
        )
        
class VerifyView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Finalizes a verification request and completes the requested action
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'verify'  # 10/minute
    
    def invalid_action(self, action: AnyStr, error: int):
        """
        Returns a server-error response for an invalid action.
        
        Args:
            action (AnyStr): The invalid action
            error (int): The error code to use for response
            
        Returns:
            restframework.responses.Response: The server error response
        """
        
        logger.error(f'The requested action: "{action}" was not found.')
        return self.build_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            success=False,
            error=error,
            message=f'Invalid action: {action}'
        )
    
    def register_action(self, user_data: dict):
        """
        Tries to create an account with user_data.
        If user account was created successfully it will return a new refresh+access token for that account.
        
        Args:
            user_data (dict): The user data -> At least should have username/phone/name | email(optional)
            
        Returns:
            restframework.responses.Response: The final result of registration
        """
        
        created, output = register(**user_data)  # If created output=user otherwise output=error_message
        
        # User data are invalid. Could be also a server-error
        if not created:
            logger.error(f'User registration failed. {output}')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-9,
                message=f'Failed to register user: {output}'
            )
        
        user = output
        refresh = RefreshToken.for_user(user)  # Generates refresh and access token for user
        
        # Returns refresh and access token
        return self.build_response(
            status.HTTP_201_CREATED,
            success=True,
            message='Registered successfully.',
            refresh=str(refresh),
            access=str(refresh.access_token)
        )
    
    def login_action(self, user_data: dict):
        logged_in, output = login(**user_data)
        
        if not logged_in:
            logger.error(f'Failed to login user: {output}')
            return self.build_response(
                status.HTTP_401_UNAUTHORIZED,
                success=False,
                error=-10,
                message=f'Failed to login user: {output}'
            )
        
        user = output
        refresh = RefreshToken.for_user(user)  # Generates refresh and access token for user
        
        # Returns refresh and access token
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Logged in successfully.',
            refresh=str(refresh),
            access=str(refresh.access_token)
        )
    
    @staticmethod
    def get_otp_error_code(code: int) -> Dict[str, Any] | None:
        """
        Maps OTP.finish error_codes to error_responses and returns it if code was in error_responses
        
        Args:
            code (int): The OTP.finish success/error code
            
        Returns:
            dict: A pre-built error response if code was in error_responses
        """
        
        # Pre-Building error_responses
        error_responses = {
             0: { 'success': False, 'error': -2, 'message': 'Invalid verification code.' },
            -1: { 'success': False, 'error': -3, 'message': 'No active verification session found.' },
            -2: { 'success': False, 'error': -4, 'message': 'Failed to validate. Please try again later.' },
            -3: { 'success': False, 'error': -5, 'message': 'Failed to decrypt the token. Please try again later.' },
            -4: { 'success': False, 'error': -6, 'message': 'Lost track attempts. Please try again later.' },
            -5: { 'success': False, 'error': -7, 'message': 'Too many attempts. Please try again later.' },
            -6: { 'success': False, 'error': -8, 'message': 'Could not check encryption of token. Please try again later.' },
        }
        
        if error_responses.get(code):  # Checking for error
            return error_responses[code]
        else:  # No error
            return None
        
    def post(self, request):
        """
        Handles verification request
        
        Expected payload: {
            indicator: The indicator of the verification request,
            token: The verification request's token
        }
        """
        
        # Extracting indicator and token from request
        success, result = self.get_data(
            request,
            ('indicator', self.validate_string),
            ('token', self.validate_string),
        )
        
        if not success:  # indicator/token is required.
            logger.error('Incomplete verification request.')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )
        
        otp = OTP(result['indicator'])  # Initiates the OTP
        code, data = otp.finish(result['token'])  # Tries to validate user token
        
        error_response = self.get_otp_error_code(code)
        
        if error_response:  # If OTP validation was not successful returns the matching response with error code
            logger.warning(f'OTP validation failed. {error_response}')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                **error_response
            )
        
        # If code reaches here it means that the OTP validation was successful and the OTP session is cleared.
        
        action = data.get('action', None)  # The action that lead to here.
        
        if action == 'register':  # User is trying to register a new account
            user_data = data.get('user')  # Restoring user data
            return self.register_action(user_data)
        
        elif action == 'login':  # User is trying to log in
            user_data = data.get('user')  # Restoring user data
            return self.login_action(user_data)
            
        else:  # The action is not supported/invalid
            return self.invalid_action(action=str(action), error=-11)

class RefreshView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Refresh access token by sending refresh token.
    Also rotate and blacklist the refresh token if settings.ROTATE_REFRESH_TOKEN and BLACKLIST_AFTER_ROTATION are set to True
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'refresh'  # 50/minute
    
    def post(self, request):
        """
        Validates refresh token. Blacklists the refresh token if required. Returns new access and refresh token.
        
        Expected payload: {
            refresh: A valid base64 encoded token string
        }
        """
        
        # Extracts refresh token from request.data
        success, result = self.get_data(request, ('refresh', self.validate_string))
        
        # refresh token is missing
        if not success:
            logger.error('Refresh token is missing.')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )

        try:  # Tries to find the refresh token
            refresh = RefreshToken(result['refresh'])
        except TokenError:  # Refresh token is expired
            logger.error('Refresh token is expired/invalid.')
            return self.build_response(
                status.HTTP_401_UNAUTHORIZED,
                success=False,
                error=-2,
                message='Refresh token is expired/invalid.'
            )
        
        user_model = get_user_model()
        
        try:
            # Getting user instance for refresh token to see if it exists
            user_id = refresh.get(settings.SIMPLE_JWT.get('USER_ID_CLAIM', 'user_id'))
            user = user_model.objects.get(**{settings.SIMPLE_JWT.get('USER_ID_FIELD', 'id'): user_id})
            
            # User account is found, but it is disabled
            if not user.is_active:
                logger.warning('User account is inactive.')
                return self.build_response(
                    status.HTTP_401_UNAUTHORIZED,
                    success=False,
                    error=-3,
                    message='User account is disabled.'
                )

        # Could not find any matching account with refresh token
        except user_model.DoesNotExist:
            logger.error('User account does not exist.')
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-4,
                message='User does not exist.'
            )
        
        # Failed to extract user data from refresh token
        except Exception as e:
            logger.error(f'Failed to get user data: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-5,
                message='Failed to process your request. Please try again later.'
            )

        # Extracting required settings from settings.py
        rotate_tokens = settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False)
        blacklist_after_rotation = settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False)

        # Generating a new access token
        data = { 'access': str(refresh.access_token) }

        # New refresh token is required
        if rotate_tokens:
            
            # Generating new refresh token and saving it
            new_refresh = RefreshToken.for_user(user)
            data['refresh'] = str(new_refresh)
            logger.info(f'Refresh token is rotated for {user}')
            
            # Old refresh token must be blacklisted
            if blacklist_after_rotation:
                try:  # Tries to blacklist refresh token
                    refresh.blacklist()
                    logger.info(f'Blacklisted the old refresh token for {user}')
                except Exception as e:  # Blacklisting refresh token failed
                    logger.error(f'Failed to blacklist refresh token for {user}: {e}')
                    return self.build_response(
                        status.HTTP_200_OK,
                        success=True,
                        message='Failed to blacklist refresh token.',
                        **data
                    )
            else:  # Token is rotated. Blacklisting is not required
                logger.info('Refresh token for user {user} is rotated, but not blacklisted.')
            
            # Returning the refresh token with the new access token
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='New refresh and access token are generated.',
                **data
            )
        
        # No rotation - No blacklist
        # Returning the old refresh token with new access token
        else:
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='Token refreshed.',
                refresh=str(refresh),
                access=data['access'],
            )
