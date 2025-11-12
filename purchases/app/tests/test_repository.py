"""
Unit tests for PurchaseRepository (simplified Saga pattern).
"""
import pytest
from decimal import Decimal
from app.models import Purchase


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseRepository:
    """Tests for Purchase model with simplified Saga pattern."""
    
    def test_get_by_id_existing(self, created_purchase):
        """Test retrieving existing purchase by ID."""
        purchase = Purchase.objects.get(id=created_purchase.id)
        
        assert purchase is not None
        assert purchase.id == created_purchase.id
        assert purchase.transaction_id == 'test-txn-fixture'
    
    def test_get_by_id_non_existing(self):
        """Test retrieving non-existing purchase raises exception."""
        with pytest.raises(Purchase.DoesNotExist):
            Purchase.objects.get(id=99999)
    
    def test_get_by_transaction_id(self, created_purchase):
        """Test retrieving purchase by transaction_id."""
        purchase = Purchase.objects.get(
            transaction_id='test-txn-fixture'
        )
        
        assert purchase is not None
        assert purchase.transaction_id == 'test-txn-fixture'
        assert purchase.user_id == 'user-123'
    
    def test_get_by_user_id(self, created_purchase):
        """Test retrieving purchases by user_id."""
        # Create another purchase for same user
        Purchase.objects.create(
            transaction_id='test-txn-user-2',
            user_id='user-123',
            product_id='prod-999',
            payment_id='pay-999',
            amount=Decimal('75.00')
        )
        
        purchases = Purchase.objects.filter(user_id='user-123')
        
        assert purchases.count() >= 2
        assert all(p.user_id == 'user-123' for p in purchases)
    
    def test_mark_success(self, created_purchase):
        """Test marking purchase as successful."""
        created_purchase.mark_success()
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_SUCCESS
    
    def test_cancel_purchase(self, created_purchase):
        """Test cancelling a purchase."""
        created_purchase.cancel()
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_CANCELLED
    
    def test_mark_failed_with_message(self, created_purchase):
        """Test marking purchase as failed with error message."""
        error_msg = "Test error message"
        created_purchase.mark_failed(error_msg)
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_FAILED
        assert purchase.error_message == error_msg
    
    def test_mark_failed_without_message(self, created_purchase):
        """Test failing purchase without error message."""
        created_purchase.mark_failed()
        
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_FAILED
    
    def test_get_all_purchases(self, created_purchase):
        """Test retrieving all purchases."""
        # Create additional purchases
        Purchase.objects.create(
            transaction_id='test-txn-all-1',
            user_id='user-999',
            product_id='prod-111',
            payment_id='pay-111',
            amount=Decimal('25.00')
        )
        
        purchases = Purchase.objects.all()
        
        assert purchases.count() >= 2
    
    def test_purchase_status_methods(self, created_purchase):
        """Test purchase status check methods."""
        assert created_purchase.is_pending()
        assert not created_purchase.is_success()
        assert not created_purchase.is_cancelled()
        assert not created_purchase.is_failed()
        
        created_purchase.mark_success()
        assert created_purchase.is_success()
        assert not created_purchase.is_pending()
