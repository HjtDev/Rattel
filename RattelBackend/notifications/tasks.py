from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5, 'countdown': 60},
    retry_backoff=True,
)
def send_email_task(self, to: str, subject: str, body: str, from_email: str, html: bool = False, fail_silently: bool = False) -> bool:
    """Celery task to send a single email."""
    try:
        if html:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[to]
            )
            msg.attach_alternative(body, "text/html")
            result = msg.send(fail_silently=fail_silently)
        else:
            result = send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[to],
                fail_silently=fail_silently
            )
        
        success = result == 1
        logger.info(f"Email sent to {to}: {success}")
        return success
        
    except Exception as e:
        logger.error(f"Error sending email to {to}: {str(e)}")
        if not fail_silently:
            raise
        return False


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5, 'countdown': 60},
    retry_backoff=True,
)
def send_emails_task(self, to: list[str], subject: str, body: str, from_email: str, html: bool = False, fail_silently: bool = False) -> dict:
    """Celery task to send emails to multiple recipients."""
    success_count = 0
    failed = []
    
    for recipient in to:
        try:
            if html:
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email=from_email,
                    to=[recipient]
                )
                msg.attach_alternative(body, "text/html")
                result = msg.send(fail_silently=fail_silently)
            else:
                result = send_mail(
                    subject=subject,
                    message=body,
                    from_email=from_email,
                    recipient_list=[recipient],
                    fail_silently=fail_silently
                )
            
            if result == 1:
                success_count += 1
            else:
                failed.append(recipient)
                
        except Exception as e:
            logger.error(f"Error sending to {recipient}: {str(e)}")
            failed.append(recipient)
            if not fail_silently:
                raise
    
    return {
        'total': len(to),
        'success': success_count,
        'failed': len(failed),
        'failed_recipients': failed
    }