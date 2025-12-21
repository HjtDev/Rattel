from notifications.providers.base import BaseSMSProvider
from typing import Type


class SMSHandler:
    """
    Main SMS Service Handler.
    Provides a simple interface to send SMS.
    For advanced features, access SMSHandler.provider directly.
    """
    
    def __init__(self, provider_class: Type[BaseSMSProvider], api_key: str = None, **provider_kwargs):
        """
        Initialize SMS handler with a provider class.
       
        Args:
            provider_class: The SMS provider class (not instance)
            api_key: API key for the provider
            **provider_kwargs: Additional provider-specific arguments
        """
        self.api_key = api_key
        self.provider = self._initialize_provider(provider_class, **provider_kwargs)
    
    def _initialize_provider(self, provider_class: Type[BaseSMSProvider], **provider_kwargs) -> BaseSMSProvider:
        """Initialize the SMS provider with validation."""
        if provider_class.REQUIRES_API_KEY and not self.api_key:
            raise ValueError(f'API key is required for provider {provider_class.__name__}')
        
        return provider_class(self.api_key, **provider_kwargs)
    
    def send(self, to: str, message: str) -> bool:
        """
        Send a simple SMS to a single recipient.
        
        Args:
            to: Recipient phone number
            message: Message to send
            
        Returns:
            True if sent successfully
        """
        return self.provider.send(to, message)
    