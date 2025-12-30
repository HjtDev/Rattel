from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from typing import Dict, Any, AnyStr, Tuple, Optional
from secrets import randbelow
from random import choice
from string import ascii_uppercase, digits
from django.core.exceptions import ImproperlyConfigured
from django_redis import get_redis_connection
from copy import deepcopy
import re, logging


logger = logging.getLogger(__name__)

class OTP:
    """
    Handle OTP authentication.
    Features:
        1. Generate secure OTP tokens.
        2. Encrypt OTP tokens.
        3. Start OTP authentication sessions.
        4. Validate an OTP token with active sessions
        5. Cancel ongoing OTP sessions.
        6. Create OTP token regex.
    """
    
    def __init__(self, indicator: str, config: Dict[str, Any] = settings.OTP_SETTING, cache_prefix: str = 'OTP'):
        """
        Initialize OTP config and setup cache key and token regex.
        
        Args:
            indicator: Unique indicator for OTP session
            config: OTP configuration settings - Defaults to settings.OTP_SETTING
            cache_prefix: Prefix for cache key. Defaults to 'OTP'
        """
        
        # Validating the indicator
        if not isinstance(indicator, str):
            raise TypeError('Indicator must be a string.')
        if not indicator or not indicator.strip():
            raise ValueError('Indicator must not be empty or contain only whitespace.')
        
        self.indicator = indicator
        
        # Validating cache_prefix
        if not isinstance(cache_prefix, str):
            raise TypeError('Cache prefix must be a string.')
        if not cache_prefix or not cache_prefix.strip():
            raise ValueError('Cache prefix must not be empty or contain only whitespace.')
        
        self._cache_prefix = cache_prefix
        self.cache_key = f'{cache_prefix}-{self.indicator}'  # Creating a cache_key based on _cache_prefix and indicator
        
        # Extracting settings from provided configuration
        self._timeout, self._attempts, self._token_type, self._token_length, self._encryptor = self._get_settings(config)
        
        self._token_regex = self._get_token_regex()  # Compiling a token regex based on the settings
    
    def generate_otp_token(self) -> str:
        """
        Generates OTP token with the provided config.
        
        Returns:
            str: OTP token
        """
        
        if self._token_type == 'int':  # Digit only token
            token = ''.join(str(randbelow(10)) for _ in range(self._token_length))
        elif self._token_type == 'str':  # Uppercase letter only token
            token = ''.join(choice(ascii_uppercase) for _ in range(self._token_length))
        else:  # Uppercase + Digit token(alphanumeric)
            alphanumeric = ascii_uppercase + digits
            token = ''.join(choice(alphanumeric) for _ in range(self._token_length))
        
        if self._token_regex.match(token):  # Making sure the token is valid before returning it
            return token
        
        raise RuntimeError('Failed to generate a valid OTP token')  # Either the token regex or the generator is broken
    
    def start(self, token: str, encrypted: bool = True, override: bool = False, **kwargs) -> bool:
        """
        Starts an OTP session with the given token.
        
        Args:
            token: Valid OTP token.
            encrypted: Default is True. If set to false the token will be stored in raw format without any encryption.
            override: Default is False. If set to True and there was an active OTP session with the same indicator it would override it.
            **kwargs: Optional - Any extra information or metadata that you need to be stored with token.
            
        Returns:
            bool: True if the OTP session was started successfully. False otherwise.

        """
        
        # Validating token with _token_regex
        if not self._token_regex.match(token):
            raise ValueError('Invalid OTP token.')
        
        # Validating encrypted argument
        if not isinstance(encrypted, bool):
            raise TypeError('encrypted must be a boolean.')
        
        # Validating override argument
        if not isinstance(override, bool):
            raise TypeError('Override must be a boolean.')
        
        # Checking for active OTP session with the same indicator
        if cache.get(self.cache_key) and not override:  # override=False => Preventing the override
            logger.warning(f'There is an active OTP token {self.cache_key}. Prevented overriding.')
            return False
        
        # Stores the raw token by default
        final_token = token
        
        if encrypted:  # Encrypting the raw token
            final_token = self._encrypt_token(token)
        
        # (raw / encrypted) token + all the extra keyword arguments to save with the token
        kwargs['token'] = final_token
        
        if self._attempts != -1:
            kwargs['attempts'] = 0  # Initialize attempts to 0
        
        # Storing token and extra info in cache with timeout
        cache.set(self.cache_key, kwargs, timeout=self._timeout)
        
        # OTP session started
        return True
    
    def cancel(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Tries to cancel/delete the active OTP session if it exists
        
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Whether the OTP was cancelled or not + If OTP session was found successfully it would return its data alongside it
        """
        
        # Tries to find an active OTP session in cache
        otp = cache.get(self.cache_key)
        
        if otp is None:  # OTP session not found.
            logger.warning(f'There is no active OTP session with the indicator {self.indicator}')
            return False, None
        
        return cache.delete(self.cache_key), otp  # deleted_cache: bool, data: dict
    
    def get_session_data(self) -> Optional[Dict[str, Any]]:
        """
        Extracts OTP session data from the cache.
        
        Returns:
            Optional[Dict[str, Any]]: OTP session data
        """
        
        data = cache.get(self.cache_key)
        
        if data is None:
            logger.warning(f'There is no active OTP session with the indicator {self.indicator}')
            return None
        
        return data
    
    def finish(self, token: str) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Validates the OTP token if there is an active OTP session.
        It decrypts the stored OTP token and compares it with the one provided if matched it returns 1, kwargs. error_code, None otherwise.
        
        Code List:
            1: Successful -> OTP session is cleared.
            0: Given token didn't match the decrypted token -> Number of attempts increased.
            -1: No OTP session was found.
            -2: OTP session is corrupted.
            -3: Failed to decrypt OTP token.
            -4: Lost track of attempts.
            -5: Passed maximum attempts -> OTP session was expired.
            
        Args:
            token: OTP token to validate
            
        Returns:
            Tuple[int, Optional[Dict[str, Any]]]: code, OTP session data
        """
        
        # First checks the token with token_regex, but if it didn't match we won't prevent it so we can also handle OTP tokens that was stored manually
        if not self._token_regex.match(token):
            logger.warning('The OTP token does not match OTP_SETTING.')
        
        otp = self.get_session_data()  # Restores token and kwargs
        
        # No OTP session
        if otp is None:
            logger.error('The OTP session was not found.')
            return -1, None
        
        otp_token = otp.get('token')  # Encrypted OTP token
        
        # Checks if token exists
        if otp_token is None:
            logger.error('The OTP session is corrupted.')
            return -2, None
        
        # Creates a copy from OTP data to keep the OTP data intact
        kwargs = deepcopy(otp)
        kwargs.pop('token')
        
        # Tries to decrypt and validates the decrypted token
        decrypted_token = self._decrypt_token(otp_token)
        if decrypted_token is None:
            logger.error('Decryption failed.')
            return -3, None
        
        # Validating attempts
        attempts = kwargs.get('attempts', None)
        
        # If we don't have the number of attempts, but attempts are enabled, or attempts is not an integer
        if (attempts is None and self._attempts != -1) or (attempts is not None and not isinstance(attempts, int)):
            logger.error('Lost track of attempts.')
            return -4, None
        
        # Given token doesn't match the decrypted token
        if decrypted_token != token:
            logger.error('Token is invalid.')
            
            # If we have the number of attempts we increase it and compare it to maximum_attempts
            if attempts is not None:
                attempts += 1
                if attempts >= self._attempts:
                    logger.warning('Too many attempts. Current OTP session is invalidated. Please start another OTP session.')
                    
                    # Clearing OTP session
                    self.cancel()
                    return -5, None
                else:
                    otp['attempts'] = attempts
                    
                    # Update cache with new attempt count
                    try:
                        redis_conn = get_redis_connection('default')
                        remaining_time = redis_conn.ttl(self.cache_key)
                        cache.set(self.cache_key, otp, timeout=remaining_time)
                    except Exception as e:
                        logger.error(f'Failed to update attempts in cache: {e}')
                        return -4, None
            
            return 0, None
        
        kwargs.pop('attempts', None)
        
        self.cancel()
        return 1, kwargs
    
    def _get_settings(self, config: Dict[str, Any]):
        """
        Validates and extracts OTP configuration
        
        Args:
            config: OTP configuration. Must contain TIMEOUT, ATTEMPTS, TOKEN_TYPE, TOKEN_LENGTH, ENCRYPTOR.
            
        Returns:
            A validated tuple ==> (TIMEOUT, ATTEMPTS, TOKEN_TYPE, TOKEN_LENGTH, ENCRYPTOR)
        """
        
        # Validating config
        if not isinstance(config, dict):
            raise ImproperlyConfigured('Either pass OTP settings through __init__ or provide them in settings.py as OTP_SETTING.')
        
        
        # Validating TIMEOUT
        timeout = config.get('TIMEOUT', None)
        if timeout is None:
            raise KeyError('Timeout must be defined in OTP_SETTING.')
        
        # Checking if timeout is an instance of timedelta
        if not isinstance(timeout, timedelta):
            raise TypeError('TIMEOUT must be a timedelta.')
        
        # Converting timedelta time to seconds
        timeout = timeout.total_seconds()
        
        # timeout can't be less than 1 second
        if timeout < 1:
            raise ValueError('TIMEOUT must be at least 1 second.')
        
        attempts = config.get('ATTEMPTS', None)
        if attempts is None:
            raise KeyError('ATTEMPTS must be defined in OTP_SETTING.')
        if not isinstance(attempts, int):
            raise TypeError('ATTEMPTS must be an integer.')
        if attempts < 1 and attempts != -1:
            raise ValueError('ATTEMPTS must be greater than 0, or equal to -1 to be disabled.')
        
        # Validating token_type
        token_type = config.get('TOKEN_TYPE', None)
        if token_type is None:
            raise KeyError('TOKEN_TYPE must be defined in OTP_SETTING.')
        if not isinstance(token_type, str):
            raise TypeError('TOKEN_TYPE must be a string.')
        
        # token_type value must be int, str or alphanumeric. For OTP token generator
        if token_type not in ('int', 'str', 'alphanumeric'):
            raise ValueError('TOKEN_TYPE must be one of "int", "str" or "alphanumeric".')
        
        
        # Validating token_length
        token_length = config.get('TOKEN_LENGTH', None)
        if token_length is None:
            raise KeyError('TOKEN_LENGTH must be defined in OTP_SETTING.')
        if not isinstance(token_length, int) or token_length <= 0:
            raise ValueError('TOKEN_LENGTH must be greater than 0.')
        
        # Validating encryptor
        encryptor = config.get('ENCRYPTOR', None)
        if encryptor is None:
            raise KeyError('ENCRYPTOR must be defined in OTP_SETTING.')
        
        # Checking if encryptor has callable encrypt and decrypt methods
        if not hasattr(encryptor, 'encrypt') or not callable(getattr(encryptor, 'encrypt')):
            raise AttributeError('ENCRYPTOR must have encrypt method.')
        if not hasattr(encryptor, 'decrypt') or not callable(getattr(encryptor, 'decrypt')):
            raise AttributeError('ENCRYPTOR must have decrypt method.')
        
        # Returning the config in one pack
        return timeout, attempts, token_type, token_length, encryptor
    
    def _get_token_regex(self) -> re.Pattern[AnyStr]:
        """
        Generates an OTP token regex based on the OTP configuration.
        
        Returns:
            re.Pattern[AnyStr]: OTP token regex.
        """
        
        if self._token_type == 'int':
            # Only digits, exact length
            return re.compile(rf'^\d{{{self._token_length}}}$')
        elif self._token_type == 'str':
            # Only uppercase letters, exact length
            return re.compile(rf'^[A-Z]{{{self._token_length}}}$')
        elif self._token_type == 'alphanumeric':
            # Uppercase letters or digits, exact length
            return re.compile(rf'^[A-Z0-9]{{{self._token_length}}}$')
        else:
            raise ValueError("Invalid type. Must be 'int', 'str', or 'alphanumeric'.")
    
    def _encrypt_token(self, token: str) -> str:
        """
        Encrypts the given token with the self._encryptor.
        
        Args:
            token: Valid OTP token to encrypt.
            
        Returns:
            str: Encrypted token.
        """
        
        # Checks if the token is valid
        if not self._token_regex.match(token):
            raise ValueError('Invalid OTP token.')
        
        # Converting the token to Bytes before encryption. Returns the encrypted token.
        return self._encryptor.encrypt(token.encode())
    
    def _decrypt_token(self, token: str | bytes) -> Optional[str]:
        """
        Tries to decrypt the given token with the self._encryptor.
        If the decrypted token didn't match the OTP configuration a warning is logged, but you still get the token.
        
        Args:
            token: An encrypted OTP token. Must be encrypted with same encryptor.
            
        Returns:
            Optional[str]: Decrypted token if decryption was successful. None if decryption failed.
        """
        
        try:
            if isinstance(token, str):
                decrypted_token = self._encryptor.decrypt(token).decode()
            elif isinstance(token, bytes):
                decrypted_token = self._encryptor.decrypt(token.decode()).decode()
            else:
                raise TypeError('Token must be an instance of string or bytes to be decrypted.')
        except Exception as e:
            logger.error(f'Failed to decrypt the token using decryptor: {e}. Be sure that the token is encrypted with the same encryptor.')
            return None
        
        if not self._token_regex.match(decrypted_token):
            logger.warning(f'Token does not match OTP_SETTING. Please use OTP.start to start OTP sessions.')
        
        return decrypted_token
