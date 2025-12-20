from abc import ABC, abstractmethod
import re


# noinspection RegExpRedundantEscape
class BaseEmailProvider(ABC):
    """Base Email Provider class for implementing different email providers"""
    
    REQUIRES_API_KEY = False
    EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.validate_credentials()
    
    def validate_credentials(self):
        """Validate that required credentials are provided"""
        if self.REQUIRES_API_KEY and not self.api_key:
            raise ValueError(f'{self.__class__.__name__} requires an API key')
    
    def validate_recipients(self, recipients: str | list[str]) -> bool:
        """Validates recipient(s) email address."""
        # Convert single recipient to list
        if isinstance(recipients, str):
            recipients = [recipients]
        
        # Check if it's a list
        if not isinstance(recipients, list):
            return False
        
        # Validate each email
        return all(isinstance(r, str) and bool(self.EMAIL_REGEX.match(r)) for r in recipients)
    
    @abstractmethod
    def send_mail(self, to: str, subject: str, body: str, html: bool = False, fail_silently: bool = False) -> bool:
        """Send an email. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def send_mails(self, to: list[str], subject: str, body: str, html: bool = False, fail_silently: bool = False) -> bool:
        """Send an email to a list of recipients. Must be implemented by subclasses."""
        pass
