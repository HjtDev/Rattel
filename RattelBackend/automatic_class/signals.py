import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ClassRequest

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ClassRequest)
def sms_on_new_class_request(sender, instance: ClassRequest, created, **kwargs):
    if not created:
        return

    required_settings = (
        'SMS_HANDLER',
        'SMS_PROVIDER',
        'SMS_SETTINGS',
        'SMS_API_ADMIN',
        'SMS_API_NEW_AUTOMATIC_PLAN_REQUEST_ALERT_TEMPLATE',
    )
    for setting in required_settings:
        if not hasattr(settings, setting):
            logger.warning(f'{setting} not configured')
            return

    try:
        sms = settings.SMS_HANDLER(settings.SMS_PROVIDER, **settings.SMS_SETTINGS)
    except Exception as e:
        logger.error(f'Failed to initialize SMS handler: {e}')
        return

    try:
        sent = sms.provider.send_with_template(
            settings.SMS_API_NEW_AUTOMATIC_PLAN_REQUEST_ALERT_TEMPLATE,
            settings.SMS_API_ADMIN,
            instance.user.username,
        )
        if not sent:
            logger.warning('SMS provider returned False for new class request alert')
    except Exception as e:
        logger.error(f'Failed to send new class request SMS alert. Exception: {e}', exc_info=True)
