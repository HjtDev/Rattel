import pytest
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from django.core.exceptions import ImproperlyConfigured
from django.core.cache import cache
from cryptography.fernet import Fernet
import re
from authentication.OTP.otp import OTP


@pytest.fixture
def cipher():
    """Create a Fernet cipher for testing."""
    return Fernet(Fernet.generate_key())


@pytest.fixture
def otp_config(cipher):
    """Default OTP configuration for testing."""
    return {
        'TIMEOUT': timedelta(minutes=2),
        'ATTEMPTS': 3,
        'TOKEN_TYPE': 'int',
        'TOKEN_LENGTH': 4,
        'ENCRYPTOR': cipher,
    }


@pytest.fixture
def otp_config_str(cipher):
    """OTP configuration with string tokens."""
    return {
        'TIMEOUT': timedelta(minutes=2),
        'ATTEMPTS': 3,
        'TOKEN_TYPE': 'str',
        'TOKEN_LENGTH': 6,
        'ENCRYPTOR': cipher,
    }


@pytest.fixture
def otp_config_alphanumeric(cipher):
    """OTP configuration with alphanumeric tokens."""
    return {
        'TIMEOUT': timedelta(minutes=2),
        'ATTEMPTS': 3,
        'TOKEN_TYPE': 'alphanumeric',
        'TOKEN_LENGTH': 8,
        'ENCRYPTOR': cipher,
    }


@pytest.fixture
def otp_config_no_attempts(cipher):
    """OTP configuration with attempts disabled."""
    return {
        'TIMEOUT': timedelta(minutes=2),
        'ATTEMPTS': -1,
        'TOKEN_TYPE': 'int',
        'TOKEN_LENGTH': 4,
        'ENCRYPTOR': cipher,
    }


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def otp_instance(otp_config):
    """Create a basic OTP instance."""
    return OTP(indicator='test_user', config=otp_config)


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch('authentication.OTP.otp.get_redis_connection') as mock:
        redis_mock = MagicMock()
        redis_mock.ttl.return_value = 120
        mock.return_value = redis_mock
        yield redis_mock


class TestOTPInitialization:
    """Test OTP class initialization."""
    
    def test_init_valid_params(self, otp_config):
        """Test initialization with valid parameters."""
        otp = OTP(indicator='user123', config=otp_config)
        
        assert otp.indicator == 'user123'
        assert otp.cache_key == 'OTP-user123'
        assert otp._cache_prefix == 'OTP'
        assert otp._timeout == 120.0
        assert otp._attempts == 3
        assert otp._token_type == 'int'
        assert otp._token_length == 4
    
    def test_init_custom_cache_prefix(self, otp_config):
        """Test initialization with custom cache prefix."""
        otp = OTP(indicator='user123', config=otp_config, cache_prefix='CUSTOM')
        
        assert otp.cache_key == 'CUSTOM-user123'
        assert otp._cache_prefix == 'CUSTOM'
    
    def test_init_invalid_indicator_type(self, otp_config):
        """Test initialization with invalid indicator type."""
        with pytest.raises(TypeError, match='Indicator must be a string'):
            OTP(indicator=123, config=otp_config)
    
    def test_init_empty_indicator(self, otp_config):
        """Test initialization with empty indicator."""
        with pytest.raises(ValueError, match='Indicator must not be empty'):
            OTP(indicator='', config=otp_config)
    
    def test_init_whitespace_indicator(self, otp_config):
        """Test initialization with whitespace-only indicator."""
        with pytest.raises(ValueError, match='Indicator must not be empty'):
            OTP(indicator='   ', config=otp_config)
    
    def test_init_invalid_cache_prefix_type(self, otp_config):
        """Test initialization with invalid cache prefix type."""
        with pytest.raises(TypeError, match='Cache prefix must be a string'):
            OTP(indicator='user123', config=otp_config, cache_prefix=123)
    
    def test_init_empty_cache_prefix(self, otp_config):
        """Test initialization with empty cache prefix."""
        with pytest.raises(ValueError, match='Cache prefix must not be empty'):
            OTP(indicator='user123', config=otp_config, cache_prefix='')


class TestOTPConfiguration:
    """Test OTP configuration validation."""
    
    def test_config_missing_timeout(self, cipher):
        """Test config without TIMEOUT."""
        config = {
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(KeyError, match='Timeout must be defined'):
            OTP(indicator='user', config=config)
    
    def test_config_invalid_timeout_type(self, cipher):
        """Test config with invalid TIMEOUT type."""
        config = {
            'TIMEOUT': 120,
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(TypeError, match='TIMEOUT must be a timedelta'):
            OTP(indicator='user', config=config)
    
    def test_config_timeout_too_short(self, cipher):
        """Test config with TIMEOUT less than 1 second."""
        config = {
            'TIMEOUT': timedelta(milliseconds=500),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(ValueError, match='TIMEOUT must be at least 1 second'):
            OTP(indicator='user', config=config)
    
    def test_config_missing_attempts(self, cipher):
        """Test config without ATTEMPTS."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(KeyError, match='ATTEMPTS must be defined'):
            OTP(indicator='user', config=config)
    
    def test_config_invalid_attempts_type(self, cipher):
        """Test config with invalid ATTEMPTS type."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': '3',
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(TypeError, match='ATTEMPTS must be an integer'):
            OTP(indicator='user', config=config)
    
    def test_config_invalid_attempts_value(self, cipher):
        """Test config with invalid ATTEMPTS value."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 0,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(ValueError, match='ATTEMPTS must be greater than 0'):
            OTP(indicator='user', config=config)
    
    def test_config_attempts_disabled(self, cipher):
        """Test config with ATTEMPTS disabled (-1)."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': -1,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        otp = OTP(indicator='user', config=config)
        assert otp._attempts == -1
    
    def test_config_missing_token_type(self, cipher):
        """Test config without TOKEN_TYPE."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(KeyError, match='TOKEN_TYPE must be defined'):
            OTP(indicator='user', config=config)
    
    def test_config_invalid_token_type_value(self, cipher):
        """Test config with invalid TOKEN_TYPE value."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'invalid',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(ValueError, match='TOKEN_TYPE must be one of'):
            OTP(indicator='user', config=config)
    
    def test_config_missing_token_length(self, cipher):
        """Test config without TOKEN_LENGTH."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(KeyError, match='TOKEN_LENGTH must be defined'):
            OTP(indicator='user', config=config)
    
    def test_config_invalid_token_length(self, cipher):
        """Test config with invalid TOKEN_LENGTH."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 0,
            'ENCRYPTOR': cipher,
        }
        with pytest.raises(ValueError, match='TOKEN_LENGTH must be greater than 0'):
            OTP(indicator='user', config=config)
    
    def test_config_missing_encryptor(self, cipher):
        """Test config without ENCRYPTOR."""
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
        }
        with pytest.raises(KeyError, match='ENCRYPTOR must be defined'):
            OTP(indicator='user', config=config)
    
    def test_config_encryptor_no_encrypt_method(self, cipher):
        """Test config with encryptor missing encrypt method."""
        encryptor = Mock(spec=[])
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': encryptor,
        }
        with pytest.raises(AttributeError, match='ENCRYPTOR must have encrypt method'):
            OTP(indicator='user', config=config)
    
    def test_config_encryptor_no_decrypt_method(self):
        """Test config with encryptor missing decrypt method."""
        encryptor = Mock()
        encryptor.encrypt = Mock()
        del encryptor.decrypt
        
        config = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': encryptor,
        }
        with pytest.raises(AttributeError, match='ENCRYPTOR must have decrypt method'):
            OTP(indicator='user', config=config)


class TestGenerateOTPToken:
    """Test OTP token generation."""
    
    def test_generate_int_token(self, otp_instance):
        """Test generating integer token."""
        token = otp_instance.generate_otp_token()
        
        assert len(token) == 4
        assert token.isdigit()
        assert re.match(r'^\d{4}$', token)
    
    def test_generate_str_token(self, otp_config_str):
        """Test generating string token."""
        otp = OTP(indicator='user', config=otp_config_str)
        token = otp.generate_otp_token()
        
        assert len(token) == 6
        assert token.isupper()
        assert token.isalpha()
        assert re.match(r'^[A-Z]{6}$', token)
    
    def test_generate_alphanumeric_token(self, otp_config_alphanumeric):
        """Test generating alphanumeric token."""
        otp = OTP(indicator='user', config=otp_config_alphanumeric)
        token = otp.generate_otp_token()
        
        assert len(token) == 8
        assert token.isupper() or any(c.isdigit() for c in token)
        assert re.match(r'^[A-Z0-9]{8}$', token)
    
    def test_generate_multiple_unique_tokens(self, otp_instance):
        """Test generating multiple tokens are different."""
        tokens = [otp_instance.generate_otp_token() for _ in range(10)]
        
        # Not all tokens should be the same (very unlikely with 4 digits)
        assert len(set(tokens)) > 1


class TestStartOTPSession:
    """Test starting OTP sessions."""
    
    def test_start_with_valid_token(self, otp_instance):
        """Test starting session with valid token."""
        result = otp_instance.start('1234')
        
        assert result is True
        assert cache.get(otp_instance.cache_key) is not None
    
    def test_start_with_encrypted_token(self, otp_instance):
        """Test starting session with encrypted token (default)."""
        result = otp_instance.start('1234', encrypted=True)
        
        assert result is True
        session = cache.get(otp_instance.cache_key)
        assert session is not None
        assert session['token'] != '1234'  # Should be encrypted
    
    def test_start_with_unencrypted_token(self, otp_instance):
        """Test starting session with unencrypted token."""
        result = otp_instance.start('1234', encrypted=False)
        
        assert result is True
        session = cache.get(otp_instance.cache_key)
        assert session is not None
        assert session['token'] == '1234'  # Should be raw
    
    def test_start_with_attempts_enabled(self, otp_instance):
        """Test starting session initializes attempts to 0."""
        otp_instance.start('1234')
        session = cache.get(otp_instance.cache_key)
        
        assert session['attempts'] == 0
    
    def test_start_with_attempts_disabled(self, otp_config_no_attempts):
        """Test starting session without attempts tracking."""
        otp = OTP(indicator='user', config=otp_config_no_attempts)
        otp.start('1234')
        session = cache.get(otp.cache_key)
        
        assert 'attempts' not in session
    
    def test_start_with_kwargs(self, otp_instance):
        """Test starting session with extra kwargs."""
        otp_instance.start('1234', user_id=123, email='test@example.com')
        session = cache.get(otp_instance.cache_key)
        
        assert session['user_id'] == 123
        assert session['email'] == 'test@example.com'
    
    def test_start_prevents_override_by_default(self, otp_instance):
        """Test starting session doesn't override existing session by default."""
        otp_instance.start('1234', user_id=1)
        result = otp_instance.start('5678', user_id=2)
        
        assert result is False
        session = cache.get(otp_instance.cache_key)
        assert session['user_id'] == 1  # Original session preserved
    
    def test_start_with_override_true(self, otp_instance):
        """Test starting session overrides existing session when override=True."""
        otp_instance.start('1234', user_id=1)
        result = otp_instance.start('5678', override=True, user_id=2)
        
        assert result is True
        session = cache.get(otp_instance.cache_key)
        assert session['user_id'] == 2  # New session
    
    def test_start_with_invalid_token(self, otp_instance):
        """Test starting session with invalid token raises error."""
        with pytest.raises(ValueError, match='Invalid OTP token'):
            otp_instance.start('ABCD')  # Letters not allowed for 'int' type
    
    def test_start_with_wrong_length_token(self, otp_instance):
        """Test starting session with wrong length token."""
        with pytest.raises(ValueError, match='Invalid OTP token'):
            otp_instance.start('12345')  # Should be 4 digits
    
    def test_start_with_invalid_encrypted_param(self, otp_instance):
        """Test starting session with invalid encrypted parameter."""
        with pytest.raises(TypeError, match='encrypted must be a boolean'):
            otp_instance.start('1234', encrypted='yes')
    
    def test_start_with_invalid_override_param(self, otp_instance):
        """Test starting session with invalid override parameter."""
        with pytest.raises(TypeError, match='Override must be a boolean'):
            otp_instance.start('1234', override='yes')


class TestCancelOTPSession:
    """Test canceling OTP sessions."""
    
    def test_cancel_existing_session(self, otp_instance):
        """Test canceling an existing session."""
        otp_instance.start('1234', user_id=123)
        deleted, data = otp_instance.cancel()
        
        assert deleted is True
        assert data is not None
        assert data['user_id'] == 123
        assert cache.get(otp_instance.cache_key) is None
    
    def test_cancel_non_existing_session(self, otp_instance):
        """Test canceling a non-existing session."""
        deleted, data = otp_instance.cancel()
        
        assert deleted is False
        assert data is None


class TestGetSessionData:
    """Test getting session data."""
    
    def test_get_existing_session_data(self, otp_instance):
        """Test getting data from existing session."""
        otp_instance.start('1234', user_id=123, email='test@example.com')
        data = otp_instance.get_session_data()
        
        assert data is not None
        assert data['user_id'] == 123
        assert data['email'] == 'test@example.com'
        assert 'token' in data
    
    def test_get_non_existing_session_data(self, otp_instance):
        """Test getting data from non-existing session."""
        data = otp_instance.get_session_data()
        
        assert data is None


class TestFinishOTPSession:
    """Test finishing/validating OTP sessions."""
    
    def test_finish_with_correct_token(self, otp_instance):
        """Test finishing with correct token."""
        otp_instance.start('1234', user_id=123)
        code, data = otp_instance.finish('1234')
        
        assert code == 1  # Success
        assert data is not None
        assert data['user_id'] == 123
        assert 'attempts' not in data  # Should be removed
        assert cache.get(otp_instance.cache_key) is None  # Session cleared
    
    def test_finish_with_incorrect_token(self, otp_instance, mock_redis):
        """Test finishing with incorrect token."""
        otp_instance.start('1234')
        code, data = otp_instance.finish('5678')
        
        assert code == 0  # Invalid token
        assert data is None
        session = cache.get(otp_instance.cache_key)
        assert session['attempts'] == 1  # Attempts incremented
    
    def test_finish_no_session(self, otp_instance):
        """Test finishing without active session."""
        code, data = otp_instance.finish('1234')
        
        assert code == -1  # No session
        assert data is None
    
    def test_finish_corrupted_session_no_token(self, otp_instance):
        """Test finishing with corrupted session (no token)."""
        cache.set(otp_instance.cache_key, {'user_id': 123})
        code, data = otp_instance.finish('1234')
        
        assert code == -2  # Corrupted session
        assert data is None
    
    def test_finish_decryption_failure(self, otp_instance):
        """Test finishing when decryption fails."""
        # Manually set invalid encrypted token
        cache.set(otp_instance.cache_key, {
            'token': 'invalid_encrypted_token',
            'attempts': 0,
            'encrypted': True
        })
        code, data = otp_instance.finish('1234')
        
        assert code == -3  # Decryption failed
        assert data is None
    
    def test_finish_lost_attempts_tracking(self, otp_instance):
        """Test finishing when attempts tracking is lost."""
        # Start without attempts (simulate corruption)
        cache.set(otp_instance.cache_key, {
            'token': otp_instance._encrypt_token('1234'),
            'encrypted': True
        })
        code, data = otp_instance.finish('1234')
        
        assert code == -4  # Lost track of attempts
        assert data is None
    
    def test_finish_max_attempts_reached(self, otp_instance, mock_redis):
        """Test finishing when max attempts is reached."""
        otp_instance.start('1234')
        
        # Make 3 failed attempts (max is 3)
        otp_instance.finish('0000')
        otp_instance.finish('0000')
        code, data = otp_instance.finish('0000')
        
        assert code == -5  # Max attempts exceeded
        assert data is None
        assert cache.get(otp_instance.cache_key) is None  # Session cleared
    
    def test_finish_with_unencrypted_token(self, otp_instance):
        """Test finishing with unencrypted token."""
        otp_instance.start('1234', encrypted=False)
        code, data = otp_instance.finish('1234')
        
        assert code == 1  # Success
        assert data is not None
    
    def test_finish_preserves_other_kwargs(self, otp_instance):
        """Test that finish preserves other kwargs after validation."""
        otp_instance.start('1234', user_id=123, email='test@example.com')
        code, data = otp_instance.finish('1234')
        
        assert code == 1
        assert data['user_id'] == 123
        assert data['email'] == 'test@example.com'
    
    def test_finish_increments_attempts_correctly(self, otp_instance, mock_redis):
        """Test that attempts are incremented correctly."""
        otp_instance.start('1234')
        
        # First failed attempt
        otp_instance.finish('0000')
        session = cache.get(otp_instance.cache_key)
        assert session['attempts'] == 1
        
        # Second failed attempt
        otp_instance.finish('0000')
        session = cache.get(otp_instance.cache_key)
        assert session['attempts'] == 2
    
    def test_finish_without_attempts_tracking(self, otp_config_no_attempts):
        """Test finishing when attempts tracking is disabled."""
        otp = OTP(indicator='user', config=otp_config_no_attempts)
        otp.start('1234')
        
        # Multiple failed attempts should not affect anything
        otp.finish('0000')
        otp.finish('0000')
        otp.finish('0000')
        
        # Should still be able to validate correct token
        code, data = otp.finish('1234')
        assert code == 1


class TestEncryptDecryptToken:
    """Test token encryption and decryption."""
    
    def test_encrypt_valid_token(self, otp_instance):
        """Test encrypting a valid token."""
        encrypted = otp_instance._encrypt_token('1234')
        
        assert encrypted != '1234'
        assert isinstance(encrypted, (str, bytes))
    
    def test_encrypt_invalid_token(self, otp_instance):
        """Test encrypting an invalid token raises error."""
        with pytest.raises(ValueError, match='Invalid OTP token'):
            otp_instance._encrypt_token('ABCD')
    
    def test_decrypt_valid_token(self, otp_instance):
        """Test decrypting a valid token."""
        encrypted = otp_instance._encrypt_token('1234')
        decrypted = otp_instance._decrypt_token(encrypted)
        
        assert decrypted == '1234'
    
    def test_decrypt_invalid_token(self, otp_instance):
        """Test decrypting an invalid token returns None."""
        decrypted = otp_instance._decrypt_token('invalid_token')
        
        assert decrypted is None
    
    def test_encrypt_decrypt_round_trip(self, otp_instance):
        """Test full encryption and decryption cycle."""
        original = '1234'
        encrypted = otp_instance._encrypt_token(original)
        decrypted = otp_instance._decrypt_token(encrypted)
        
        assert decrypted == original


class TestTokenRegex:
    """Test token regex generation."""
    
    def test_int_token_regex(self, otp_instance):
        """Test integer token regex."""
        assert otp_instance._token_regex.match('1234')
        assert not otp_instance._token_regex.match('ABCD')
        assert not otp_instance._token_regex.match('12345')
        assert not otp_instance._token_regex.match('123')
        assert not otp_instance._token_regex.match('12A4')
    
    def test_str_token_regex(self, otp_config_str):
        """Test string token regex."""
        otp = OTP(indicator='user', config=otp_config_str)
        
        assert otp._token_regex.match('ABCDEF')
        assert not otp._token_regex.match('123456')
        assert not otp._token_regex.match('ABCDEFG')
        assert not otp._token_regex.match('ABCDE')
        assert not otp._token_regex.match('abcdef')
        assert not otp._token_regex.match('ABC123')
    
    def test_alphanumeric_token_regex(self, otp_config_alphanumeric):
        """Test alphanumeric token regex."""
        otp = OTP(indicator='user', config=otp_config_alphanumeric)
        
        assert otp._token_regex.match('ABCD1234')
        assert otp._token_regex.match('12345678')
        assert otp._token_regex.match('ABCDEFGH')
        assert not otp._token_regex.match('ABCD123')
        assert not otp._token_regex.match('abcd1234')
        assert not otp._token_regex.match('ABCD123!')


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_multiple_users_different_sessions(self, otp_config):
        """Test multiple users can have independent sessions."""
        otp1 = OTP(indicator='user1', config=otp_config)
        otp2 = OTP(indicator='user2', config=otp_config)
        
        otp1.start('1234', data='user1_data')
        otp2.start('5678', data='user2_data')
        
        code1, data1 = otp1.finish('1234')
        code2, data2 = otp2.finish('5678')
        
        assert code1 == 1
        assert data1['data'] == 'user1_data'
        assert code2 == 1
        assert data2['data'] == 'user2_data'
    
    def test_cache_timeout(self, otp_instance):
        """Test that cache expires after timeout."""
        # This is difficult to test without actually waiting
        # Just verify the timeout is set correctly
        otp_instance.start('1234')
        # Cache timeout would be 120 seconds (2 minutes) as per config
        # In a real test, you might use freezegun or similar to test time-based behavior
    
    def test_redis_connection_failure(self, otp_instance):
        """Test handling Redis connection failure."""
        with patch('authentication.OTP.otp.get_redis_connection', side_effect=Exception('Redis error')):
            otp_instance.start('1234')
            code, data = otp_instance.finish('0000')
            
            # Should return error code for failed cache update
            assert code == -4
    
    def test_finish_with_non_matching_regex_token(self, otp_instance):
        """Test finishing with token that doesn't match regex still processes."""
        otp_instance.start('1234')
        # Try with token that doesn't match regex (should log warning but continue)
        code, data = otp_instance.finish('ABCD')
        
        # Should still process (return invalid token code)
        assert code in [0, -3]  # Invalid token or decryption failed
    
    def test_start_with_zero_attempts_in_session(self, otp_instance):
        """Test that attempts start at 0."""
        otp_instance.start('1234')
        session = cache.get(otp_instance.cache_key)
        
        assert session['attempts'] == 0
    
    def test_different_encryptors(self, cipher):
        """Test that different encryptors can't decrypt each other's tokens."""
        cipher2 = Fernet(Fernet.generate_key())
        
        config1 = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher,
        }
        
        config2 = {
            'TIMEOUT': timedelta(minutes=2),
            'ATTEMPTS': 3,
            'TOKEN_TYPE': 'int',
            'TOKEN_LENGTH': 4,
            'ENCRYPTOR': cipher2,
        }
        
        otp1 = OTP(indicator='user', config=config1)
        otp1.start('1234')
        
        # Try to decrypt with different encryptor
        otp2 = OTP(indicator='user', config=config2)
        code, data = otp2.finish('1234')
        
        # Should fail to decrypt
        assert code == -3


class TestIntegrationScenarios:
    """Test complete integration scenarios."""
    
    def test_complete_otp_flow_success(self, otp_instance):
        """Test complete successful OTP flow."""
        # Generate token
        token = otp_instance.generate_otp_token()
        
        # Start session
        result = otp_instance.start(token, user_id=123, email='test@example.com')
        assert result is True
        
        # Get session data
        session = otp_instance.get_session_data()
        assert session is not None
        assert session['user_id'] == 123
        
        # Validate correct token
        code, data = otp_instance.finish(token)
        assert code == 1
        assert data['user_id'] == 123
        assert data['email'] == 'test@example.com'
        
        # Session should be cleared
        assert otp_instance.get_session_data() is None
    
    def test_complete_otp_flow_with_retry(self, otp_instance, mock_redis):
        """Test OTP flow with one failed attempt then success."""
        token = otp_instance.generate_otp_token()
        otp_instance.start(token, user_id=123)
        
        # First attempt - wrong token
        code, data = otp_instance.finish('0000')
        assert code == 0
        assert data is None
        
        # Second attempt - correct token
        code, data = otp_instance.finish(token)
        assert code == 1
        assert data['user_id'] == 123
    
    def test_complete_otp_flow_max_attempts_then_new_session(self, otp_instance, mock_redis):
        """Test OTP flow with max attempts, then starting new session."""
        # First session - exhaust attempts
        otp_instance.start('1234', user_id=123)
        otp_instance.finish('0000')
        otp_instance.finish('0000')
        code, data = otp_instance.finish('0000')
        assert code == -5  # Max attempts
        
        # Start new session
        result = otp_instance.start('5678', override=True, user_id=456)
        assert result is True
        
        # Should work with new session
        code, data = otp_instance.finish('5678')
        assert code == 1
        assert data['user_id'] == 456
    
    def test_otp_flow_cancel_midway(self, otp_instance):
        """Test canceling OTP session midway."""
        token = otp_instance.generate_otp_token()
        otp_instance.start(token, user_id=123)
        
        # Cancel session
        deleted, data = otp_instance.cancel()
        assert deleted is True
        assert data['user_id'] == 123
        
        # Try to finish - should fail
        code, result_data = otp_instance.finish(token)
        assert code == -1  # No session
    
    def test_otp_flow_with_unencrypted_storage(self, otp_instance):
        """Test complete OTP flow with unencrypted storage."""
        token = otp_instance.generate_otp_token()
        otp_instance.start(token, encrypted=False, user_id=123)
        
        # Verify token is stored in plain text
        session = cache.get(otp_instance.cache_key)
        assert session['token'] == token
        
        # Should still validate correctly
        code, data = otp_instance.finish(token)
        assert code == 1
        assert data['user_id'] == 123
    
    def test_otp_flow_no_attempts_limit(self, otp_config_no_attempts):
        """Test OTP flow with no attempts limit."""
        otp = OTP(indicator='user', config=otp_config_no_attempts)
        
        token = otp.generate_otp_token()
        otp.start(token, user_id=123)
        
        # Make many failed attempts
        for _ in range(10):
            code, data = otp.finish('0000')
            assert code == 0  # Should keep returning invalid
        
        # Should still be able to validate correct token
        code, data = otp.finish(token)
        assert code == 1
        assert data['user_id'] == 123


class TestConcurrencyAndRaceConditions:
    """Test concurrent access scenarios."""
    
    def test_concurrent_start_without_override(self, otp_config):
        """Test concurrent start attempts without override."""
        otp = OTP(indicator='user', config=otp_config)
        
        # First start
        result1 = otp.start('1234', data='first')
        assert result1 is True
        
        # Second start without override should fail
        result2 = otp.start('5678', data='second')
        assert result2 is False
        
        # Original session should be preserved
        session = cache.get(otp.cache_key)
        assert session['data'] == 'first'
    
    def test_concurrent_finish_attempts(self, otp_instance, mock_redis):
        """Test concurrent finish attempts."""
        otp_instance.start('1234')
        
        # Simulate two concurrent wrong attempts
        code1, _ = otp_instance.finish('0000')
        code2, _ = otp_instance.finish('0000')
        
        assert code1 == 0
        assert code2 == 0
        
        # Attempts should be incremented
        session = cache.get(otp_instance.cache_key)
        assert session['attempts'] == 2


class TestLoggingAndErrorMessages:
    """Test that appropriate logging occurs."""
    
    def test_logging_on_override_prevention(self, otp_instance, caplog):
        """Test logging when override is prevented."""
        import logging
        caplog.set_level(logging.WARNING)
        
        otp_instance.start('1234')
        otp_instance.start('5678')  # Should log warning
        
        assert 'Prevented overriding' in caplog.text
    
    def test_logging_on_no_session(self, otp_instance, caplog):
        """Test logging when session not found."""
        import logging
        caplog.set_level(logging.WARNING)
        
        otp_instance.cancel()
        
        assert 'no active OTP session' in caplog.text
    
    def test_logging_on_finish_failure(self, otp_instance, caplog):
        """Test logging on finish with no session."""
        import logging
        caplog.set_level(logging.ERROR)
        
        otp_instance.finish('1234')
        
        assert 'OTP session was not found' in caplog.text
    
    def test_logging_on_invalid_token_finish(self, otp_instance, caplog, mock_redis):
        """Test logging on finish with invalid token."""
        import logging
        caplog.set_level(logging.ERROR)
        
        otp_instance.start('1234')
        otp_instance.finish('5678')
        
        assert 'Token is invalid' in caplog.text
    
    def test_logging_on_max_attempts(self, otp_instance, caplog, mock_redis):
        """Test logging when max attempts reached."""
        import logging
        caplog.set_level(logging.WARNING)
        
        otp_instance.start('1234')
        otp_instance.finish('0000')
        otp_instance.finish('0000')
        otp_instance.finish('0000')
        
        assert 'Too many attempts' in caplog.text
