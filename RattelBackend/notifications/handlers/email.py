from typing import Type
from notifications.providers.base import BaseEmailProvider


class EmailHandler:
    """Main Email Service Handler"""
    
    def __init__(self, provider_class: Type[BaseEmailProvider], api_key: str = None, use_celery: bool = False, **provider_kwargs):
        """
        Initialize email handler with a provider class.
        
        Args:
            provider_class: The email provider class (not instance)
            api_key: API key if required by the provider
        """
        self.api_key = api_key
        self.use_celery = use_celery
        self.provider = self._initialize_provider(provider_class, **provider_kwargs)
    
    def _initialize_provider(self, provider_class: Type[BaseEmailProvider], **kwargs) -> BaseEmailProvider:
        """Initialize the email provider with validation."""
        # Check if API key is required but not provided
        if provider_class.REQUIRES_API_KEY and not self.api_key:
            raise ValueError(f'API key is required for provider {provider_class.__name__}')
        
        return provider_class(self.api_key, self.use_celery, **kwargs)
    
    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> bool:
        """Send an email using the configured provider."""
        return self.provider.send_mail(to, subject, body, html)
    
    def send_email_to_list(self, to: list[str], subject: str, body: str, html: bool = False) -> bool:
        """Send an email to a list of recipients using the configured provider."""
        return self.provider.send_mails(to, subject, body, html)
