from django.contrib.auth import get_user_model
from typing import Tuple, Any
from django.utils import timezone
from RattelBackend.mixins import GetDataMixin
import logging


logger = logging.getLogger(__name__)

def update_user_login_date(_user) -> bool:
    """
    Sets the user last_login to timezone.now()
    
    Args:
        _user: A valid user instance
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    user_model = get_user_model()
    
    # Validating _user + Updating last_login
    if isinstance(_user, user_model):
        _user.last_login = timezone.now()
        _user.save(update_fields=['last_login'])  # Only updates the last_login
        return True
    
    return False

def login(**user_data) -> Tuple[bool, Any]:
    """
    Tries to extract id from user_data and find its matching account.
    
    Args:
        user_data: Should contain user_id -> {'id': 1, ...}
        
    Returns:
        Tuple[bool, Any]: logged_in_successfully, user_instance | error_message
    """
    
    user_model = get_user_model()
    
    # Checking for id in user_data
    if 'id' not in user_data:
        return False, 'Could not find user ID'
    
    # Validating id
    if not GetDataMixin.is_id(user_data['id']):
        return False, f'ID: {user_data['id']} is not a valid ID.'
    
    # Tries to find user instance based on id
    try:
        user = user_model.objects.get(id=user_data['id'])
        
        # user instance is found, but it is inactive.
        if not user.is_active:
            return False, 'User account is inactive.'
        
        # Tries to update user.last_login, but it wouldn't stop login flow if it fails
        updated = update_user_login_date(user)
        if not updated:
            logger.warning(f'Failed to update the last_login for {user}')
            
        # Returning True, user_instance
        return True, user
    
    except user_model.DoesNotExist:  # Could not find any matching account with the given id
        return False, 'User account does not exist.'
    
    except user_model.MultipleObjectsReturned as e:  # Integrity error. ID should be unique per user
        logger.warning(f'Multiple users found for ID: {user_data['id']}. {e}')
        return False, 'Your account is currently unavailable. Please try again later.'
    
    except Exception as e:  # Unknow issue occurred
        logger.warning(f'Failed to login with ID: {user_data['id']}. {e}')
        return False, 'Something went wrong. Please try again later.'
    