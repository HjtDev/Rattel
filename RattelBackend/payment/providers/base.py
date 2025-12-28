from abc import ABC, abstractmethod
from typing import Any, Dict
from enum import Enum


class GatewayResult(Enum):
    SUCCESS = 'success'
    FAILURE = 'failure'
    TIMEOUT = 'timeout'
    ERROR = 'error'

class BaseProvider(ABC):
    """
    Defines the four base methods all gateway providers should implement.
    """
    
    @abstractmethod
    def start_payment(self, amount: int, callback_url: str, **kwargs) -> tuple[bool, str]:
        """
        Initiates payment with the gateway provider.
        
        Args:
            amount: Payment amount
            callback_url: URL where gateway will send payment result
            **kwargs: Additional provider-specific parameters
            
        Returns:
            tuple[bool, str]: (success status, track_id or error message)
        """
        pass
    
    @abstractmethod
    def build_gateway_url(self, track_id: int, **kwargs) -> str:
        """
        Builds the redirect URL for the payment gateway.
        
        Args:
            track_id: Payment tracking identifier from start_payment
            **kwargs: Additional provider-specific parameters
            
        Returns:
            str: Complete gateway URL to redirect user to
        """
        pass
    
    @abstractmethod
    def validate_gateway_response(self, response_data: Dict[str, Any], **kwargs):
        """
        Validates and processes the callback response from gateway provider.
        
        Args:
            response_data: Raw callback data from gateway (query params or POST data)
            **kwargs: Additional provider-specific parameters
        """
        pass
    
    @abstractmethod
    def verify_transaction(self, track_id: str, **kwargs):
        """
        Queries the gateway provider to verify payment status.
        
        Args:
            track_id: Payment tracking identifier
            **kwargs: Additional provider-specific parameters
        """
        pass
