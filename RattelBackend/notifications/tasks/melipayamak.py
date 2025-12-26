from celery import shared_task
from notifications.providers.sms.melipayamak import Api
import logging


logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={'max_retries': 3}
)
def send_sms_task(self, to: str, sender: str, message: str, is_flash: bool, **kwargs):
    return Api(**kwargs).sms(**kwargs).send(to, sender, message, is_flash)

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=10,
    retry_kwargs={'max_retries': 3}
)
def send_sms_with_template_task(self, text: str, to: str, body_id: int | str, **kwargs):
    return Api(username=kwargs.get('username'), password=kwargs.get('password')).sms(_method=kwargs.get('_method'), _type=kwargs.get('_type')).send_by_base_number(text, to, body_id)

