"""
Unit tests for PurchaseRepository.
"""
import pytest
from decimal import Decimal
from app.repositories import PurchaseRepository
from app.models import Purchase, PurchaseDetail


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseRepository:
    """Tests for PurchaseRepository."""
    
    def test_create_purchase(self, sample_items):
        """Test creating a purchase with details."""
        purchase = PurchaseRepository.create_purchase(
            customer_id=1,
            items=sample_items,
            saga_id='test-saga-001'
        )
        
        assert purchase.id is not None
        assert purchase.customer_id == 1
        assert purchase.saga_id == 'test-saga-001'
        assert purchase.status == Purchase.STATUS_PENDING
        assert purchase.details.count() == 2
        assert purchase.total_amount == Decimal('109.97')
    
    def test_create_purchase_without_saga_id(self, sample_items):
        """Test creating purchase without saga_id."""
        purchase = PurchaseRepository.create_purchase(
            customer_id=2,
            items=sample_items
        )
        
        assert purchase.id is not None
        assert purchase.saga_id is None
    
    def test_create_purchase_calculates_total(self):
        """Test that total is calculated correctly."""
        items = [
            {
                'product_id': 1,
                'quantity': 5,
                'unit_price': Decimal('10.00')
            }
        ]
        
        purchase = PurchaseRepository.create_purchase(
            customer_id=1,
            items=items
        )
        
        assert purchase.total_amount == Decimal('50.00')
    
    def test_get_by_id_existing(self, created_purchase):
        """Test retrieving existing purchase by ID."""
        purchase = PurchaseRepository.get_by_id(created_purchase.id)
        
        assert purchase is not None
        assert purchase.id == created_purchase.id
        assert purchase.details.count() == 2
    
    def test_get_by_id_non_existing(self):
        """Test retrieving non-existing purchase returns None."""
        purchase = PurchaseRepository.get_by_id(99999)
        
        assert purchase is None
    
    def test_get_by_saga_id_existing(self, created_purchase):
        """Test retrieving purchase by saga_id."""
        purchase = PurchaseRepository.get_by_saga_id('test-saga-123')
        
        assert purchase is not None
        assert purchase.saga_id == 'test-saga-123'
    
    def test_get_by_saga_id_non_existing(self):
        """Test retrieving non-existing saga returns None."""
        purchase = PurchaseRepository.get_by_saga_id('non-existing')
        
        assert purchase is None
    
    def test_get_by_customer(self, sample_items):
        """Test retrieving purchases by customer."""
        # Create multiple purchases for same customer
        PurchaseRepository.create_purchase(
            customer_id=5,
            items=sample_items
        )
        PurchaseRepository.create_purchase(
            customer_id=5,
            items=sample_items
        )
        PurchaseRepository.create_purchase(
            customer_id=6,
            items=sample_items
        )
        
        purchases = PurchaseRepository.get_by_customer(5)
        
        assert len(purchases) == 2
        assert all(p.customer_id == 5 for p in purchases)
    
    def test_get_by_customer_with_limit(self, sample_items):
        """Test limit parameter works."""
        # Create 3 purchases
        for _ in range(3):
            PurchaseRepository.create_purchase(
                customer_id=7,
                items=sample_items
            )
        
        purchases = PurchaseRepository.get_by_customer(7, limit=2)
        
        assert len(purchases) == 2
    
    def test_confirm_purchase_success(self, created_purchase):
        """Test confirming a purchase."""
        result = PurchaseRepository.confirm_purchase(created_purchase.id)
        
        assert result is True
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_CONFIRMED
    
    def test_confirm_purchase_non_existing(self):
        """Test confirming non-existing purchase returns False."""
        result = PurchaseRepository.confirm_purchase(99999)
        
        assert result is False
    
    def test_confirm_purchase_invalid_status(self, created_purchase):
        """Test confirming purchase with invalid status."""
        created_purchase.status = Purchase.STATUS_CANCELLED
        created_purchase.save()
        
        result = PurchaseRepository.confirm_purchase(created_purchase.id)
        
        assert result is False
    
    def test_cancel_purchase_success(self, created_purchase):
        """Test cancelling a purchase."""
        result = PurchaseRepository.cancel_purchase(created_purchase.id)
        
        assert result is True
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_CANCELLED
    
    def test_cancel_purchase_non_existing(self):
        """Test cancelling non-existing purchase returns False."""
        result = PurchaseRepository.cancel_purchase(99999)
        
        assert result is False
    
    def test_fail_purchase_success(self, created_purchase):
        """Test marking purchase as failed."""
        error_msg = "Test error message"
        result = PurchaseRepository.fail_purchase(
            created_purchase.id,
            error_msg
        )
        
        assert result is True
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_FAILED
        assert purchase.error_message == error_msg
    
    def test_fail_purchase_without_message(self, created_purchase):
        """Test failing purchase without error message."""
        result = PurchaseRepository.fail_purchase(created_purchase.id)
        
        assert result is True
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_FAILED
    
    def test_get_all(self, sample_items):
        """Test retrieving all purchases."""
        # Create multiple purchases
        for i in range(3):
            PurchaseRepository.create_purchase(
                customer_id=i,
                items=sample_items
            )
        
        purchases = PurchaseRepository.get_all()
        
        assert len(purchases) >= 3
    
    def test_get_all_with_limit(self, sample_items):
        """Test get_all with limit."""
        purchases = PurchaseRepository.get_all(limit=5)
        
        assert len(purchases) <= 5
