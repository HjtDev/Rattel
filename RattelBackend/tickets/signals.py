import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
def sms_on_new_ticket(sender, instance: Ticket, created, **kwargs):
    if not created:
        return

    required_settings = (
        'SMS_HANDLER',
        'SMS_PROVIDER',
        'SMS_SETTINGS',
        'SMS_API_ADMIN',
        'SMS_API_NEW_TICKET_ALERT_TEMPLATE',
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
            settings.SMS_API_NEW_TICKET_ALERT_TEMPLATE,
            settings.SMS_API_ADMIN,
            instance.user.username,
            instance.get_category_display(),
        )
        if not sent:
            logger.warning('SMS provider returned False for new ticket alert')
    except Exception as e:
        logger.error(f'Failed to send new ticket SMS alert. Exception: {e}', exc_info=True)
