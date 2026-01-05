from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from .models import Transaction
from django.conf import settings
import logging


logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transaction)
def email_on_payment(sender, instance: Transaction, created, **kwargs):
    if not created:
        return
    
    if not instance.user.email:
        return
    
    user_settings = getattr(instance.user, 'settings', None)
    if not user_settings or not user_settings.email_on_payment:
        return
    
    required_settings = (
        'EMAIL_HANDLER',
        'EMAIL_PROVIDER',
        'EMAIL_USE_CELERY',
        'SITE_NAME',
    )
    
    for setting in required_settings:
        if not hasattr(settings, setting):
            logger.warning(f'{setting} not configured')
            return
    
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
    
    try:
        sent = email.send_email(
            to=instance.user.email,
            subject=f'{settings.SITE_NAME} - Transaction {instance.tracking_id}',
            body=rendered_content,
            html=True
        )
        if not sent:
            logger.warning(f'Email provider returned False for {instance.user.email}')
    except Exception as e:
        logger.error(
            f'Failed to send transaction email to {instance.user.email}. Exception: {e}',
            exc_info=True
        )
