from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from .unique import check_user_uniqueness
from typing import Tuple, Any
from RattelBackend.mixins import GetDataMixin
import logging


logger = logging.getLogger(__name__)


def validate_register_data(**kwargs) -> Tuple[bool, str | None]:
    """
    Validates the kwargs and checks if the base requirements for registering are met.
    
    Args:
        kwargs: Should contain username, phone and name | email(optional)
        
    Returns:
        Tuple[bool, str | None]: data_is_valid, error_message
    """
    
    # Checking if the base required fields are present
    if not all(field in kwargs for field in ('username', 'phone', 'name')):
        return False, f'Not all the required fields are provided. {kwargs}'
    
    # Validating username
    if not GetDataMixin.validate_username(kwargs['username']):
        return False, f'Username {kwargs['username']} is invalid.'
    
    # Validating phone
    if not GetDataMixin.validate_phone(kwargs['phone']):
        return False, f'Phone {kwargs['phone']} is invalid.'
    
    # Validating name
    name = kwargs['name']
    if not isinstance(name, str) or len(name) < 3:
        return False, f'Name {name} is invalid.'
    
    # Checking if email exists and then validating it
    email = kwargs['email']
    if email and not GetDataMixin.validate_email(email):
        return False, f'Email {email} is invalid.'
    
    return True, None

def register(**user_data) -> Tuple[bool, Any]:
    """
    Tries to validate user_data and create a new account using it.
    
    Args:
        user_data: Should contain username, phone and name | email(optional)
        
    Returns:
        Tuple[bool, Any]: (success, user_instance or error_message)
    """
    
    user_model = get_user_model()
    
    # Validating user input
    is_valid, message = validate_register_data(**user_data)
    
    # user_data are invalid
    if not is_valid:
        return False, message
    
    # Checking if any other user with the same credentials exists
    already_exists, field = check_user_uniqueness(**user_data)
    if already_exists:
        return False, f'User with the same {field} already exists.'
    
    # Tries to create a user instance and submit it
    try:
        user = user_model(**user_data)
        user.save()  # Saving + Triggering user signals to create UserProfile and UserSettings
        return True, user
    except IntegrityError:  # Race condition occurred
        return False, f'User with the same credentials already exists.'
    except ValidationError:
        return False, 'Invalid credentials.'
    except Exception as e:
        logger.warning(f'Unknown error occurred while registering a user: {e}')
        return False, 'Something went wrong. Failed to register.'
    