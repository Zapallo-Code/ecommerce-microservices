"""
Unit tests for PurchaseService.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from app.services import PurchaseService
from app.models import Purchase


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseService:
    """Tests for PurchaseService."""
    
    def test_service_initialization(self):
        """Test service initializes correctly."""
        service = PurchaseService()
        
        assert service is not None
        assert service.repository is not None
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_process_purchase_success(
        self,
        mock_sleep,
        mock_random,
        sample_items
    ):
        """Test successful purchase processing."""
        mock_random.return_value = 0.3  # Below 0.5, will succeed
        
        service = PurchaseService()
        result = service.process_purchase(
            customer_id=1,
            items=sample_items
        )
        
        assert result['success'] is True
        assert result['status'] == 'confirmed'
        assert 'purchase_id' in result
        assert 'saga_id' in result
        assert mock_sleep.called
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_process_purchase_failure(
        self,
        mock_sleep,
        mock_random,
        sample_items
    ):
        """Test failed purchase processing."""
        mock_random.return_value = 0.7  # Above 0.5, will fail
        
        service = PurchaseService()
        result = service.process_purchase(
            customer_id=1,
            items=sample_items
        )
        
        assert result['success'] is False
        assert result['status'] == 'failed'
        assert 'purchase_id' in result
        assert 'error' in result
        assert mock_sleep.called
    
    @patch('app.services.purchase_service.time.sleep')
    def test_process_purchase_creates_saga_id(
        self,
        mock_sleep,
        sample_items
    ):
        """Test that saga_id is generated."""
        service = PurchaseService()
        result = service.process_purchase(
            customer_id=1,
            items=sample_items
        )
        
        assert 'saga_id' in result
        assert result['saga_id'] is not None
        assert len(result['saga_id']) > 0
    
    @patch('app.services.purchase_service.time.sleep')
    def test_process_purchase_exception_handling(self, mock_sleep):
        """Test exception handling in process_purchase."""
        service = PurchaseService()
        
        # Pass invalid data that will cause a KeyError
        result = service.process_purchase(
            customer_id=1,
            items=[{'invalid_key': 'value'}]  # Missing required keys
        )
        
        assert result['success'] is False
        assert result['status'] == 'error'
        assert 'error' in result
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_by_id_success(
        self,
        mock_sleep,
        created_purchase
    ):
        """Test successful compensation by purchase_id."""
        service = PurchaseService()
        result = service.compensate_purchase(
            purchase_id=created_purchase.id
        )
        
        assert result['success'] is True
        assert result['status'] == 'cancelled'
        assert result['purchase_id'] == created_purchase.id
        assert mock_sleep.called
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_by_saga_id_success(
        self,
        mock_sleep,
        created_purchase
    ):
        """Test successful compensation by saga_id."""
        service = PurchaseService()
        result = service.compensate_purchase(
            saga_id='test-saga-123'
        )
        
        assert result['success'] is True
        assert result['status'] == 'cancelled'
        assert result['saga_id'] == 'test-saga-123'
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_not_found(self, mock_sleep):
        """Test compensation with non-existing purchase."""
        service = PurchaseService()
        result = service.compensate_purchase(purchase_id=99999)
        
        assert result['success'] is False
        assert result['error'] == 'NOT_FOUND'
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_missing_identifier(self, mock_sleep):
        """Test compensation without purchase_id or saga_id."""
        service = PurchaseService()
        result = service.compensate_purchase()
        
        assert result['success'] is False
        assert result['error'] == 'MISSING_IDENTIFIER'
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_invalid_state(
        self,
        mock_sleep,
        created_purchase
    ):
        """Test compensation with invalid purchase state."""
        # Confirm purchase first
        created_purchase.confirm()
        
        service = PurchaseService()
        result = service.compensate_purchase(
            purchase_id=created_purchase.id
        )
        
        assert result['success'] is False
        assert result['error'] == 'INVALID_STATE'
    
    def test_get_purchase_existing(self, created_purchase):
        """Test getting existing purchase."""
        service = PurchaseService()
        purchase = service.get_purchase(created_purchase.id)
        
        assert purchase is not None
        assert purchase.id == created_purchase.id
    
    def test_get_purchase_non_existing(self):
        """Test getting non-existing purchase returns None."""
        service = PurchaseService()
        purchase = service.get_purchase(99999)
        
        assert purchase is None
    
    def test_get_customer_purchases(self, sample_items):
        """Test getting purchases by customer."""
        service = PurchaseService()
        
        # Create purchases for customer
        from app.repositories import PurchaseRepository
        PurchaseRepository.create_purchase(
            customer_id=10,
            items=sample_items
        )
        PurchaseRepository.create_purchase(
            customer_id=10,
            items=sample_items
        )
        
        purchases = service.get_customer_purchases(10)
        
        assert len(purchases) == 2
        assert all(p.customer_id == 10 for p in purchases)
    
    def test_get_customer_purchases_with_limit(self, sample_items):
        """Test get_customer_purchases respects limit."""
        service = PurchaseService()
        
        # Create multiple purchases
        from app.repositories import PurchaseRepository
        for _ in range(5):
            PurchaseRepository.create_purchase(
                customer_id=11,
                items=sample_items
            )
        
        purchases = service.get_customer_purchases(11, limit=3)
        
        assert len(purchases) == 3
    
    @patch('app.services.purchase_service.random.randint')
    def test_latency_simulation_ranges(self, mock_randint, sample_items):
        """Test that latency is within configured ranges."""
        mock_randint.return_value = 100
        
        service = PurchaseService()
        
        # Test purchase latency range
        assert service.MIN_LATENCY_MS == 50
        assert service.MAX_LATENCY_MS == 200
        
        # Test compensation latency range
        assert service.COMPENSATION_MIN_LATENCY_MS == 30
        assert service.COMPENSATION_MAX_LATENCY_MS == 100
    
    def test_success_rate_configuration(self):
        """Test that success rate is configured correctly."""
        service = PurchaseService()
        
        assert service.SUCCESS_RATE == 0.5
