from django.core.exceptions import ValidationError
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from notifications.providers.base import BaseEmailProvider


class SMTPEmailProvider(BaseEmailProvider):
    """
    SMTP-based email provider using Django's email backend.

    Requires the following Django settings to be configured in settings.py:
    - EMAIL_BACKEND
    - EMAIL_HOST
    - EMAIL_HOST_USER
    - EMAIL_HOST_PASSWORD
    - EMAIL_PORT
    - EMAIL_USE_SSL
    - EMAIL_USE_TLS
    - DEFAULT_FROM_EMAIL
    """
    
    REQUIRES_API_KEY = False
    
    def __init__(self, api_key=None, email_from: str = None):
        super().__init__(api_key)
        
        # Use provided email or fall back to Django settings
        self.email_from = email_from or settings.DEFAULT_FROM_EMAIL
        
        if not self.validate_recipients([self.email_from]):
            raise ValidationError(f'Invalid email address: {self.email_from}')
    
    def send_mail(self, to: str, subject: str, body: str, html: bool = False, fail_silently: bool = False) -> bool:
        """Send an email using Django's send_mail or EmailMultiAlternatives."""
        # Validate inputs
        if not self.validate_recipients([to]):
            raise ValidationError("'to' must be a valid email address")
        
        if not isinstance(subject, str) or not subject.strip():
            raise TypeError("'subject' must be a non-empty string")
        
        if not isinstance(body, str) or not body.strip():
            raise TypeError("'body' must be a non-empty string")
        
        if not isinstance(html, bool):
            raise TypeError("'html' must be a boolean value")
        
        if not isinstance(fail_silently, bool):
            raise TypeError("'fail_silently' must be a boolean value")
        
        # Send email
        try:
            if html:
                # Send HTML email
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body,  # Plain text fallback
                    from_email=self.email_from,
                    to=[to]
                )
                msg.attach_alternative(body, "text/html")
                result = msg.send(fail_silently=fail_silently)
            else:
                # Send plain text email
                result = send_mail(
                    subject=subject,
                    message=body,
                    from_email=self.email_from,
                    recipient_list=[to],
                    fail_silently=fail_silently
                )
            
            return result == 1
        except Exception as e:
            if fail_silently:
                return False
            raise
    
    def send_mails(self, to: list[str], subject: str, body: str, html: bool = False, fail_silently: bool = False) -> bool:
        """Send an email to multiple recipients."""
        # Validate inputs
        if not isinstance(to, list) or not to:
            raise ValidationError("'to' must be a non-empty list")
        
        if not self.validate_recipients(to):
            raise ValidationError("'to' must contain valid email addresses")
        
        if not isinstance(subject, str) or not subject.strip():
            raise TypeError("'subject' must be a non-empty string")
        
        if not isinstance(body, str) or not body.strip():
            raise TypeError("'body' must be a non-empty string")
        
        if not isinstance(html, bool):
            raise TypeError("'html' must be a boolean value")
        
        if not isinstance(fail_silently, bool):
            raise TypeError("'fail_silently' must be a boolean value")
        
        # Send emails
        try:
            if html:
                # Send HTML email to multiple recipients
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email=self.email_from,
                    to=to
                )
                msg.attach_alternative(body, "text/html")
                result = msg.send(fail_silently=fail_silently)
            else:
                # Send plain text email to multiple recipients
                result = 0
                for recipient in to:
                    result += send_mail(
                        subject=subject,
                        message=body,
                        from_email=self.email_from,
                        recipient_list=[recipient],
                        fail_silently=fail_silently
                    )
            
            return result == len(to)
        except Exception as e:
            if fail_silently:
                return False
            raise
