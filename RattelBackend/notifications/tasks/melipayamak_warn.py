# from notifications.providers.sms.melipayamak_service import MelipayamakProvider
# from celery import shared_task
# from django.conf import settings
import logging


logger = logging.getLogger(__name__)


# @shared_task(
#     bind=True,
#     autoretry_for=(Exception,),
#     retry_backoff=30,
#     retry_kwargs={'max_retries': 3}
# )
# def warn_admin_task(self):
#     sms = MelipayamakProvider(api_key=settings.SMS_API_KEY, username=settings.SMS_API_USERNAME, password=settings.SMS_API_PASSWORD, sender=None, use_soap=False, use_async=False, use_celery=False, admin='09186298438')
#     if not sms.warn_admin():
#         logger.info(f'Sending a warning to admin: {sms.admin}')
#         return True
#     return False