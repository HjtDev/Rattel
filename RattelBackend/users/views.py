from typing import Tuple, Any, Dict
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin, FieldValidator
from .models import Profile, User, UserSettings
from .utils.user_relations import get_accessible_profile, get_user_profile, update_user_profile, update_user_settings
from .serializers import ProfileSerializer, UserSettingsSerializer
from rest_framework.views import APIView
from rest_framework import status
import logging


logger = logging.getLogger(__name__)

class UserProfileView(APIView, GetDataMixin, ResponseBuilderMixin, FieldValidator):
    """
    Using this endpoint you can See/Edit your profile if you are authenticated and other users' profile if it's accessible.
    """
    
    permission_classes = (IsAuthenticatedOrReadOnly,)  # Because user must be authenticated to see his own profile, but authentication is not required when checking someone else's profile
    throttle_scope = 'user-profile'  # 100/min
    
    valid_fields = ('gender', 'national_code', 'education', 'had_other_classes',
                    'memorized', 'invited_by', 'birthday', 'city',
                    'telegram_id', 'eitaa_id', 'instagram_id')
    validators = {
        'max_length': 500,
        'sql': False,
        'lookup': True,
        'injection': False,
        'redis': False
    }
    
    def get_throttles(self):
        if self.request.method == 'PATCH':
            self.throttle_scope = 'user-profile-edit'  # 15/min
        
        return super().get_throttles()
    
    def validate_target_profile(self, value: str) -> bool:
        """
        Tries to validate the target profile
        
        Args:
            value (str): target profile username or me(to check you own profile)
            
        Returns:
            True or False depending on if the target value is valid
        """
        
        # Validating value type
        if not isinstance(value, str):
            return False
        
        # User is trying to check his own profile
        if value == 'me':
            return True
        
        # User is trying to check another profile
        return self.validate_username(value)
    
    def get_profile(self, target: str, viewer: User) -> Tuple[Profile | None, int]:
        """
        Selects user profile based on target value
        
        Args:
            target: The target profile username or me(to check you own profile)
            viewer: request.user
            
        Returns:
            A profile instance if available, None otherwise + code
        """
        
        # Returns viewer.profile if target is 'me'
        if target == 'me' and viewer.is_authenticated:
            return viewer.profile, 1
            
        # Tries to access a profile
        has_access, target_profile = get_accessible_profile(user__username=target)
        
        # Didn't find the profile
        if target_profile is None:
            return None, -2
        
        # You don't have access to target profile, and you are not an admin.
        if not has_access and not (viewer.is_authenticated and viewer.is_superuser):
            logger.info(f"User {viewer.id if viewer.is_authenticated else 'Anonymous'} attempted to access private profile {target}")
            return None, -3
        
        # You have access to profile, or bypassed the permission with viewer.is_superuser
        return target_profile, 2
    
    def build_success_response(self, profile: Profile, message: str = 'Successful'):
        """
        Serializes the profile instance, and builds a successful response using self.build_response for the serializer.data
        
        Args:
            profile: The profile instance
            message: The message you want to use in response -> Default: 'Successful'
            
        Returns:
            A success response with profile data
        """
        
        serializer = ProfileSerializer(profile)  # Serializing profile instance
        
        # Building success response
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message=message,
            profile=serializer.data
        )
    
    def get(self, request):
        """
        Access a profile instance
        
        Expected query_params: {
            target: 'me' or '{username}' -> Fetch your own profile by target=me and fetch other's by me={username}
        }
        """
        
        # Extracting target from request
        success, result = self.get_data(request, ('target', self.validate_target_profile))
        
        # Target is missing or its value is invalid
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )
        
        target = result['target']
        
        # Tries to get the profile
        profile, code = self.get_profile(target, request.user)
        
        # Couldn't find any profile instance
        if code == -2:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=code,
                message='Profile not found.'
            )
        
        # Found a profile instance but access is limited
        elif code == -3:
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=code,
                message='Target profile is private.'
            )
        
        # Profile is found and ready to be returned
        else:
            # Builds a success response and returns
            return self.build_success_response(profile)
        
    
    def patch(self, request):
        """
        Partially updates the authenticated user's profile.
        Editing other users' profiles is not allowed.
        
        Expected payload: {
            gender: Optional - 'male' or 'female',
            national_code: Optional - Your 10 digit national code,
            education: Optional - Your education,
            had_other_classes: Optional - Explain if you had other classes and where was it,
            memorized: Optional - Explain how much of Quran you have memorized,
            invited_by: Optional - Username or Phone number of the person who invited you,
            birthday: Optional - Date of birth,
            city: Optional - Province/City you live in,
            telegram_id: Optional - Your Telegram ID
            eitaa_id: Optional - Your Eitaa ID
            instagram_id: Optional - Your Instagram ID
        }
        """
        
        # Validates the input to be safe
        is_valid, error = self.validate_string_fields(valid_fields=self.valid_fields, validators=self.validators, **request.data)
        
        # Input is empty or unsafe
        if not is_valid:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=error
            )
        
        # Tries to fetch request.user.profile if the user is authenticated
        profile, code = self.get_profile(target='me', viewer=request.user)
        
        # Could not fetch user.profile
        if code != 1:
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-2,
                message='Please login/register first.'
            )
        
        # Update profile - If failed to update then result will be error_dict and if succeed result=updated_profile_instance
        success, result = update_user_profile(profile, **request.data)
        
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-3,
                message=result
            )
        
        # Mapping result to updated_profile on success
        updated_profile = result
        
        # Builds and return a success response for the updated profile
        return self.build_success_response(updated_profile, message='Updated profile successfully.')


class UserSettingsView(APIView, GetDataMixin, ResponseBuilderMixin, FieldValidator):
    """
    API endpoint for viewing and updating authenticated user settings.
    
    Provides GET and PATCH methods to retrieve and modify user preference settings
    such as profile visibility and notification preferences.
    
    Permissions:
        - Requires authentication for all operations
    
    Throttling:
        - GET: 50 requests/minute
        - PATCH: 15 requests/minute
    """
    
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'user-settings'  # 50/min
    
    # Fields allowed for PATCH operations
    valid_fields = ('profile_visible', 'email_on_login', 'email_on_payment', 'sms_on_payment')
    
    def get_throttles(self):
        """
        Applies different throttle rates based on HTTP method.
        
        Returns:
            List of throttle instances for the current request
        """
        # Apply stricter throttle for updates
        if self.request.method == 'PATCH':
            self.throttle_scope = 'user-settings-edit'  # 15/min
        
        return super().get_throttles()
    
    def build_success_response(self, settings: UserSettings, message: str = 'Successful'):
        """
        Serializes the settings instance and builds a successful response.
        
        Args:
            settings: The UserSettings instance to serialize
            message: The success message to include in response
            
        Returns:
            Response object with serialized settings data
        """
        # Serialize the settings instance
        serializer = UserSettingsSerializer(settings)
        
        # Build and return success response
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            settings=serializer.data,
            message=message
        )
    
    def get(self, request):
        """
        Retrieve the authenticated user's settings.
        
        Returns the current settings configuration including profile visibility
        and notification preferences.
        
        Returns:
            200 OK: Settings data with success=True
            404 NOT FOUND: If settings don't exist for the user (error=-1)
        """
        # Get the user's settings instance
        settings = request.user.settings
        
        # Validate that settings exist
        if not isinstance(settings, UserSettings):
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='There is no settings for this user.'
            )
        
        # Return serialized settings
        return self.build_success_response(settings)
    
    def patch(self, request):
        """
        Partially update the authenticated user's settings.
        
        Validates and updates boolean settings fields. Only provided fields
        will be updated; omitted fields remain unchanged.
        
        Expected payload: {
            profile_visible: Optional - Boolean for profile visibility,
            email_on_login: Optional - Boolean for login email notifications,
            email_on_payment: Optional - Boolean for payment email notifications,
            sms_on_payment: Optional - Boolean for payment SMS notifications
        }
        
        Returns:
            200 OK: Updated settings with success=True
            400 BAD REQUEST:
                - error=-1: Invalid field name or non-boolean value
                - error=-2: Failed to update settings in database
        """
        # Validate boolean fields
        success, error = self.validate_boolean_fields(
            valid_fields=self.valid_fields,
            **request.data
        )
        
        # Input validation failed
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=error
            )
        
        # Attempt to update user settings
        success, result = update_user_settings(request.user.settings, **request.data)
        
        # Update operation failed
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-2,
                message=result
            )
        
        # Map result to updated_settings on success
        updated_settings = result
        
        # Return success response with updated settings
        return self.build_success_response(updated_settings)
