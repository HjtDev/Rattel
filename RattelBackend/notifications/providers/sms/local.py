from django.core.exceptions import ValidationError
from notifications.providers.base import BaseSMSProvider
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class LocalSMSProvider(BaseSMSProvider):
    """
    Local SMS Provider for development and testing.
    Outputs SMS to console/logger instead of actually sending.
    """
    
    REQUIRES_API_KEY = False
    
    def __init__(self, api_key: str = None, sender: str = 'TEST', output: Callable = None):
        """
        Initialize the local SMS provider.
        
        Args:
            sender: Sender name/phone number
            output: Callable to output messages (defaults to logger.info)
            api_key: Not required for local provider
        """
        super().__init__(api_key)
        
        if not isinstance(sender, str) or not sender.strip():
            raise ValidationError("Sender must be a non-empty string")
        
        self.sender = sender
        self.output = output or logger.info
        self.output(f'LocalSMSProvider initialized with sender: {sender}')
    
    def send(self, to: str, message: str) -> bool:
        """
        Send SMS to a single contact (simulated).
        
        Args:
            to: Recipient phone number
            message: Message to send
            
        Returns:
            True if successful
        """
        # Validate contact
        if not self.validate_contacts([to]):
            raise ValidationError(f"Invalid phone number: {to}")
        
        # Validate message
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("Message must be a non-empty string")
        
        # Output the message
        self.output(f'[SMS] From: {self.sender} | To: {to} | Message: {message}')
        return True
    
    def send_to_list(self, to: list[str], message: str) -> bool:
        """
        Send the same message to multiple contacts (simulated).
        
        Args:
            to: List of recipient phone numbers
            message: Message to send to all
            
        Returns:
            True if all successful
        """
        if not isinstance(to, list) or not to:
            raise ValidationError("'to' must be a non-empty list")
        
        if not self.validate_contacts(to):
            raise ValidationError("Invalid contacts in list")
        
        if not isinstance(message, str) or not message.strip():
            raise ValidationError("Message must be a non-empty string")
        
        self.output(f'[SMS BULK] Sending to {len(to)} recipients from {self.sender}')
        
        for contact in to:
            self.send(contact, message)
        
        return True
    
    def send_to_list_with_builder(
            self,
            to: list[str],
            message_template: str,
            message_builder: Callable,
            **builder_kwargs
    ) -> bool:
        """
        Build unique messages for each contact and send them.
        
        Args:
            to: List of recipient phone numbers
            message_template: Template string with placeholders
            message_builder: Function that takes (contact, template, **kwargs) and returns final message
            **builder_kwargs: Additional arguments for message_builder
            
        Returns:
            True if all successful
        """
        if not isinstance(to, list) or not to:
            raise ValidationError("'to' must be a non-empty list")
        
        if not self.validate_contacts(to):
            raise ValidationError("Invalid contacts in list")
        
        if not isinstance(message_template, str) or not message_template.strip():
            raise ValidationError("Message template must be a non-empty string")
        
        if not callable(message_builder):
            raise TypeError("message_builder must be callable")
        
        self.output(f'[SMS CUSTOM BULK] Sending to {len(to)} recipients with custom messages')
        
        messages = {}
        for contact in to:
            try:
                custom_message = message_builder(contact, message_template, **builder_kwargs)
                messages[contact] = custom_message
            except Exception as e:
                raise ValidationError(f"Error building message for {contact}: {str(e)}")
        
        # Send all custom messages
        for contact, custom_message in messages.items():
            self.send(contact, custom_message)
        
        return True
