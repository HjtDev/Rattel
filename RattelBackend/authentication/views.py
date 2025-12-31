from typing import Tuple
from django.contrib.auth import get_user_model
from django.db.models.expressions import result
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from notifications.handlers.sms import SMSHandler
from notifications.providers.sms.local import LocalSMSProvider
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .OTP.otp import OTP
from rest_framework import status
from django.conf import settings
import logging


logger = logging.getLogger(__name__)


def check_for_user_race_condition(username: str = None, phone: str = None, email: str = None, **kwargs) -> Tuple[bool, str | None]:
    """
    Checks if any user with the given username/phone/email exists.
    Happens when two user try to log in with the same credentials or when credentials are already is use.
    Prevents registering the same user twice because of race conditions and also can be used for duplicate users.
    At least one argument must be provided
    
    Args:
        username: str
        phone: str
        email: str
        kwargs: To ignore extra user data if available
        
    Returns:
        True if user with the given credentials exists, False otherwise + duplicate field if it exists, None otherwise.
    """
    
    user_model = get_user_model()
    
    # Checking if any user with the same username exists
    if username and user_model.objects.only('id').filter(username=username).exists():
        logger.error('User with this username already exists')
        return True, 'username'
    
    # Checking if any user with the same phone exists
    if phone and user_model.objects.only('id').filter(phone=phone).exists():
        logger.error('User with this phone already exists')
        return True, 'phone'
    
    # Checking if any user with the same email address exists
    if email and user_model.objects.only('id').filter(email=email).exists():
        logger.error('User with this email already exists.')
        return True, 'email'
    
    # No race condition
    return False, None


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
            ('name', lambda name: name and name.strip() and isinstance(name, str) and len(name) < 60),
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
        already_exists, field = check_for_user_race_condition(**result)
        if already_exists:
            logger.error(f'User with the same {field} already exists.')
            return self.build_response(
                status.HTTP_409_CONFLICT,
                success=False,
                error=-3,
                message=f'{field} already exists'
            )
        
        # Initializing SMS handler
        sms = SMSHandler(LocalSMSProvider, sender='Local SMS Provider', output=logger.info)
        
        # Initializing OTP session with username as indicator
        indicator = result['username']
        otp = OTP(indicator)
        
        # Creating a secure/random token
        token = otp.generate_otp_token()
        
        # Initiating OTP session
        started = otp.start(token=token, encrypted=True, override=False, user=result, action='register')
        
        if not started:  # If otp.start failed it means there is another active OTP session with the same indicator
            logger.error('An active OTP session already exists')
            return self.build_response(
                status.HTTP_208_ALREADY_REPORTED,
                success=False,
                error=-5,
                message='An active verification request with this username already exists.'
            )
        
        # OTP session started
        
        # Sending the token to user phone number
        sent = sms.send(result['phone'], f'Your verification code: {token}')
        
        if not sent:  # If it failed to send SMS
            logger.error('Failed to send verification code. Canceling the OTP session.')
            otp.cancel()
            return self.build_response(
                status.HTTP_502_BAD_GATEWAY,
                success=False,
                error=-6,
                message='Failed to send verification code'
            )
        
        # Successfully started OTP session and verification sms is sent.
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            indicator=indicator,
            message='Verification code sent.'
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
        
        if self.validate_phone(result['username']):  # username matches phone-regex
            username_type = 'phone'
        elif self.validate_username(result['username']):  # username matches username-regex
            username_type = 'username'
        else:  # username is invalid
            logger.error(f'username: {result['username']} is not a valid username/phone number')
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-2,
                message='Use username or phone number to login.'
            )
        
        user_model = get_user_model()
        
        try:
            if username_type == 'phone':  # Tries to find user account based on phone number
                user = user_model.objects.only('id', 'phone', 'is_active').get(phone=result['username'])
            else:  # Tries to find user account based on username
                user = user_model.objects.only('id', 'phone', 'is_active').get(username=result['username'])
                
            # User account is disabled and con not be accessed
            if not user.is_active:
                logger.error(f'User {result['username']} is inactive')
                return self.build_response(
                    status.HTTP_403_FORBIDDEN,
                    success=False,
                    error=-7,
                    message='User account is disabled.'
                )
            
            result['id'] = user.id  # Saving user.id in result next to username/phone
            phone = user.phone  # Saving user.phone so we can send SMS to it later
            
        # Failed to find any user matching the given username/phone
        except user_model.DoesNotExist:
            logger.error(f'Could find any matching user account for {result['username']}')
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Username/Phone does not exist.'
            )
        
        # Initializing SMS handler
        sms = SMSHandler(LocalSMSProvider, sender='Local SMS Provider', output=logger.info)
        
        # Initializing OTP session
        indicator = f'login-{result['id']}'
        otp = OTP(indicator)
        
        # Generating secure/random token
        token = otp.generate_otp_token()
        
        # Starting OTP session with the generated token + encryption
        started = otp.start(token=token, encrypted=True, override=False, user=result, action='login')
        
        # Another active OTP session already exists
        if not started:
            logger.error('An active OTP session already exists.')
            return self.build_response(
                status.HTTP_208_ALREADY_REPORTED,
                success=False,
                error=-5,
                message='An active verification request with this username already exists.'
            )
        
        # Sending the token to user's phone number
        sent = sms.send(phone, f'Your verification code: {token}')
        
        # Failed to send verification token to user
        if not sent:
            logger.error('Failed to send verification code. Canceling the OTP session.')
            otp.cancel()
            return self.build_response(
                status.HTTP_502_BAD_GATEWAY,
                success=False,
                error=-6,
                message='Failed to send verification code'
            )
        
        # OTP session was started successfully, and verification code is sent
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            indicator=indicator,
            message='Verification code sent.'
        )
    
    
class VerifyView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Finalizes a verification request and completes the requested action
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'verify'  # 10/minute
    
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
        
        # Pre-building error responses
        error_responses = {
             0: { 'success': False, 'error': -2, 'message': 'Invalid verification code.' },
            -1: { 'success': False, 'error': -3, 'message': 'No active verification session found.' },
            -2: { 'success': False, 'error': -4, 'message': 'Failed to validate. Please try again later.' },
            -3: { 'success': False, 'error': -5, 'message': 'Failed to decrypt the token. Please try again later.' },
            -4: { 'success': False, 'error': -6, 'message': 'Lost track attempts. Please try again later.' },
            -5: { 'success': False, 'error': -7, 'message': 'Too many attempts. Please try again later.' },
            -6: { 'success': False, 'error': -8, 'message': 'Could not check encryption of token. Please try again later.' },
        }
        
        if code != 1:  # If OTP validation was not successful returns the matching response with error code
            logger.warning(f'OTP validation failed. Token: {result['token']} is invalid.')
            return self.build_response(
                status.HTTP_406_NOT_ACCEPTABLE,
                **error_responses[code]
            )
        
        # If code reaches here it means that the OTP validation was successful and the OTP session is cleared.
        
        user_model = get_user_model()
        action = data.get('action', None)  # The action that lead to here.
        
        if action == 'register':  # User is trying to register a new account
            user_data = data.get('user')  # Restoring user data
            
            # All the necessary fields should exist in the user_data to continue
            if not all(field in user_data for field in ('username', 'phone', 'name')):
                logger.error(f'Not all the required fields for registration are present. {user_data}')
                return self.build_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    success=False,
                    error=-9,
                    message='Failed to find user data for registration.'
                )
            
            # Checking for race condition
            already_exists, field = check_for_user_race_condition(**user_data)
            if already_exists:
                logger.error(f'User with the same {field} already exists.')
                return self.build_response(
                    status.HTTP_409_CONFLICT,
                    success=False,
                    error=-14,
                    message=f'User with the same {field} already exists.'
                )
            
            # Creates the user account with user_data and saves the user
            user = user_model(**user_data)
            user.save()
            
            refresh = RefreshToken.for_user(user)  # Generates refresh and access token for user
            
            # Returns refresh and access token
            return self.build_response(
                status.HTTP_201_CREATED,
                success=True,
                message='Registered successfully.',
                refresh=str(refresh),
                access=str(refresh.access_token)
            )
        elif action == 'login':  # User is trying to log in
            user_data = data.get('user')  # Restoring user data
            
            # User id must be saved in user_data to continue
            if 'id' not in user_data:
                logger.error(f'Could not find any user ID to log in. {user_data=}')
                return self.build_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    success=False,
                    error=-10,
                    message='Failed to find user data for login.'
                )
            
            try:
                user = user_model.objects.get(id=user_data['id'])  # Tries to find the user account
            
                if not user.is_active:
                    logger.error(f'User {user} is inactive')
                    return self.build_response(
                        status.HTTP_403_FORBIDDEN,
                        success=False,
                        error=-13,
                        message='User account is disabled.'
                    )
                
                refresh = RefreshToken.for_user(user)  # Generates refresh and access token for user
                
                # Returns refresh and access token
                return self.build_response(
                    status.HTTP_200_OK,
                    success=True,
                    message='Logged in successfully.',
                    refresh=str(refresh),
                    access=str(refresh.access_token)
                )
            except user_model.DoesNotExist:  # Failed to find the user account
                logger.error(f'Could not find any matching account with user ID {user_data=}')
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False,
                    error=-11,
                    message='User does not exist.'
                )
        else:  # The action is not supported/invalid
            logger.error(f'The requested action: "{action}" was not found.')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-12,
                message='The action you requested is invalid/supported.'
            )


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
        success, result = self.get_data(request, 'refresh')
        
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
