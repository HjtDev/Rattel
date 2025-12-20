import pytest
from django.core.exceptions import ValidationError
from django.core import mail
from django.test import override_settings
from notifications.providers.email.smtp import SMTPEmailProvider
from notifications.handlers.email import EmailHandler


@pytest.fixture
def smtp_provider():
    """Create an SMTP provider instance for testing."""
    return SMTPEmailProvider(email_from='test@gmail.com')


@pytest.fixture
def email_handler():
    """Create an email handler with SMTP provider."""
    return EmailHandler(SMTPEmailProvider, api_key=None, use_celery=False)


class TestBaseEmailProvider:
    """Test base email provider functionality."""
    
    def test_validate_single_email(self, smtp_provider):
        """Test single email validation."""
        assert smtp_provider.validate_recipients('valid@example.com') is True
        assert smtp_provider.validate_recipients('invalid-email') is False
        assert smtp_provider.validate_recipients('') is False
    
    def test_validate_email_list(self, smtp_provider):
        """Test email list validation."""
        assert smtp_provider.validate_recipients(['valid@example.com', 'another@test.com']) is True
        assert smtp_provider.validate_recipients(['valid@example.com', 'invalid']) is False
        assert smtp_provider.validate_recipients([]) is False
    
    def test_validate_invalid_type(self, smtp_provider):
        """Test validation with invalid input types."""
        assert smtp_provider.validate_recipients(123) is False
        assert smtp_provider.validate_recipients(None) is False
        assert smtp_provider.validate_recipients({'email': 'test@example.com'}) is False


class TestSMTPEmailProvider:
    """Test SMTP email provider."""
    
    def test_initialization_valid_email(self):
        """Test provider initialization with valid email."""
        provider = SMTPEmailProvider(email_from='valid@example.com')
        assert provider.email_from == 'valid@example.com'
    
    def test_initialization_invalid_email(self):
        """Test provider initialization with invalid email."""
        with pytest.raises(ValidationError):
            SMTPEmailProvider(email_from='invalid-email')
    
    @override_settings(DEFAULT_FROM_EMAIL='default@example.com')
    def test_initialization_default_email(self):
        """Test provider falls back to Django settings."""
        provider = SMTPEmailProvider()
        assert provider.email_from == 'default@example.com'
    
    @pytest.mark.django_db
    def test_send_plain_text_email(self, smtp_provider):
        """Test sending plain text email."""
        result = smtp_provider.send_mail(
            to='recipient@example.com',
            subject='Test Subject',
            body='Test Body',
            html=False
        )
        
        assert result is True
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Test Subject'
        assert mail.outbox[0].body == 'Test Body'
        assert mail.outbox[0].to == ['recipient@example.com']
    
    @pytest.mark.django_db
    def test_send_html_email(self, smtp_provider):
        """Test sending HTML email."""
        result = smtp_provider.send_mail(
            to='recipient@example.com',
            subject='HTML Test',
            body='<h1>Test HTML</h1>',
            html=True
        )
        
        assert result is True
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'HTML Test'
        assert len(mail.outbox[0].alternatives) == 1
        assert mail.outbox[0].alternatives[0][1] == 'text/html'
    
    @pytest.mark.django_db
    def test_send_to_multiple_recipients(self, smtp_provider):
        """Test sending email to multiple recipients."""
        recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']
        
        result = smtp_provider.send_mails(
            to=recipients,
            subject='Multi Recipient Test',
            body='Test to multiple',
            html=False
        )
        
        assert result is True
        assert len(mail.outbox) == 3
        
        for i in range(0, len(mail.outbox)):
            assert mail.outbox[i].to == [recipients[i]]
    
    def test_send_invalid_recipient(self, smtp_provider):
        """Test sending to invalid email raises error."""
        with pytest.raises(ValidationError, match="must be a valid email"):
            smtp_provider.send_mail(
                to='invalid-email',
                subject='Test',
                body='Test'
            )
    
    def test_send_empty_subject(self, smtp_provider):
        """Test sending with empty subject raises error."""
        with pytest.raises(TypeError, match="must be a non-empty string"):
            smtp_provider.send_mail(
                to='valid@example.com',
                subject='',
                body='Test'
            )
    
    def test_send_empty_body(self, smtp_provider):
        """Test sending with empty body raises error."""
        with pytest.raises(TypeError, match="must be a non-empty string"):
            smtp_provider.send_mail(
                to='valid@example.com',
                subject='Test',
                body=''
            )
    
    def test_send_invalid_html_type(self, smtp_provider):
        """Test sending with invalid html parameter type."""
        with pytest.raises(TypeError, match="must be a boolean"):
            smtp_provider.send_mail(
                to='valid@example.com',
                subject='Test',
                body='Test',
                html='yes'  # Should be boolean
            )


class TestEmailHandler:
    """Test email handler."""
    
    def test_handler_initialization(self):
        """Test handler initializes correctly."""
        handler = EmailHandler(SMTPEmailProvider, api_key=None, use_celery=False)
        assert handler.provider is not None
        assert isinstance(handler.provider, SMTPEmailProvider)
    
    @pytest.mark.django_db
    def test_send_email_via_handler(self, email_handler):
        """Test sending email through handler."""
        result = email_handler.send_email(
            to='recipient@example.com',
            subject='Handler Test',
            body='Test via handler'
        )
        
        assert result is True
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Handler Test'
    
    @pytest.mark.django_db
    def test_send_email_list_via_handler(self, email_handler):
        """Test sending to multiple recipients via handler."""
        recipients = ['user1@example.com', 'user2@example.com']
        
        result = email_handler.send_email_to_list(
            to=recipients,
            subject='List Test',
            body='Test to list'
        )
        
        assert result is True
        assert len(mail.outbox) == 2
        
        for i in range(0, len(mail.outbox)):
            assert mail.outbox[i].to == [recipients[i]]
    
    def test_handler_requires_api_key_for_providers_that_need_it(self):
        """Test handler validates API key requirement."""
        # Mock a provider that requires API key
        class APIProvider(SMTPEmailProvider):
            REQUIRES_API_KEY = True
        
        with pytest.raises(ValueError, match="API key is required"):
            EmailHandler(APIProvider)
        
        # Should work with API key
        handler = EmailHandler(APIProvider, api_key='test-key')
        assert handler.provider.api_key == 'test-key'
        
        
class TestCeleryMode:
    """Test email sending with Celery enabled."""
    
    @pytest.mark.django_db
    def test_send_email_with_celery(self, smtp_provider_async):
        """Test sending email with Celery (runs sync due to EAGER mode)."""
        result = smtp_provider_async.send_mail(
            to='recipient@example.com',
            subject='Celery Test',
            body='Test with Celery',
            html=False
        )
        
        assert result is True
        # Email should still be in outbox due to EAGER mode
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Celery Test'
    
    @pytest.mark.django_db
    def test_send_emails_with_celery(self, smtp_provider_async):
        """Test sending multiple emails with Celery."""
        recipients = ['user1@example.com', 'user2@example.com']
        
        result = smtp_provider_async.send_mails(
            to=recipients,
            subject='Bulk Celery Test',
            body='Test bulk with Celery',
            html=False
        )
        
        assert result is True
        assert len(mail.outbox) == 2