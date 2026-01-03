from typing import Tuple
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from .models import Profile, User
from .utils.user_relations import get_accessible_profile, get_user_profile, update_user_profile
from .serializers import ProfileSerializer, UserSettingsSerializer
from rest_framework.views import APIView
from rest_framework import status
import logging


logger = logging.getLogger(__name__)

class UserProfileView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Using this endpoint you can See your profile if you are authenticated and other users' profile if it's accessible.
    """
    
    permission_classes = (IsAuthenticatedOrReadOnly,)  # Because user must be authenticated to see his own profile, but authentication is not required when checking someone else's profile
    throttle_scope = 'user-profile'  # 15/min
    
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
    
    def build_success_response(self, profile: Profile):
        """
        Serializes the profile instance, and builds a successful response using self.build_response for the serializer.data
        
        Args:
            profile: The profile instance
            
        Returns:
            A success response with profile data
        """
        
        serializer = ProfileSerializer(profile)  # Serializing profile instance
        
        # Building success response
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            profile=serializer.data
        )
    
    def get(self, request):
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
        