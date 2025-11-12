"""
Unit tests for Purchase model (Saga pattern).
"""
import pytest
from decimal import Decimal
from app.models import Purchase


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseModel:
    """Tests for Purchase model (Saga pattern)."""
    
    def test_create_purchase(self):
        """Test creating a purchase with Saga fields."""
        purchase = Purchase.objects.create(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.50')
        )
        
        assert purchase.id is not None
        assert purchase.transaction_id == 'test-txn-001'
        assert purchase.user_id == 'user-123'
        assert purchase.product_id == 'prod-456'
        assert purchase.payment_id == 'pay-789'
        assert purchase.amount == Decimal('100.50')
        assert purchase.status == Purchase.STATUS_PENDING
    
    def test_purchase_str(self):
        """Test string representation."""
        purchase = Purchase.objects.create(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00'),
            status=Purchase.STATUS_SUCCESS
        )
        
        assert 'test-txn-001' in str(purchase)
        assert 'user-123' in str(purchase)
        assert 'success' in str(purchase)
    
    def test_mark_success(self):
        """Test marking a purchase as successful."""
        purchase = Purchase.objects.create(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00')
        )
        
        purchase.mark_success()
        
        assert purchase.status == Purchase.STATUS_SUCCESS
    
    def test_mark_failed(self):
        """Test marking a purchase as failed."""
        purchase = Purchase.objects.create(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00')
        )
        
        purchase.mark_failed('Test error message')
        
        assert purchase.status == Purchase.STATUS_FAILED
        assert purchase.error_message == 'Test error message'
    
    def test_cancel_purchase(self):
        """Test cancelling a purchase (compensation)."""
        purchase = Purchase.objects.create(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00')
        )
        
        purchase.cancel()
        
        assert purchase.status == Purchase.STATUS_CANCELLED
    
    def test_status_checks(self):
        """Test status check methods."""
        purchase = Purchase.objects.create(
            transaction_id='test-txn-001',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00')
        )
        
        assert purchase.is_pending()
        assert not purchase.is_success()
        assert not purchase.is_cancelled()
        assert not purchase.is_failed()
        
        purchase.mark_success()
        assert not purchase.is_pending()
        assert purchase.is_success()
        
        purchase2 = Purchase.objects.create(
            transaction_id='test-txn-002',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('50.00')
        )
        purchase2.cancel()
        assert purchase2.is_cancelled()
    
    def test_unique_transaction_id(self):
        """Test that transaction_id must be unique."""
        Purchase.objects.create(
            transaction_id='test-txn-unique',
            user_id='user-123',
            product_id='prod-456',
            payment_id='pay-789',
            amount=Decimal('100.00')
        )
        
        with pytest.raises(Exception):  # IntegrityError
            Purchase.objects.create(
                transaction_id='test-txn-unique',
                user_id='user-456',
                product_id='prod-789',
                payment_id='pay-123',
                amount=Decimal('200.00')
            )
