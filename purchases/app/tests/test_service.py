"""
Unit tests for PurchaseService (Saga pattern).
"""
import pytest
from unittest.mock import patch
from decimal import Decimal
from app.services.purchase_service import PurchaseService
from app.models import Purchase


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseService:
    """Tests for PurchaseService (Saga pattern)."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = PurchaseService()
        assert service is not None
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_success(
        self,
        mock_sleep,
        mock_random
    ):
        """Test successful purchase creation."""
        mock_random.return_value = 0.3  # Below 0.5, will succeed
        
        service = PurchaseService()
        result = service.create_purchase(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=100.50
        )
        
        assert result['status'] == 'success'
        assert 'purchase_id' in result
        assert result['transaction_id'] == 'test-txn-001'
        assert mock_sleep.called
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_failure(
        self,
        mock_sleep,
        mock_random
    ):
        """Test failed purchase creation (409 Conflict)."""
        mock_random.return_value = 0.7  # Above 0.5, will fail
        
        service = PurchaseService()
        result = service.create_purchase(
            transaction_id='test-txn-002',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=100.50
        )
        
        assert result['status'] == 'error'
        assert result['message'] == 'Purchase failed'
        assert result['error'] == 'CONFLICT'
        assert mock_sleep.called
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_idempotency(
        self,
        mock_sleep,
        mock_random
    ):
        """Test that duplicate transaction_id returns existing purchase."""
        mock_random.return_value = 0.3  # Ensure success
        service = PurchaseService()
        
        # First call
        result1 = service.create_purchase(
            transaction_id='test-txn-idempotent',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=100.50
        )
        
        # Second call with same transaction_id
        result2 = service.create_purchase(
            transaction_id='test-txn-idempotent',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=100.50
        )
        
        assert result1['transaction_id'] == result2['transaction_id']
        assert result1['purchase_id'] == result2['purchase_id']
        assert result1['status'] == 'success'
        assert result2['status'] == 'success'
    
    @patch('app.services.purchase_service.time.sleep')
    def test_cancel_purchase_success(self, mock_sleep):
        """Test successful purchase cancellation."""
        # First create a purchase
        Purchase.objects.create(
            transaction_id='test-txn-cancel',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00'),
            status=Purchase.STATUS_PENDING
        )
        
        service = PurchaseService()
        result = service.cancel_purchase('test-txn-cancel')
        
        assert result['status'] == 'success'
        assert result['transaction_id'] == 'test-txn-cancel'
        assert mock_sleep.called
        
        # Verify purchase was cancelled
        purchase = Purchase.objects.get(transaction_id='test-txn-cancel')
        assert purchase.status == Purchase.STATUS_CANCELLED
    
    @patch('app.services.purchase_service.time.sleep')
    def test_cancel_purchase_not_found(self, mock_sleep):
        """Test cancellation with non-existing transaction (idempotent)."""
        service = PurchaseService()
        result = service.cancel_purchase('non-existent-txn')
        
        # Should still return success for idempotency
        assert result['status'] == 'success'
    
    @patch('app.services.purchase_service.time.sleep')
    def test_latency_simulation(self, mock_sleep):
        """Test that latency simulation is called."""
        service = PurchaseService()
        service.create_purchase(
            transaction_id='test-latency',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=100.50
        )
        
        # Verify sleep was called
        assert mock_sleep.called
        # Check that latency is in expected range (50-200 ms)
        call_args = mock_sleep.call_args[0][0]
        assert 0.05 <= call_args <= 0.2
    
    def test_success_rate_configuration(self):
        """Test that success rate is configured correctly."""
        service = PurchaseService()
        assert service.SUCCESS_RATE == 0.5
    
    def test_latency_configuration(self):
        """Test that latency ranges are configured correctly."""
        service = PurchaseService()
        assert service.MIN_LATENCY_MS == 50
        assert service.MAX_LATENCY_MS == 200
