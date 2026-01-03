from typing import Any, List
from django.contrib.auth import get_user_model
from RattelBackend.mixins import GetDataMixin
import logging


logger = logging.getLogger(__name__)


def get_user_by_dynamic_username(username: str, username_type: str, _only: List[str] | None = None) -> Any:
    """
    Receives a username with its type and tries to find the user account based on it
    
    Args:
        username: The username to look for
        username_type: The type of username to look for -> username/phone
        _only: If you only want certain fields of user instance -> for micro-optimizations
        
    Returns:
        Any: The user instance if user account was found, None otherwise.
    """
    
    user_model = get_user_model()
    
    # Validating username_type
    if username_type not in ('username', 'phone'):
        raise ValueError(f'Username type {username_type} is not supported. Please use "username" or "phone" as type.')
    
    # Validating _only
    if _only and not isinstance(_only, list):
        raise TypeError(f'_only must be a list of strings.')
        
    # Setting the matching validator for the given username
    validator = GetDataMixin.validate_username if username_type == 'username' else GetDataMixin.validate_phone
    
    # Username is invalid
    if not validator(username):
        return None
    
    try:
        if _only:  # Not all the fields are required
            return user_model.objects.only(*_only).get(**{f'{username_type}': username})
        return user_model.objects.get(**{f'{username_type}': username})  # All the fields are required
    
    except user_model.DoesNotExist:  # User account does not exist
        return None
    
    except user_model.MultipleObjectsReturned:  # Integrity problems. Username should be unique
        logger.error(f'Multiple users were found for username: {username}')
        return None
    except Exception as e:  # Unknow issue occurred
        logger.warning(f'Failed to get user: {username}: {e}')
        return None
