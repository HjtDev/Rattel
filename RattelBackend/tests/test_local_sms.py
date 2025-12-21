import pytest
from django.core.exceptions import ValidationError
from notifications.providers.sms.local import LocalSMSProvider
from notifications.handlers.sms import SMSHandler


class TestBaseSMSProvider:
    """Test base SMS provider functionality."""
    
    def test_validate_single_contact_valid(self, local_sms_provider):
        """Test validation of valid single phone number."""
        assert local_sms_provider.validate_contacts('09123456789') is True
        assert local_sms_provider.validate_contacts('09000000000') is True
        assert local_sms_provider.validate_contacts('09999999999') is True
    
    def test_validate_single_contact_invalid(self, local_sms_provider):
        """Test validation of invalid single phone number."""
        assert local_sms_provider.validate_contacts('9123456789') is False  # Missing leading 0
        assert local_sms_provider.validate_contacts('091234567890') is False  # Too long (12 digits)
        assert local_sms_provider.validate_contacts('0912345678') is False  # Too short (10 digits)
        assert local_sms_provider.validate_contacts('08123456789') is False  # Doesn't start with 09
        assert local_sms_provider.validate_contacts('09123456abc') is False  # Contains letters
        assert local_sms_provider.validate_contacts('') is False  # Empty string
        assert local_sms_provider.validate_contacts(' ') is False  # Whitespace
    
    def test_validate_contact_list_valid(self, local_sms_provider):
        """Test validation of valid contact list."""
        assert local_sms_provider.validate_contacts(['09123456789', '09987654321']) is True
        assert local_sms_provider.validate_contacts(['09111111111', '09222222222', '09333333333']) is True
    
    def test_validate_contact_list_invalid(self, local_sms_provider):
        """Test validation of invalid contact list."""
        assert local_sms_provider.validate_contacts(['09123456789', 'invalid']) is False
        assert local_sms_provider.validate_contacts(['invalid', '09123456789']) is False
        assert local_sms_provider.validate_contacts(['09123456789', '']) is False
        assert local_sms_provider.validate_contacts([]) is False  # Empty list
    
    def test_validate_contact_invalid_types(self, local_sms_provider):
        """Test validation with invalid input types."""
        assert local_sms_provider.validate_contacts(123) is False
        assert local_sms_provider.validate_contacts(9123456789) is False
        assert local_sms_provider.validate_contacts(None) is False
        assert local_sms_provider.validate_contacts({'phone': '09123456789'}) is False
        assert local_sms_provider.validate_contacts(('09123456789',)) is False  # Tuple not list
    
    def test_validate_contact_mixed_types_in_list(self, local_sms_provider):
        """Test validation with mixed types in list."""
        assert local_sms_provider.validate_contacts(['09123456789', 123]) is False
        assert local_sms_provider.validate_contacts(['09123456789', None]) is False
        assert local_sms_provider.validate_contacts([123, 456]) is False


class TestLocalSMSProvider:
    """Test local SMS provider."""
    
    def test_initialization_valid_sender(self, captured_output):
        """Test provider initialization with valid sender."""
        provider = LocalSMSProvider(sender='MySender', output=captured_output)
        
        assert provider.sender == 'MySender'
        assert provider.api_key is None
        assert len(captured_output.messages) == 1
        assert 'LocalSMSProvider initialized with sender: MySender' in captured_output.messages[0]
    
    def test_initialization_with_custom_output(self):
        """Test provider initialization with custom output function."""
        custom_messages = []
        
        def custom_output(msg):
            custom_messages.append(f"CUSTOM: {msg}")
        
        provider = LocalSMSProvider(sender='TestSender', output=custom_output)
        
        assert len(custom_messages) == 1
        assert 'CUSTOM:' in custom_messages[0]
    
    def test_initialization_invalid_sender_empty(self):
        """Test provider initialization with empty sender."""
        with pytest.raises(ValidationError, match="Sender must be a non-empty string"):
            LocalSMSProvider(sender='', output=print)
    
    def test_initialization_invalid_sender_whitespace(self):
        """Test provider initialization with whitespace-only sender."""
        with pytest.raises(ValidationError, match="Sender must be a non-empty string"):
            LocalSMSProvider(sender='   ', output=print)
    
    def test_initialization_invalid_sender_type(self):
        """Test provider initialization with invalid sender type."""
        with pytest.raises(ValidationError):
            LocalSMSProvider(sender=123, output=print)
    
    def test_send_valid_sms(self, local_sms_provider, captured_output):
        """Test sending a valid SMS."""
        # Clear initialization message
        captured_output.messages.clear()
        
        result = local_sms_provider.send(
            to='09123456789',
            message='Test message'
        )
        
        assert result is True
        assert len(captured_output.messages) == 1
        assert '[SMS]' in captured_output.messages[0]
        assert 'TestSender' in captured_output.messages[0]
        assert '09123456789' in captured_output.messages[0]
        assert 'Test message' in captured_output.messages[0]
    
    def test_send_with_special_characters(self, local_sms_provider, captured_output):
        """Test sending SMS with special characters."""
        captured_output.messages.clear()
        
        result = local_sms_provider.send(
            to='09123456789',
            message='Hello! Your code is: #1234. Please verify @app.com'
        )
        
        assert result is True
        assert '#1234' in captured_output.messages[0]
        assert '@app.com' in captured_output.messages[0]
    
    def test_send_invalid_phone_number(self, local_sms_provider):
        """Test sending to invalid phone number raises error."""
        with pytest.raises(ValidationError, match="Invalid phone number"):
            local_sms_provider.send(
                to='invalid-phone',
                message='Test'
            )
    
    def test_send_empty_phone_number(self, local_sms_provider):
        """Test sending to empty phone number raises error."""
        with pytest.raises(ValidationError, match="Invalid phone number"):
            local_sms_provider.send(
                to='',
                message='Test'
            )
    
    def test_send_wrong_format_phone(self, local_sms_provider):
        """Test sending to incorrectly formatted phone."""
        with pytest.raises(ValidationError, match="Invalid phone number"):
            local_sms_provider.send(
                to='9123456789',  # Missing leading 0
                message='Test'
            )
    
    def test_send_empty_message(self, local_sms_provider):
        """Test sending empty message raises error."""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            local_sms_provider.send(
                to='09123456789',
                message=''
            )
    
    def test_send_whitespace_message(self, local_sms_provider):
        """Test sending whitespace-only message raises error."""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            local_sms_provider.send(
                to='09123456789',
                message='   '
            )
    
    def test_send_invalid_message_type(self, local_sms_provider):
        """Test sending with invalid message type raises error."""
        with pytest.raises(ValidationError):
            local_sms_provider.send(
                to='09123456789',
                message=123
            )
    
    def test_send_to_list_valid(self, local_sms_provider, captured_output):
        """Test sending to multiple contacts."""
        captured_output.messages.clear()
        
        contacts = ['09123456789', '09987654321', '09111111111']
        
        result = local_sms_provider.send_to_list(
            to=contacts,
            message='Bulk test message'
        )
        
        assert result is True
        # Should have 1 bulk header + 3 individual messages
        assert len(captured_output.messages) == 4
        assert '[SMS BULK]' in captured_output.messages[0]
        
        # Check all contacts received the message
        message_text = '\n'.join(captured_output.messages)
        for contact in contacts:
            assert contact in message_text
    
    def test_send_to_list_empty_list(self, local_sms_provider):
        """Test sending to empty list raises error."""
        with pytest.raises(ValidationError, match="must be a non-empty list"):
            local_sms_provider.send_to_list(
                to=[],
                message='Test'
            )
    
    def test_send_to_list_not_a_list(self, local_sms_provider):
        """Test sending with non-list parameter raises error."""
        with pytest.raises(ValidationError, match="must be a non-empty list"):
            local_sms_provider.send_to_list(
                to='09123456789',  # String instead of list
                message='Test'
            )
    
    def test_send_to_list_invalid_contacts(self, local_sms_provider):
        """Test sending to list with invalid contacts."""
        with pytest.raises(ValidationError, match="Invalid contacts"):
            local_sms_provider.send_to_list(
                to=['09123456789', 'invalid', '09987654321'],
                message='Test'
            )
    
    def test_send_to_list_empty_message(self, local_sms_provider):
        """Test sending to list with empty message."""
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            local_sms_provider.send_to_list(
                to=['09123456789', '09987654321'],
                message=''
            )
    
    def test_send_with_message_builder_valid(self, local_sms_provider, captured_output):
        """Test sending with message builder."""
        captured_output.messages.clear()
        
        def builder(contact, template, name='User', code='0000'):
            return template.format(contact=contact, name=name, code=code)
        
        contacts = ['09123456789', '09987654321']
        
        result = local_sms_provider.send_to_list_with_builder(
            to=contacts,
            message_template='Hello {name}, your number is {contact}. Code: {code}',
            message_builder=builder,
            name='John',
            code='1234'
        )
        
        assert result is True
        message_text = '\n'.join(captured_output.messages)
        assert 'John' in message_text
        assert '09123456789' in message_text
        assert '1234' in message_text
    
    def test_send_with_message_builder_different_messages(self, local_sms_provider, captured_output):
        """Test that message builder creates unique messages per contact."""
        captured_output.messages.clear()
        
        def builder(contact, template, **kwargs):
            # Create different message based on contact
            if contact == '09123456789':
                return "Message for first user"
            else:
                return "Message for second user"
        
        contacts = ['09123456789', '09987654321']
        
        result = local_sms_provider.send_to_list_with_builder(
            to=contacts,
            message_template='Template',
            message_builder=builder
        )
        
        assert result is True
        message_text = '\n'.join(captured_output.messages)
        assert 'first user' in message_text
        assert 'second user' in message_text
    
    def test_send_with_message_builder_invalid_contacts(self, local_sms_provider):
        """Test message builder with invalid contacts."""
        def builder(contact, template):
            return template.format(contact=contact)
        
        with pytest.raises(ValidationError, match="Invalid contacts"):
            local_sms_provider.send_to_list_with_builder(
                to=['09123456789', 'invalid'],
                message_template='Test {contact}',
                message_builder=builder
            )
    
    def test_send_with_message_builder_empty_template(self, local_sms_provider):
        """Test message builder with empty template."""
        def builder(contact, template):
            return template
        
        with pytest.raises(ValidationError, match="must be a non-empty string"):
            local_sms_provider.send_to_list_with_builder(
                to=['09123456789'],
                message_template='',
                message_builder=builder
            )
    
    def test_send_with_message_builder_not_callable(self, local_sms_provider):
        """Test message builder with non-callable."""
        with pytest.raises(TypeError, match="must be callable"):
            local_sms_provider.send_to_list_with_builder(
                to=['09123456789'],
                message_template='Test',
                message_builder='not_callable'
            )
    
    def test_send_with_message_builder_exception(self, local_sms_provider):
        """Test message builder that raises exception."""
        def bad_builder(contact, template):
            raise Exception("Builder error")
        
        with pytest.raises(ValidationError, match="Error building message"):
            local_sms_provider.send_to_list_with_builder(
                to=['09123456789'],
                message_template='Test',
                message_builder=bad_builder
            )


class TestSMSHandler:
    """Test SMS handler."""
    
    def test_handler_initialization_valid(self):
        """Test handler initializes correctly."""
        handler = SMSHandler(LocalSMSProvider, sender='TestSender')
        
        assert handler.provider is not None
        assert isinstance(handler.provider, LocalSMSProvider)
        assert handler.api_key is None
    
    def test_handler_initialization_with_api_key(self):
        """Test handler initialization with API key."""
        handler = SMSHandler(LocalSMSProvider, api_key='test-key', sender='TestSender')
        
        assert handler.api_key == 'test-key'
        assert handler.provider.api_key == 'test-key'
    
    def test_send_via_handler(self, local_sms_handler, captured_output):
        """Test sending SMS through handler."""
        captured_output.messages.clear()
        
        result = local_sms_handler.send(
            to='09123456789',
            message='Handler test'
        )
        
        assert result is True
        assert len(captured_output.messages) == 1
        assert '09123456789' in captured_output.messages[0]
        assert 'Handler test' in captured_output.messages[0]
    
    def test_send_multiple_messages_via_handler(self, local_sms_handler, captured_output):
        """Test sending multiple SMS through handler."""
        captured_output.messages.clear()
        
        local_sms_handler.send('09123456789', 'Message 1')
        local_sms_handler.send('09987654321', 'Message 2')
        
        assert len(captured_output.messages) == 2
        assert '09123456789' in captured_output.messages[0]
        assert '09987654321' in captured_output.messages[1]
    
    def test_handler_requires_api_key_when_needed(self):
        """Test handler validates API key requirement."""
        # Create a provider that requires API key
        class APIRequiredProvider(LocalSMSProvider):
            REQUIRES_API_KEY = True
        
        # Should raise error without API key
        with pytest.raises(ValueError, match="API key is required"):
            SMSHandler(APIRequiredProvider, sender='Test')
        
        # Should work with API key
        handler = SMSHandler(APIRequiredProvider, api_key='test-key', sender='Test')
        assert handler.provider.api_key == 'test-key'
    
    def test_handler_provider_access(self, local_sms_handler):
        """Test accessing provider directly through handler."""
        # Can access provider methods directly
        assert hasattr(local_sms_handler.provider, 'send')
        assert hasattr(local_sms_handler.provider, 'send_to_list')
        assert hasattr(local_sms_handler.provider, 'send_to_list_with_builder')
    
    def test_handler_with_invalid_provider(self):
        """Test handler with invalid provider class."""
        class InvalidProvider:
            pass
        
        with pytest.raises(AttributeError):
            SMSHandler(InvalidProvider, sender='Test')


class TestSMSProviderCredentials:
    """Test SMS provider credential validation."""
    
    def test_provider_without_api_key_when_required(self):
        """Test creating provider that requires API key without providing it."""
        class StrictProvider(LocalSMSProvider):
            REQUIRES_API_KEY = True
        
        with pytest.raises(ValueError, match="requires an API key"):
            StrictProvider(sender='Test')
    
    def test_provider_with_api_key_when_required(self):
        """Test creating provider with required API key."""
        class StrictProvider(LocalSMSProvider):
            REQUIRES_API_KEY = True
        
        provider = StrictProvider(api_key='valid-key', sender='Test')
        assert provider.api_key == 'valid-key'
    
    def test_provider_without_api_key_when_not_required(self, local_sms_provider):
        """Test creating provider that doesn't require API key."""
        assert local_sms_provider.api_key is None
        assert local_sms_provider.REQUIRES_API_KEY is False
