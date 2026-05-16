import pytest
from rest_framework import status
from rest_framework.response import Response
from RattelBackend.mixins import ResponseBuilderMixin, GetDataMixin


class TestResponseBuilderMixin:
    
    def test_build_response_default_status(self):
        response = ResponseBuilderMixin.build_response(message="ok")
        assert isinstance(response, Response)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"message": "ok"}
    
    def test_build_response_custom_status(self):
        response = ResponseBuilderMixin.build_response(
            status.HTTP_201_CREATED,
            id=1
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {"id": 1}
    
    def test_build_response_no_content(self):
        response = ResponseBuilderMixin.build_response(
            status.HTTP_204_NO_CONTENT
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None


class TestUsernameValidation:
    
    @pytest.mark.parametrize("username", [
        "john_doe",
        "John123",
        "a_b.c",
    ])
    def test_valid_username(self, username):
        assert GetDataMixin.validate_username(username) is True
    
    @pytest.mark.parametrize("username", [
        "1john",
        "jo",
        "john@doe",
        "",
        None,
    ])
    def test_invalid_username(self, username):
        assert GetDataMixin.validate_username(username) is False
        
        
class TestEmailValidation:
    
    def test_valid_email(self):
        assert GetDataMixin.validate_email("test@example.com") is True
    
    @pytest.mark.parametrize("email", [
        "invalid",
        "test@",
        "@example.com",
        None,
    ])
    def test_invalid_email(self, email):
        assert GetDataMixin.validate_email(email) is False


class TestPhoneValidation:
    
    def test_valid_phone(self):
        assert GetDataMixin.validate_phone("09123456789") is True
    
    @pytest.mark.parametrize("phone", [
        "9123456789",
        "09123",
        "09abcdefgh",
        None,
    ])
    def test_invalid_phone(self, phone):
        assert GetDataMixin.validate_phone(phone) is False


class TestPasswordValidation:
    
    def test_valid_password(self, settings):
        settings.AUTH_PASSWORD_VALIDATORS = []
        valid, errors = GetDataMixin.validate_password("StrongPass123!")
        assert valid is True
        assert errors == []
    
    def test_password_mismatch(self):
        valid, errors = GetDataMixin.validate_password(
            "password123",
            "password321"
        )
        assert valid is False
        assert "Passwords don't match" in errors
        
        
class TestIsId:
    
    @pytest.mark.parametrize("value", [1, "1", 999])
    def test_valid_id(self, value):
        assert GetDataMixin.is_id(value) is True
    
    @pytest.mark.parametrize("value", [0, -1, "0", "abc", None])
    def test_invalid_id(self, value):
        assert GetDataMixin.is_id(value) is False


class TestConvertToBool:
    
    @pytest.mark.parametrize("value", ["true", "yes", "y", "1", 1, True])
    def test_truthy_values(self, value):
        assert GetDataMixin.convert_data_to_bool(value) is True
    
    @pytest.mark.parametrize("value", ["false", 0, None, False, "no"])
    def test_falsy_values(self, value):
        assert GetDataMixin.convert_data_to_bool(value) is False


class TestGetData:
    
    def test_get_data_success(self, post_request):
        request = post_request({
            "username": "john_doe",
            "email": "john@example.com"
        })
        
        success, data = GetDataMixin.get_data(
            request,
            "username",
            ("email", GetDataMixin.validate_email),
        )
        
        assert success is True
        assert data == {
            "username": "john_doe",
            "email": "john@example.com"
        }
    
    def test_missing_required_field(self, post_request):
        request = post_request({"username": "john_doe"})
        
        success, errors = GetDataMixin.get_data(
            request,
            "username",
            ("email", GetDataMixin.validate_email),
        )
        
        assert success is False
        assert "email is required" in errors
    
    def test_invalid_field(self, post_request):
        request = post_request({
            "username": "john_doe",
            "email": "invalid-email"
        })
        
        success, errors = GetDataMixin.get_data(
            request,
            "username",
            ("email", GetDataMixin.validate_email),
        )
        
        assert success is False
        assert "email is invalid" in errors
    
    def test_validator_exception_handling(self, post_request):
        def exploding_validator(_):
            raise RuntimeError("boom")
        
        request = post_request({"field": "value"})
        
        success, errors = GetDataMixin.get_data(
            request,
            ("field", exploding_validator),
        )
        
        assert success is False
        assert "field validation error: boom" in errors
    
    def test_get_request_uses_query_params(self, get_request):
        request = get_request({"id": "1"})
        
        success, data = GetDataMixin.get_data(
            request,
            ("id", GetDataMixin.is_id),
        )
        
        assert success is True
        assert data["id"] == "1"
