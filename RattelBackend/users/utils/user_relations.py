from typing import Tuple, Any, Dict
from users.models import User, Profile, UserSettings
from users.serializers import ProfileSerializer, UserSettingsSerializer
import logging


logger = logging.getLogger(__name__)

def get_accessible_profile(**profile_filters) -> Tuple[bool, Profile | None]:
    """
    Checks whether a profile is public or not.
    
    Args:
        profile_filters: filters to find the Profile object -> id, user__username, or any other filter.
        
    Returns:
        Tuple[bool, Profile | None] -> (success, Profile Instance | None)
    """
    
    try:
        # Load Profile object(id only) and join user__settings to it then in user.settings check for profile_visible
        profile = Profile.objects.select_related('user__settings').get(**profile_filters)
        return profile.user.settings.profile_visible and not profile.user.is_superuser, profile
    except Profile.DoesNotExist:
        logger.warning(f'Profile {profile_filters} does not exist.')
    except Profile.MultipleObjectsReturned:
        logger.warning(f'Multiple profiles found for {profile_filters}.')
    except Exception as e:
        logger.warning(f'Error getting profile {profile_filters}: {e}')
    return False, None


def get_user_profile(**user_filters) -> Profile | None:
    """
    Fetch the user profile for a given user filter.
    
    Args:
        user_filters: User filters -> id, pk, phone or any other field you want to use to find your user.
        
    Returns:
         Profile instance or None.
    """
    
    try:
        if not user_filters:
            raise Exception('You must specify at least one user filter.')
        # Load user instance(id only) and join profile to it then fetch profile
        return User.objects.select_related('profile').get(**user_filters).profile
    except User.DoesNotExist:
        logger.warning(f'Could not find user profile for {user_filters}.')
    except User.MultipleObjectsReturned:
        logger.warning(f'Multiple user profiles for {user_filters}.')
    except Exception as e:
        logger.error(f'Unexpected error while getting user profile for {user_filters}: {e}')
    return None
    

def get_user_settings(**user_filters) -> UserSettings | None:
    """
    Admins Only.
    Fetch the user settings for a given user filter.
    
    Args:
        user_filters: User filters -> id, user__username, or any other field you want to use to find your user.
        
    Returns:
        UserSettings instance or None.
    """
    
    try:
        if not user_filters:
            raise Exception('You must specify at least one user filter.')
        
        # Fetch user(id only) and join settings to it then return the user.settings if user was found
        return User.objects.select_related('settings').get(**user_filters).settings
    except User.DoesNotExist:
        logger.warning(f'Could not find user settings for {user_filters}.')
    except User.MultipleObjectsReturned:
        logger.warning(f'Multiple user settings for {user_filters}.')
    except Exception as e:
        logger.error(f'Unexpected error while getting user settings for {user_filters}: {e}')
    return None


def update_user_profile(profile: Profile, **fields) -> Tuple[bool, Dict[str, Any] | Profile]:
    """
    Tries to update a profile instance using its serializer. The serializer itself validates the input date and saves the instance.
    
    Args:
        profile: The profile instance you want to update
        fields: The fields you want to update in the profile instance
        
    Returns:
        success, Profile or error_message_dict
    """
    
    # Validate profile instance
    if not isinstance(profile, Profile):
        raise TypeError(f'Profile {profile} is not a Profile.')
        
    # Validate fields. At least one field is required
    if not fields:
        return False, {'fields': 'There is nothing to update.'}
    
    # Setup profile serializer
    serializer = ProfileSerializer(instance=profile, data=fields, partial=True)
    
    # fields are invalid and require correction
    if not serializer.is_valid():
        errors = serializer.errors
        logger.warning(f'Failed to update profile: {errors}')
        return False, errors
    
    try:  # Saving the instance(commit=True)
        profile = serializer.save()
    except Exception as e:  # Failed to save profile instance
        logger.error(f'Profile serializer validated the data, but failed to save it. {e}', exc_info=True)
        return False, {'fields': 'Failed to update profile.'}
    
    # Return True, updated_profile_instance
    return True, profile
        

def update_user_settings(settings: UserSettings, **fields) -> Tuple[bool, Dict[str, Any] | UserSettings]:
    """
    Tries to update a UserSettings instance using its serializer. The serializer itself validates the input date and saves the instance.
    
    Args:
        settings: The UserSettings instance you want to update
        fields: The fields you want to update in the UserSettings instance
        
    Returns:
        success, UserSettings or error_message_dict
    """
    
    # Validate settings instance
    if not isinstance(settings, UserSettings):
        raise TypeError(f'UserSettings {settings} is not a instance of UserSettings.')
    
    # Validate fields. At least one field is required
    if not fields:
        return False, {'fields': 'There is nothing to update.'}
    
    # Setup settings serializer
    serializer = UserSettingsSerializer(instance=settings, data=fields, partial=True)
    
    # fields are invalid and require correction
    if not serializer.is_valid():
        errors = serializer.errors
        logger.warning(f'Failed to update settings: {errors}')
        return False, errors
    
    try:  # Saving the instance(commit=True)
        settings = serializer.save()
    except Exception as e:  # Failed to save settings instance
        logger.error(f'UserSettings serializer validated the data, but failed to save it. {e}', exc_info=True)
        return False, {'fields': 'Failed to update settings.'}
    
    # Return True, updated_settings_instance
    return True, settings
    
    
