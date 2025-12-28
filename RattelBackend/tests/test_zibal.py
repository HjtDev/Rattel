import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from django.core.cache import cache
from payment.providers.zibal import ZibalGateway
from payment.models import Transaction


@pytest.fixture
def zibal_gateway():
    """Create a ZibalGateway instance for testing."""
    return ZibalGateway(merchant='test_merchant', cache_prefix='test_zibal')


@pytest.fixture
def mock_user(db):
    """Create a mock user for testing."""
    User = get_user_model()
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


class TestZibalGatewayInit:
    """Test ZibalGateway initialization."""
    
    def test_init_success(self):
        gateway = ZibalGateway(merchant='test_merchant')
        assert gateway.merchant == 'test_merchant'
        assert gateway.cache_prefix == 'zibal'
        assert gateway._start_cache_prefix == 'zibal-started'
    
    def test_init_custom_cache_prefix(self):
        gateway = ZibalGateway(merchant='test_merchant', cache_prefix='custom')
        assert gateway.cache_prefix == 'custom'
        assert gateway._start_cache_prefix == 'custom-started'
    
    def test_init_invalid_merchant_type(self):
        with pytest.raises(TypeError, match='merchant must be a string'):
            ZibalGateway(merchant=12345)
    
    def test_init_empty_merchant(self):
        with pytest.raises(ValueError, match='Provide a valid merchant'):
            ZibalGateway(merchant='   ')
    
    def test_init_invalid_cache_prefix_type(self):
        with pytest.raises(TypeError, match='cache_prefix must be a string'):
            ZibalGateway(merchant='test', cache_prefix=123)
    
    def test_init_empty_cache_prefix(self):
        with pytest.raises(ValueError, match='cache_prefix should not be an empty string'):
            ZibalGateway(merchant='test', cache_prefix='  ')


class TestStartPayment:
    """Test start_payment method."""
    
    @patch('payment.providers.zibal.requests.post')
    def test_start_payment_success(self, mock_post, zibal_gateway):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 100,
            'trackId': 123456,
            'message': 'Success'
        }
        mock_post.return_value = mock_response
        
        success, track_id = zibal_gateway.start_payment(
            amount=10000,
            callback_url='https://example.com/callback',
            identifier='ORDER-123',
            phone='09123456789'
        )
        
        assert success is True
        assert track_id == 123456
        
        # Verify cache was set
        cached_data = cache.get('test_zibal-started-test_merchant-ORDER-123')
        assert cached_data is not None
        assert cached_data['track_id'] == 123456
        assert cached_data['amount'] == 10000
    
    @patch('payment.providers.zibal.requests.post')
    def test_start_payment_removes_none_values(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 100, 'trackId': 123456}
        mock_post.return_value = mock_response
        
        zibal_gateway.start_payment(
            amount=10000,
            callback_url='https://example.com/callback',
            identifier='ORDER-123',
            phone='09123456789',
            description=None,  # Should be removed
            national_code=None  # Should be removed
        )
        
        # Get the actual request body sent
        call_args = mock_post.call_args
        sent_data = call_args.kwargs['json']
        
        # None values should not be in the request
        assert 'description' not in sent_data or sent_data.get('description') is not None
        assert 'nationalCode' not in sent_data or sent_data.get('nationalCode') is not None
    
    def test_start_payment_invalid_amount_type(self, zibal_gateway):
        with pytest.raises(TypeError, match='amount must be an integer'):
            zibal_gateway.start_payment(
                amount='10000',
                callback_url='https://example.com/callback',
                identifier='ORDER-123',
                phone='09123456789'
            )
    
    def test_start_payment_amount_too_small(self, zibal_gateway):
        with pytest.raises(ValueError, match='amount must be greater than 1000'):
            zibal_gateway.start_payment(
                amount=500,
                callback_url='https://example.com/callback',
                identifier='ORDER-123',
                phone='09123456789'
            )
    
    def test_start_payment_invalid_callback_url_type(self, zibal_gateway):
        with pytest.raises(TypeError, match='callback_url must be a string'):
            zibal_gateway.start_payment(
                amount=10000,
                callback_url=12345,
                identifier='ORDER-123',
                phone='09123456789'
            )
    
    def test_start_payment_invalid_callback_url_format(self, zibal_gateway):
        with pytest.raises(ValueError, match='Use a valid URL for callback_url'):
            zibal_gateway.start_payment(
                amount=10000,
                callback_url='not-a-url',
                identifier='ORDER-123',
                phone='09123456789'
            )
    
    def test_start_payment_invalid_identifier_type(self, zibal_gateway):
        with pytest.raises(TypeError, match='identifier must be a string'):
            zibal_gateway.start_payment(
                amount=10000,
                callback_url='https://example.com/callback',
                identifier=12345,
                phone='09123456789'
            )
    
    def test_start_payment_invalid_phone_type(self, zibal_gateway):
        with pytest.raises(TypeError, match='phone must be a string'):
            zibal_gateway.start_payment(
                amount=10000,
                callback_url='https://example.com/callback',
                identifier='ORDER-123',
                phone=9123456789
            )
    
    @patch('payment.providers.zibal.requests.post')
    def test_start_payment_network_error(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response
        
        success, error = zibal_gateway.start_payment(
            amount=10000,
            callback_url='https://example.com/callback',
            identifier='ORDER-123',
            phone='09123456789'
        )
        
        assert success is False
        assert 'Could not connect to Zibal gateway' in error
    
    @patch('payment.providers.zibal.requests.post')
    def test_start_payment_invalid_merchant(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 102,  # merchant not found
            'trackId': None
        }
        mock_post.return_value = mock_response
        
        success, error = zibal_gateway.start_payment(
            amount=10000,
            callback_url='https://example.com/callback',
            identifier='ORDER-123',
            phone='09123456789'
        )
        
        assert success is False
        assert 'Invalid parameters' in error
    
    @patch('payment.providers.zibal.requests.post')
    def test_start_payment_missing_track_id(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 100,
            'trackId': None  # Missing track_id
        }
        mock_post.return_value = mock_response
        
        success, error = zibal_gateway.start_payment(
            amount=10000,
            callback_url='https://example.com/callback',
            identifier='ORDER-123',
            phone='09123456789'
        )
        
        assert success is False
        assert 'Could not get track ID' in error


class TestBuildGatewayUrl:
    """Test build_gateway_url method."""
    
    def test_build_gateway_url(self, zibal_gateway):
        url = zibal_gateway.build_gateway_url(123456)
        assert url == 'https://gateway.zibal.ir/start/123456/'
    
    def test_build_gateway_url_different_track_id(self, zibal_gateway):
        url = zibal_gateway.build_gateway_url(999999)
        assert url == 'https://gateway.zibal.ir/start/999999/'


class TestValidateGatewayResponse:
    """Test validate_gateway_response method."""
    
    @patch('payment.providers.zibal.ZibalGateway.verify_transaction')
    def test_validate_gateway_response_success(self, mock_verify, zibal_gateway, mock_user, db):
        # Setup cache
        cache.set('test_zibal-started-test_merchant-ORDER-123', {
            'track_id': 123456,
            'amount': 10000,
            'callback_url': 'https://example.com/callback',
            'reason': Transaction.TransactionReason.PAYMENT
        }, timeout=600)
        
        # Mock verify response
        mock_verify.return_value = (True, {
            'amount': 10000,
            'identifier': 'ORDER-123',
            'status': 1,
            'reference_number': 'REF123'
        })
        
        response_data = {
            'success': '1',
            'trackId': 123456,
            'orderId': 'ORDER-123',
            'status': 1
        }
        
        success, metadata = zibal_gateway.validate_gateway_response(
            response_data,
            user=mock_user
        )
        
        assert success is True
        assert metadata is not None
        assert 'transaction' in metadata
        
        # Check transaction was created
        transaction = Transaction.objects.get(id=metadata['transaction'])
        assert transaction.transaction_status == Transaction.TransactionStatus.SUCCESS
        assert transaction.amount == 10000
        assert transaction.user == mock_user
    
    def test_validate_gateway_response_no_user(self, zibal_gateway):
        response_data = {
            'success': '1',
            'trackId': 123456,
            'orderId': 'ORDER-123',
            'status': 1
        }
        
        with pytest.raises(RuntimeError, match='User must be set'):
            zibal_gateway.validate_gateway_response(response_data)
    
    def test_validate_gateway_response_payment_failed(self, zibal_gateway, mock_user):
        response_data = {
            'success': '0',  # Failed
            'trackId': 123456,
            'orderId': 'ORDER-123',
            'status': 0
        }
        
        success, metadata = zibal_gateway.validate_gateway_response(
            response_data,
            user=mock_user
        )
        
        assert success is False
        assert metadata is None
    
    def test_validate_gateway_response_missing_track_id(self, zibal_gateway, mock_user):
        response_data = {
            'success': '1',
            'trackId': None,  # Missing
            'orderId': 'ORDER-123',
            'status': 1
        }
        
        success, metadata = zibal_gateway.validate_gateway_response(
            response_data,
            user=mock_user
        )
        
        assert success is False
        assert metadata is None
    
    def test_validate_gateway_response_no_cache_data(self, zibal_gateway, mock_user):
        response_data = {
            'success': '1',
            'trackId': 123456,
            'orderId': 'ORDER-999',  # Not in cache
            'status': 1
        }
        
        success, metadata = zibal_gateway.validate_gateway_response(
            response_data,
            user=mock_user
        )
        
        assert success is False
        assert metadata is None
    
    @patch('payment.providers.zibal.ZibalGateway.verify_transaction')
    def test_validate_gateway_response_track_id_mismatch(self, mock_verify, zibal_gateway, mock_user):
        # Setup cache with different track_id
        cache.set('test_zibal-started-test_merchant-ORDER-123', {
            'track_id': 999999,  # Different track_id
            'amount': 10000,
            'callback_url': 'https://example.com/callback',
            'reason': Transaction.TransactionReason.PAYMENT
        }, timeout=600)
        
        response_data = {
            'success': '1',
            'trackId': 123456,
            'orderId': 'ORDER-123',
            'status': 1
        }
        
        success, metadata = zibal_gateway.validate_gateway_response(
            response_data,
            user=mock_user
        )
        
        assert success is False
        assert metadata is None


class TestVerifyTransaction:
    """Test verify_transaction method."""
    
    @patch('payment.providers.zibal.requests.post')
    def test_verify_transaction_success(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 100,
            'paidAt': '2024-01-01T12:00:00.000',
            'cardNumber': '1234****5678',
            'status': 2,
            'amount': 10000,
            'refNumber': 'REF123',
            'description': 'Test payment',
            'orderId': 'ORDER-123',
            'message': 'Success'
        }
        mock_post.return_value = mock_response
        
        success, metadata = zibal_gateway.verify_transaction(123456)
        
        assert success is True
        assert metadata['amount'] == 10000
        assert metadata['reference_number'] == 'REF123'
        assert metadata['masked_card_number'] == '1234****5678'
    
    def test_verify_transaction_invalid_track_id_type(self, zibal_gateway):
        with pytest.raises(ValueError, match='track_id must be an integer'):
            zibal_gateway.verify_transaction('not-an-int')
    
    @patch('payment.providers.zibal.requests.post')
    def test_verify_transaction_network_error(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        success, metadata = zibal_gateway.verify_transaction(123456)
        
        assert success is False
        assert metadata is None
    
    @patch('payment.providers.zibal.requests.post')
    def test_verify_transaction_already_verified(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 201,  # Already verified
            'amount': 10000
        }
        mock_post.return_value = mock_response
        
        success, metadata = zibal_gateway.verify_transaction(123456)
        
        assert success is False
        assert metadata is not None
    
    @patch('payment.providers.zibal.requests.post')
    def test_verify_transaction_unsuccessful(self, mock_post, zibal_gateway):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': 202,  # Transaction not successful
            'amount': 10000
        }
        mock_post.return_value = mock_response
        
        success, metadata = zibal_gateway.verify_transaction(123456)
        
        assert success is False


class TestCheckGatewayStarterResult:
    """Test _check_gateway_starter_result method."""
    
    def test_check_result_success(self, zibal_gateway):
        assert zibal_gateway._check_gateway_starter_result(100) is True
    
    def test_check_result_merchant_not_found(self, zibal_gateway):
        assert zibal_gateway._check_gateway_starter_result(102) is False
    
    def test_check_result_merchant_disabled(self, zibal_gateway):
        assert zibal_gateway._check_gateway_starter_result(103) is False
    
    def test_check_result_unknown_error(self, zibal_gateway):
        assert zibal_gateway._check_gateway_starter_result(999) is False


class TestValidateVerifyResult:
    """Test _validate_verify_result method."""
    
    def test_validate_result_success(self, zibal_gateway):
        assert zibal_gateway._validate_verify_result(100) is True
    
    def test_validate_result_already_verified(self, zibal_gateway):
        assert zibal_gateway._validate_verify_result(201) is False
    
    def test_validate_result_unsuccessful(self, zibal_gateway):
        assert zibal_gateway._validate_verify_result(202) is False
    
    def test_validate_result_invalid_track_id(self, zibal_gateway):
        assert zibal_gateway._validate_verify_result(203) is False


class TestRestoreGatewayData:
    """Test _restore_gateway_data method."""
    
    def test_restore_gateway_data_exists(self, zibal_gateway):
        test_data = {'track_id': 123456, 'amount': 10000}
        cache.set('test_zibal-started-test_merchant-ORDER-123', test_data, timeout=600)
        
        restored = zibal_gateway._restore_gateway_data('ORDER-123')
        
        assert restored == test_data
        # Should be deleted after restore
        assert cache.get('test_zibal-started-test_merchant-ORDER-123') is None
    
    def test_restore_gateway_data_not_exists(self, zibal_gateway):
        restored = zibal_gateway._restore_gateway_data('NON-EXISTENT')
        assert restored is None
