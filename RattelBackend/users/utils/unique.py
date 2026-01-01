from django.contrib.auth import get_user_model
from typing import Tuple


def check_user_uniqueness(username: str = None, phone: str = None, email: str = None, **kwargs) -> Tuple[bool, str | None]:
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
        return True, 'username'
    
    # Checking if any user with the same phone exists
    if phone and user_model.objects.only('id').filter(phone=phone).exists():
        return True, 'phone'
    
    # Checking if any user with the same email address exists
    if email and user_model.objects.only('id').filter(email=email).exists():
        return True, 'email'
    
    # No conflicts
    return False, None
