import pytest
from django.conf import settings
from django.core import mail


class DummyRequest:
    def __init__(self, method="POST", data=None, query_params=None):
        self.method = method
        self.data = data or {}
        self.query_params = query_params or {}


@pytest.fixture
def post_request():
    def _factory(data):
        return DummyRequest(method="POST", data=data)
    return _factory


@pytest.fixture
def get_request():
    def _factory(query_params):
        return DummyRequest(method="GET", query_params=query_params)
    return _factory

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configure test environment for all tests."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    
    # Make Celery run synchronously in tests
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    
    mail.outbox = []
    
    yield
    
    mail.outbox = []


@pytest.fixture
def smtp_provider():
    """Create an SMTP provider with Celery disabled for testing."""
    from notifications.providers.email.smtp import SMTPEmailProvider
    return SMTPEmailProvider(email_from='test@gmail.com', use_celery=False)


@pytest.fixture
def smtp_provider_async():
    """Create an SMTP provider with Celery enabled (runs sync in tests due to EAGER mode)."""
    from notifications.providers.email.smtp import SMTPEmailProvider
    return SMTPEmailProvider(email_from='test@gmail.com', use_celery=True)


@pytest.fixture
def email_handler():
    """Create an email handler with Celery disabled."""
    from notifications.handlers.email import EmailHandler
    from notifications.providers.email.smtp import SMTPEmailProvider
    return EmailHandler(SMTPEmailProvider, use_celery=False, email_from='test@gmail.com')


@pytest.fixture
def email_handler_async():
    """Create an email handler with Celery enabled."""
    from notifications.handlers.email import EmailHandler
    from notifications.providers.email.smtp import SMTPEmailProvider
    return EmailHandler(SMTPEmailProvider, use_celery=True, email_from='test@gmail.com')
