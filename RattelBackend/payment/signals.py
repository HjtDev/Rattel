from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from setuptools.command.install_scripts import install_scripts

from .models import Transaction
from django.conf import settings
import logging


logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transaction)
def email_on_payment(sender, instance: Transaction, created, **kwargs):
    """
    Django signal receiver that sends email notifications for new transactions.
    
    Automatically triggered after a Transaction instance is saved. Sends an HTML
    email to the user with transaction details if the user has enabled email
    notifications in their settings.
    
    Args:
        sender: The model class that sent the signal (Transaction)
        instance: The Transaction instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments from the signal
    
    Returns:
        None: Function exits early if conditions aren't met
    
    Conditions for sending email:
        - Transaction must be newly created (not an update)
        - User must have an email address
        - User settings must exist and email_on_payment must be enabled
        - Required Django settings must be configured
    
    Required Settings:
        - EMAIL_HANDLER: Email handler class
        - EMAIL_PROVIDER: Email service provider
        - EMAIL_USE_CELERY: Whether to use async delivery
        - SITE_NAME: Application name for email content
    
    Notes:
        - Logs warnings for missing configuration
        - Logs errors for initialization or sending failures
        - Uses HTML template 'transaction_result.html'
        - Supports async delivery via Celery if configured
    """
    
    # Only process newly created transactions
    if not created:
        return
    
    # Check if user has an email address
    if not instance.user.email:
        return
    
    # Verify user settings exist and email notifications are enabled
    user_settings = getattr(instance.user, 'settings', None)
    if not user_settings or not user_settings.email_on_payment:
        return
    
    # Define required Django settings
    required_settings = (
        'EMAIL_HANDLER',
        'EMAIL_PROVIDER',
        'EMAIL_USE_CELERY',
        'SITE_NAME',
    )
    
    # Verify all required settings are configured
    for setting in required_settings:
        if not hasattr(settings, setting):
            logger.warning(f'{setting} not configured')
            return
    
    # Initialize email handler
    try:
        email = settings.EMAIL_HANDLER(
            settings.EMAIL_PROVIDER,
            api_key=None,
            use_celery=settings.EMAIL_USE_CELERY,
            email_from=settings.DEFAULT_FROM_EMAIL
        )
    except Exception as e:
        logger.error(f'Failed to initialize email handler: {e}')
        return
    
    # Render HTML email content with transaction details
    rendered_content = render_to_string(
        template_name='transaction_result.html',
        context={
            'user_name': instance.user.name or instance.user.username,
            'transaction_status': instance.transaction_status,
            'amount': instance.amount,
            'currency': instance.currency,
            'transaction_type': instance.transaction_type,
            'transaction_reason': instance.transaction_reason,
            'tracking_id': instance.tracking_id,
            'description': instance.description,
            'created_at': instance.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'site_name': settings.SITE_NAME,
        }
    )
    
    # Attempt to send the email
    try:
        sent = email.send_email(
            to=instance.user.email,
            subject=f'{settings.SITE_NAME} - Transaction {instance.tracking_id}',
            body=rendered_content,
            html=True
        )
        # Log if email provider indicates failure
        if not sent:
            logger.warning(f'Email provider returned False for {instance.user.email}')
    except Exception as e:
        logger.error(
            f'Failed to send transaction email to {instance.user.email}. Exception: {e}',
            exc_info=True
        )

@receiver(post_save, sender=Transaction)
def sms_on_payment(sender, instance: Transaction, created, **kwargs):
    """
    Django signal receiver that sends SMS notifications for new transactions.
    
    Automatically triggered after a Transaction instance is saved. Sends a text
    message to the user with transaction details if the user has enabled SMS
    notifications in their settings.
    
    Args:
        sender: The model class that sent the signal (Transaction)
        instance: The Transaction instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments from the signal
    
    Returns:
        None: Function exits early if conditions aren't met
    
    Conditions for sending SMS:
        - Transaction must be newly created (not an update)
        - User must have a phone number
        - User settings must exist and sms_on_payment must be enabled
        - Required Django settings must be configured
    
    Required Settings:
        - SMS_HANDLER: SMS handler class
        - SMS_PROVIDER: SMS service provider
        - SMS_SETTINGS: Provider-specific configuration dict
        - SITE_NAME: Application name for SMS content
    
    SMS Content Includes:
        - Transaction tracking ID
        - Amount and currency
        - Transaction status (uppercase)
        - Transaction type (uppercase)
        - Transaction reason (uppercase)
        - Timestamp
        - Site name
    
    Notes:
        - Logs warnings for missing configuration
        - Logs errors for initialization or sending failures
        - Uses plain text format for SMS content
    """
    
    # Only process newly created transactions
    if not created:
        return

    logger.info(f'{instance.transaction_status=}')
    if instance.transaction_status != instance.TransactionStatus.SUCCESS:
        return

    # Check if user has a phone number
    if not instance.user.phone:
        return
    
    # Verify user settings exist and SMS notifications are enabled
    user_settings = getattr(instance.user, 'settings', None)
    if not user_settings or not user_settings.sms_on_payment:
        return
    
    # Define required Django settings
    required_settings = (
        'SMS_HANDLER',
        'SMS_PROVIDER',
        'SMS_SETTINGS',
        'SITE_NAME',
    )
    
    # Verify all required settings are configured
    for setting in required_settings:
        if not hasattr(settings, setting):
            logger.warning(f'{setting} not configured')
            return
    
    # Initialize SMS handler
    try:
        sms = settings.SMS_HANDLER(
            settings.SMS_PROVIDER,
            **settings.SMS_SETTINGS
        )
    except Exception as e:
        logger.error(f'Failed to initialize SMS handler: {e}')
        return

    # Attempt to send the SMS
    try:
        sent = sms.provider.send_with_template(
            settings.SMS_API_PAYMENT_SUCCESS_TEMPLATE,
            instance.user.phone,
            f'{instance.amount:,} ریال',
            instance.get_transaction_type_display(),
            instance.get_transaction_reason_display(),
            instance.tracking_id,
        )
        # Log if SMS provider indicates failure
        if not sent:
            logger.warning(f'SMS provider returned False for {instance.user.phone}')
    except Exception as e:
        logger.error(
            f'Failed to send transaction SMS to {instance.user.phone}. Exception: {e}',
            exc_info=True
        )
