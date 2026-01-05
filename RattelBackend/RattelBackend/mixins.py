from urllib.parse import urlparse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpRequest
from rest_framework import status
from rest_framework.response import Response
from typing import Any, AnyStr, List, Tuple, Dict, Iterable
import re, os


class ResponseBuilderMixin:
    """Mixin to simplify building REST API responses."""
    
    __slots__ = ()
    
    @staticmethod
    def build_response(response_status: int = status.HTTP_200_OK, **kwargs) -> Response:
        """
        Build a REST framework Response with the given status and data.
        
        Args:
            response_status: HTTP status code (default: 200)
            **kwargs: Data to include in response body
            
        Returns:
            Response object with data and status
        """
        if response_status == status.HTTP_204_NO_CONTENT:
            return Response(status=response_status)
        return Response(data=kwargs, status=response_status)


# noinspection RegExpUnnecessaryNonCapturingGroup,RegExpRedundantEscape
class GetDataMixin:
    """
    Mixin to extract and validate request data with flexible validation rules.
    
    Usage:
        success, result = self.get_data(request, 'username', ('email', self.validate_email))
        
        If success is True, result is a dict with extracted values.
        If success is False, result is a list of error messages.
    """
    
    __slots__ = ()
    
    # Compiled regex patterns for performance
    EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    USERNAME_REGEX = re.compile(r'^[a-zA-Z][a-zA-Z0-9_.]{2,29}$')
    PHONE_REGEX = re.compile(r'^09\d{9}$')
    PERSIAN_NAME_REGEX = re.compile(r'^[\u0600-\u06FF ]{1,60}$')
    ENGLISH_NAME_REGEX = re.compile(r'^[A-Za-z ]{1,60}$')
    NATIONAL_CODE_REGEX = re.compile(r'^[0-9]{10}$')
    FILTER_REGEX = re.compile(
        r'^'
        r'(?:'
        r'[a-zA-Z0-9_]+:'
        r'[\w\u0600-\u06FF\s\-.,!?:\'"()]+(?:,[\w\u0600-\u06FF\s\-.,!?:\'"()]+)*'
        r')'
        r'(?:;'
        r'[a-zA-Z0-9_]+:'
        r'[\w\u0600-\u06FF\s\-.,!?:\'"()]+(?:,[\w\u0600-\u06FF\s\-.,!?:\'"()]+)*'
        r')*'
        r'$',
        re.UNICODE
    )
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bSELECT\b.*\bFROM\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bUPDATE\b.*\bSET\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(\bDROP\b.*\b(TABLE|DATABASE)\b)',
        r'(\bEXEC\b|\bEXECUTE\b)',
        r'(;.*(-{2}|\/\*))',  # SQL comments
        r'(\bOR\b.*=.*)',
        r'(\bAND\b.*=.*)',
        r"('.*--)",
        r'(1=1|1\s*=\s*1)',
    ]
    
    # Django ORM lookup patterns
    DJANGO_ORM_PATTERNS = [
        r'__icontains',
        r'__contains',
        r'__iexact',
        r'__exact',
        r'__gt',
        r'__gte',
        r'__lt',
        r'__lte',
        r'__in',
        r'__startswith',
        r'__istartswith',
        r'__endswith',
        r'__iendswith',
        r'__range',
        r'__isnull',
        r'__regex',
        r'__iregex',
    ]
    
    # Dangerous characters and patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # XSS
        r'on\w+\s*=',  # Event handlers
        r'\$\{.*\}',  # Template injection
        r'\{\{.*\}\}',  # Template injection
        r'\.\./',  # Path traversal
        r'\.\.\%2[fF]',  # URL encoded path traversal
    ]
    
    # Redis key dangerous patterns
    REDIS_KEY_PATTERNS = [
        r'\s',  # No whitespace allowed
        r'[\r\n]',  # No newlines
        r'\*',  # Wildcard patterns
        r'\?',  # Wildcard patterns
        r'\[',  # Pattern matching
        r'\]',  # Pattern matching
        r'\.\.',  # Path traversal
        r'//',  # Double slashes
        r'^\./',  # Relative paths
    ]
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format.
        Must start with letter, 3-30 chars, alphanumeric plus underscore/dot.
        """
        if not isinstance(username, str):
            return False
        return bool(GetDataMixin.USERNAME_REGEX.match(username))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format using regex."""
        if not isinstance(email, str):
            return False
        return bool(GetDataMixin.EMAIL_REGEX.match(email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone format using regex."""
        if not isinstance(phone, str):
            return False
        return bool(GetDataMixin.PHONE_REGEX.match(phone))
    
    @staticmethod
    def validate_password(password: str, password2: str = None) -> tuple[bool, list[str]]:
        """
        Validate password strength and optionally match confirmation.
        
        Args:
            password: Password to validate
            password2: Optional confirmation password
            
        Returns:
            (is_valid, error_messages)
        """
        if password2 is not None and password != password2:
            return False, ['Passwords don\'t match']
        
        try:
            validate_password(password)
            return True, []
        except ValidationError as e:
            return False, e.messages
        
    @staticmethod
    def validate_string(string: AnyStr):
        """
        Validates a string:
            1. Should be an instance of str
            2. Can not be empty
            3. Can not only contain whitespace
            
        Args:
            string: String to validate
            
        Returns:
            bool: True if string is valid, False otherwise
        """
        return True if string and isinstance(string, str) and string.strip() else False
    
    @classmethod
    def validate_string_secure(
            cls,
            string: AnyStr,
            max_length: int = 1000,
            sql: bool = False,
            lookup: bool = False,
            injection: bool = False,
            redis: bool = False
    ) -> bool:
        """
        Validates a string with configurable security checks:
            1. Basic validation (non-empty, proper type, not only whitespace)
            2. Length validation
            3. SQL injection patterns (optional)
            4. Django ORM lookup patterns (optional)
            5. XSS and other injection patterns (optional)
            6. Redis key validation (optional)
            
        Args:
            string: String to validate
            max_length: Maximum allowed length (default: 1000)
            sql: Enable SQL injection validation (default: False)
            lookup: Enable Django ORM lookup validation (default: False)
            injection: Enable XSS/template injection validation (default: False)
            redis: Enable Redis key validation (default: False)
            
        Returns:
            bool: True if string is valid and safe, False otherwise
        """
        
        # Empty value is safe
        if not isinstance(string, str):
            return True
        
        # Length check
        if len(string) > max_length:
            return False
        
        # Convert to uppercase for case-insensitive pattern matching
        string_upper = string.upper()
        
        # Check SQL injection patterns
        if sql:
            for pattern in cls.SQL_PATTERNS:
                if re.search(pattern, string_upper, re.IGNORECASE):
                    return False
        
        # Check Django ORM lookup patterns
        if lookup:
            for pattern in cls.DJANGO_ORM_PATTERNS:
                if re.search(pattern, string, re.IGNORECASE):
                    return False
        
        # Check dangerous patterns (XSS, template injection, path traversal)
        if injection:
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, string, re.IGNORECASE):
                    return False
        
        # Check Redis key patterns
        if redis:
            if not cls._validate_redis_key(string):
                return False
        
        return True
    
    @classmethod
    def _validate_redis_key(cls, key: str) -> bool:
        """
        Internal method to validate Redis keys.
        
        Args:
            key: Redis key to validate
            
        Returns:
            bool: True if key is valid for Redis
        """
        # Check dangerous patterns
        for pattern in cls.REDIS_KEY_PATTERNS:
            if re.search(pattern, key):
                return False
        
        # Redis keys should not be too long (recommended max: 512 bytes)
        if len(key.encode('utf-8')) > 512:
            return False
        
        return True
    
    @classmethod
    def validate_redis_key(cls, key: AnyStr, prefix: str = None) -> bool:
        """
        Validates a Redis key with strict rules:
            1. Basic validation
            2. No whitespace or newlines
            3. No wildcard characters (*, ?, [, ])
            4. No path traversal patterns
            5. Maximum 512 bytes (Redis recommendation)
            6. Optional prefix validation
            
        Args:
            key: Redis key to validate
            prefix: Optional required prefix for the key
            
        Returns:
            bool: True if key is valid for Redis, False otherwise
        """
        # Basic validation
        if not cls.validate_string(key):
            return False
        
        # Check if prefix is required and present
        if prefix and not key.startswith(prefix):
            return False
        
        # Validate Redis key patterns
        return cls._validate_redis_key(key)
    
    @staticmethod
    def is_id(value: Any) -> bool:
        """
        Check if value is a valid positive ID.
        Accepts integers or numeric strings.
        """
        if isinstance(value, int):
            return value > 0
        if isinstance(value, str):
            return value.isdigit() and int(value) > 0
        return False
    
    @staticmethod
    def convert_data_to_bool(data: Any) -> bool:
        """
        Convert various data types to boolean.
        Recognizes: 'true', 'yes', 'y', '1', or int 1 as True.
        """
        if isinstance(data, int):
            return data == 1
        if isinstance(data, str):
            normalized = data.strip().lower()
            return normalized in {'true', 'yes', 'y', '1'}
        if isinstance(data, bool):
            return data
        return False
    
    @staticmethod
    def is_url(url: str) -> bool:
        """
        Checks if url is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if url is valid, False otherwise
        """
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    
    @staticmethod
    def username_type(username: AnyStr) -> str | None:
        """
        Determine the type of username.
        
        Args:
            username: Username value to check its type
            
        Returns:
            str: Type of username -> username/phone/None(Could not match it with anything)
        """
        if GetDataMixin.validate_phone(username):
            return 'phone'
        elif GetDataMixin.validate_username(username):
            return 'username'
        else:
            return None
        
        
    @staticmethod
    def validate_name(name: str) -> bool:
        """
        Validates a person's name.

        Rules:
        - Must not be empty or whitespace
        - Maximum length: 60 characters
        - Must contain only Persian OR only English letters
        - No digits or special characters
        """
        
        if not isinstance(name, str):
            return False

        name = name.strip()

        if not name:
            return False
        
        is_persian = GetDataMixin.PERSIAN_NAME_REGEX.fullmatch(name) is not None
        is_english = GetDataMixin.ENGLISH_NAME_REGEX.fullmatch(name) is not None
        
        return is_persian ^ is_english  # It can only be Persian or English
    
    @staticmethod
    def get_data(request, *args) -> tuple[bool, dict[str, Any] | list[str]]:
        """
        Extract and validate fields from request data.
        
        Args:
            request: Django request object
            *args: Field specifications. Each can be:
                - str: Field name (required, no validation)
                - tuple[str, Callable]: (field_name, validator_function)
                
        Validator function should return:
            - True: validation passed
            - False: validation failed (generic error)
            - str: validation failed with custom error message
            
        Returns:
            (success, result) where:
                - If success=True: result is dict of {field_name: value}
                - If success=False: result is list of error messages
                
        Example:
            success, result = self.get_data(
                request,
                'username',  # Required field, no validation
                ('email', self.validate_email),  # Required with validation
                ('id', self.is_id)  # Required, must be valid ID
            )
        """
        # Get data source based on request method
        data = request.query_params if request.method == 'GET' else request.data
        
        errors = []
        fields = {}
        
        for arg in args:
            # Handle string argument (required field, no validation)
            if isinstance(arg, str):
                field_name = arg
                if field_name not in data:
                    errors.append(f'{field_name} is required')
                    continue
                fields[field_name] = data[field_name]
            
            # Handle tuple argument (field with validator)
            elif isinstance(arg, tuple):
                if len(arg) != 2 or not callable(arg[1]):
                    raise TypeError(
                        f'Tuple arguments must be (field_name, validator). Got: {arg}'
                    )
                
                field_name, validator = arg
                
                # Check if field exists
                if field_name not in data:
                    errors.append(f'{field_name} is required')
                    continue
                
                value = data[field_name]
                
                # Run validator
                try:
                    validation_result = validator(value)
                except Exception as e:
                    errors.append(f'{field_name} validation error: {str(e)}')
                    continue
                
                # Handle validation result
                if isinstance(validation_result, str):
                    # Custom error message from validator
                    errors.append(validation_result)
                elif validation_result is True:
                    # Validation passed
                    fields[field_name] = value
                else:
                    # Validation failed (False or other falsy value)
                    errors.append(f'{field_name} is invalid')
            
            else:
                raise TypeError(
                    f'Arguments must be str or tuple[str, Callable]. Got: {type(arg)}'
                )
        
        # Return results
        if errors:
            return False, errors
        return True, fields

    @staticmethod
    def get_client_ip(request: HttpRequest):
        """
        Extract request's user IP-Address from request instance
        
        Args:
            request: Django request object
            
        Returns:
            str: User IP
        """
        
        if not hasattr(request, 'META'):
            raise TypeError(f'Please use a valid request instance that has META.')
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    @staticmethod
    def get_client_user_agent(request: HttpRequest):
        """
        Extract request's user agent from request instance
        
        Args:
            request: Django request object
            
        Returns:
            str: User agent
        """
        
        if not hasattr(request, 'META'):
            raise TypeError(f'Please use a valid request instance that has META.')
        
        return request.META.get('HTTP_USER_AGENT')


class FieldValidator:
    """
    A validator class for validating form/request fields with security checks.
    
    This class provides methods to validate string and boolean fields against
    allowed field names and security patterns. It integrates with GetDataMixin
    to perform comprehensive security validation including SQL injection,
    Django ORM lookups, XSS, and Redis key validation.
    
    Attributes:
        _validators (dict): Mapping of validator names to their expected types.
            Available validators:
                - max_length (int): Maximum allowed string length
                - sql (bool): Enable SQL injection validation
                - lookup (bool): Enable Django ORM lookup validation
                - injection (bool): Enable XSS/template injection validation
                - redis (bool): Enable Redis key validation
    """
    
    # Define the allowed validators and their expected data types
    _validators = {
        'max_length': int,    # Maximum length for string validation
        'sql': bool,          # Toggle SQL injection validation
        'lookup': bool,       # Toggle Django ORM lookup validation
        'injection': bool,    # Toggle XSS/injection validation
        'redis': bool         # Toggle Redis key validation
    }
    
    def _validate_validators(self, validators: Dict[str, bool | int]) -> None:
        """
        Internal method to validate the validators configuration dictionary.
        
        Ensures that:
        1. The validators parameter is a dictionary
        2. All validator keys are recognized (exist in _validators)
        3. All validator values have the correct type
        
        Args:
            validators: Dictionary containing validator configuration.
                       Keys should be from _validators, values should match
                       the expected type for each validator.
        
        Raises:
            TypeError: If validators is not a dict or if a validator value
                      has an incorrect type.
            ValueError: If an unrecognized validator key is provided.
        """
        
        # Check if validators is a dictionary
        if not isinstance(validators, dict):
            raise TypeError(
                f'Expected a dict, got {type(validators)=} instead. {validators=}'
            )
        
        # Validate each key-value pair in the validators dictionary
        for key, value in validators.items():
            # Check if the validator key is recognized
            if key not in self._validators:
                raise ValueError(f'Invalid validator: {key}: {value}')
            
            # Check if the validator value has the correct type
            if not isinstance(value, self._validators[key]):
                raise TypeError(f'Invalid validator value: {key}: {value}')
    
    def validate_string_fields(
            self,
            valid_fields: Tuple | List,
            validators: Dict[str, bool | int],
            **fields
    ) -> Tuple[bool, Dict[Any, str]]:
        """
        Validate multiple string fields against allowed field names and security patterns.
        
        This method performs comprehensive validation on string fields by:
        1. Checking if field names are in the allowed list
        2. Validating basic string requirements (non-empty, not only whitespace)
        3. Running security checks (SQL injection, XSS, Django ORM lookups, etc.)
        
        Args:
            valid_fields: Tuple or list of allowed field names. Only fields
                         in this collection will be accepted for validation.
            validators: Dictionary of validator configurations to apply.
                       See _validators attribute for available options.
            **fields: Keyword arguments where keys are field names and values
                     are the field values to validate.
        
        Returns:
            Tuple containing:
                - bool: True if all fields are valid, False if any validation fails
                - dict: Empty dict if valid, or dict with error details if invalid
                       Format: {field_name: error_message}
        
        Raises:
            TypeError: If valid_fields is not a list or tuple, or if validators
                      configuration is invalid.
        """
        
        # Validate that valid_fields is a tuple or list
        if not isinstance(valid_fields, tuple | list):
            raise TypeError(
                f'Expected a list or tuple, got {type(valid_fields)=}: {valid_fields=}'
            )
        
        # Validate the validators configuration
        self._validate_validators(validators)
        
        # Check if any fields were provided
        if not fields:
            return False, {'fields': 'There is nothing to validate'}
        
        # Validate each field
        for field, value in fields.items():
            # Check if field name is in the allowed list
            if field not in valid_fields:
                return False, {field: 'This field is not acceptable'}
            
            # Basic string validation (non-empty, not only whitespace)
            if not GetDataMixin.validate_string(value):
                return False, {field: f'This field value is invalid. {value}'}
            
            # Security validation (SQL injection, XSS, etc.)
            if not GetDataMixin.validate_string_secure(value, **validators):
                return False, {field: f'This field contains dangerous content. {value}'}
        
        # All fields passed validation
        return True, {}
    
    @staticmethod
    def validate_boolean_fields(
            valid_fields: Tuple | List,
            **fields
    ) -> Tuple[bool, Dict[Any, str]]:
        """
        Validate multiple boolean fields against allowed field names and type.
        
        This method validates that:
        1. Field names are in the allowed list
        2. Field values are boolean or can be converted to boolean
        
        The method uses GetDataMixin.convert_data_to_bool() to handle string
        representations of boolean values (e.g., 'true', 'false', '1', '0').
        
        Args:
            valid_fields: Tuple or list of allowed field names. Only fields
                         in this collection will be accepted for validation.
            **fields: Keyword arguments where keys are field names and values
                     are the field values to validate as booleans.
        
        Returns:
            Tuple containing:
                - bool: True if all fields are valid, False if any validation fails
                - dict: Empty dict if valid, or dict with error details if invalid
                       Format: {field_name: error_message}
        
        Raises:
            TypeError: If valid_fields is not a list or tuple.
        """
        
        # Validate that valid_fields is a tuple or list
        if not isinstance(valid_fields, tuple | list):
            raise TypeError(f'Expected a list or tuple, got {type(valid_fields)=}')
        
        # Check if any fields were provided
        if not fields:
            return False, {'fields': 'There is nothing to validate'}
        
        # Validate each field
        for field, value in fields.items():
            # Check if field name is in the allowed list
            if field not in valid_fields:
                return False, {field: 'This field is not acceptable'}
            
            # Check if value is already boolean or can be converted to boolean
            if not isinstance(value, bool) and not isinstance(
                    GetDataMixin.convert_data_to_bool(value), bool
            ):
                return False, {field: f'This field value should be a boolean. {value}'}
        
        # All fields passed validation
        return True, {}

    @staticmethod
    def validate_uploaded_file(
            file: UploadedFile,
            *,
            max_size: int,
            allowed_mime_types: Iterable[str],
            allowed_extensions: Iterable[str],
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Validates an uploaded file from request.data / request.FILES.
        
        Performs comprehensive validation on uploaded files including file presence,
        size limits, filename safety, extension whitelist, and MIME type verification.
        
        Args:
            file: Django UploadedFile instance from request.FILES
            max_size: Maximum file size in bytes (e.g., 5242880 for 5MB)
            allowed_mime_types: Iterable of allowed MIME types (e.g., ['image/jpeg', 'image/png'])
            allowed_extensions: Iterable of allowed file extensions without dots (e.g., ['jpg', 'png', 'pdf'])
        
        Returns:
            Tuple containing:
                - bool: True if file is valid, False otherwise
                - dict: Empty dict if valid, or dict with error details if invalid
                       Format: {'file': error_message}
        """
        # 1. Presence & type validation
        # Check if file was provided
        if file is None:
            return False, {'file': 'No file provided.'}
        
        # Verify file is a valid Django UploadedFile instance
        if not isinstance(file, UploadedFile):
            return False, {'file': 'Invalid file object.'}
        
        # 2. Size validation
        # Ensure file is not empty
        if file.size <= 0:
            return False, {'file': 'Uploaded file is empty.'}
        
        # Enforce maximum file size limit
        if file.size > max_size:
            return False, {'file': f'File size exceeds {max_size} bytes.'}
        
        # 3. Filename safety validation
        filename = file.name
        
        # Check filename exists and is within acceptable length
        if not filename or len(filename) > 255:
            return False, {'file': 'Invalid filename.'}
        
        # Prevent path traversal attacks and invalid path characters
        if '..' in filename or '/' in filename or '\\' in filename:
            return False, {'file': 'Invalid filename path.'}
        
        # 4. Extension validation
        # Extract file extension (lowercase, without leading dot)
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        
        # Verify extension is in the allowed list
        if ext not in allowed_extensions:
            return False, {'file': f'Invalid file extension: .{ext}'}
        
        # 5. MIME type validation
        # Get the content type from the uploaded file
        content_type = file.content_type
        
        # Verify MIME type is in the allowed list
        if content_type not in allowed_mime_types:
            return False, {'file': f'Invalid file type: {content_type}'}
        
        # All validations passed
        return True, {}
    