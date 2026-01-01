from urllib.parse import urlparse

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response
from typing import Any, AnyStr
import re


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
