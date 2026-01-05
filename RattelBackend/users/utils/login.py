from django.contrib.auth import get_user_model
from typing import Tuple, Any

from django.http import HttpRequest
from django.utils import timezone
from RattelBackend.mixins import GetDataMixin
from django.conf import settings
from django.template.loader import render_to_string
import logging


logger = logging.getLogger(__name__)

def update_user_login_date(_user) -> None:
    """
    Sets the user last_login to timezone.now()
    
    Args:
        _user: A valid user instance
        
    Returns:
        None
    """
    user_model = get_user_model()
    
    # Validating _user + Updating last_login
    if isinstance(_user, user_model):
        _user.last_login = timezone.now()
        _user.save(update_fields=['last_login'])  # Only updates the last_login
    else:
        logger.error(f'Expected a user instance, got {type(_user)}. user.last_login will not update.')

def login(request, **user_data) -> Tuple[bool, Any]:
    """
    Tries to extract id from user_data and find its matching account.
    
    Args:
        request: request instance for the HttpRequest
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
        user = user_model.objects.select_related('settings').get(id=user_data['id'])
        
        # user instance is found, but it is inactive.
        if not user.is_active:
            return False, 'User account is inactive.'
        
        # Tries to update user.last_login, but it wouldn't stop login flow if it fails
        try:
            update_user_login_date(user)
        except Exception as e:
            logger.error(f'Failed to update user login date: {e}')
        
        # Checks if user.settings.email_on_login is True
        if user.settings.email_on_login:
            email_sent = login_email(request, user)  # Send a welcome email to user
            
            # Failed to send the email, but we won't block the login
            if not email_sent:
                logger.warning(f'Failed to send an email to {user}')
            
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


def login_email(request: HttpRequest, _user) -> bool:
    """
    Sends a login notification email to the user.
    
    Constructs and sends an email notification when a user successfully logs in,
    including login details such as time, IP address, and user agent. Requires
    proper email configuration in Django settings.
    
    Args:
        request: The HttpRequest object containing login metadata
        _user: The User instance who logged in
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    
    Raises:
        TypeError: If _user is not an instance of the configured user model
    
    Notes:
        - Returns False if user has no email address
        - Returns False if EMAIL_HANDLER or EMAIL_PROVIDER not configured
        - Logs warnings/errors for configuration issues or send failures
        - Uses Celery for async email delivery if configured
    """
    # Get the configured user model
    user_model = get_user_model()
    
    # Validate user parameter type
    if not isinstance(_user, user_model):
        raise TypeError(f'User {_user} is not an instance of {user_model.__name__}')
    
    # Check if user has an email address
    if not _user.email:
        logger.warning(f'User {_user} does not have an email address to receive welcome message')
        return False
    
    # Verify EMAIL_HANDLER is configured
    if not hasattr(settings, 'EMAIL_HANDLER'):
        logger.warning('EMAIL_HANDLER not configured.')
        return False
    
    # Verify EMAIL_PROVIDER is configured
    if not hasattr(settings, 'EMAIL_PROVIDER'):
        logger.warning('EMAIL_PROVIDER not configured.')
        return False
    
    # Attempt to send login notification email
    try:
        # Initialize email handler with configured provider
        email = settings.EMAIL_HANDLER(
            settings.EMAIL_PROVIDER,
            api_key=None,
            use_celery=True,
            email_from=settings.DEFAULT_FROM_EMAIL
        )
        
        # Build HTML email content
        rendered_file = build_login_message_html(request, _user)
        
        # Send the email
        return email.send_email(
            to=_user.email,
            subject='New login to your Rattel account',
            body=rendered_file,
            html=True
        )
    except Exception as e:
        # Log email sending failure
        logger.error(f'Failed to send an email to {_user}: {e}')
        return False


def build_login_message_html(request: HttpRequest, user):
    """
    Builds the HTML content for login notification email.
    
    Renders the login notification template with user information and login
    metadata including timestamp, IP address, and user agent.
    
    Args:
        request: The HttpRequest object containing login metadata
        user: The User instance who logged in
    
    Returns:
        str: Rendered HTML string for the email body
    
    Raises:
        TypeError: If user is not an instance of the configured user model
    
    Template Context:
        - user_name: User's display name or username
        - login_time: Formatted timestamp of login (YYYY-MM-DD HH:MM:SS)
        - ip_address: Client's IP address
        - user_agent: Client's browser/device user agent string
        - site_name: Application name (Rattel)
    """
    # Get the configured user model
    user_model = get_user_model()
    
    # Validate user parameter type
    if not isinstance(user, user_model):
        raise TypeError(f'User {user} is not an instance of {user_model.__name__}')
    
    # Build template context with login information
    render_context = {
        'user_name': user.name or user.username,  # Fallback to username if name not set
        'login_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': GetDataMixin.get_client_ip(request),
        'user_agent': GetDataMixin.get_client_user_agent(request),
        'site_name': 'Rattel',
    }
    
    # Render and return the HTML template
    return render_to_string(
        request=request,
        template_name='login_message.html',
        context=render_context
    )
