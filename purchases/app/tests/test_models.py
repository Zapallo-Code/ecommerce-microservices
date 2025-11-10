"""
Unit tests for Purchase and PurchaseDetail models.
"""
import pytest
from decimal import Decimal
from django.db import transaction
from app.models import Purchase, PurchaseDetail


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseModel:
    """Tests for Purchase model."""
    
    def test_create_purchase(self):
        """Test creating a purchase."""
        purchase = Purchase.objects.create(
            customer_id=1,
            saga_id='test-saga-001'
        )
        
        assert purchase.id is not None
        assert purchase.customer_id == 1
        assert purchase.status == Purchase.STATUS_PENDING
        assert purchase.total_amount == Decimal('0.00')
        assert purchase.saga_id == 'test-saga-001'
    
    def test_purchase_str(self):
        """Test string representation."""
        purchase = Purchase.objects.create(
            customer_id=1,
            status=Purchase.STATUS_CONFIRMED
        )
        
        expected = f"Purchase #{purchase.id} - Customer 1 - confirmed"
        assert str(purchase) == expected
    
    def test_calculate_total(self):
        """Test total calculation from details."""
        purchase = Purchase.objects.create(customer_id=1)
        
        PurchaseDetail.objects.create(
            purchase=purchase,
            product_id=1,
            quantity=2,
            unit_price=Decimal('10.00')
        )
        PurchaseDetail.objects.create(
            purchase=purchase,
            product_id=2,
            quantity=3,
            unit_price=Decimal('5.00')
        )
        
        total = purchase.calculate_total()
        
        assert total == Decimal('35.00')
        assert purchase.total_amount == Decimal('35.00')
    
    def test_confirm_purchase(self):
        """Test confirming a purchase."""
        purchase = Purchase.objects.create(customer_id=1)
        
        purchase.confirm()
        
        assert purchase.status == Purchase.STATUS_CONFIRMED
    
    def test_confirm_non_pending_purchase_raises_error(self):
        """Test that confirming non-pending purchase raises error."""
        purchase = Purchase.objects.create(
            customer_id=1,
            status=Purchase.STATUS_CANCELLED
        )
        
        with pytest.raises(ValueError):
            purchase.confirm()
    
    def test_cancel_purchase(self):
        """Test cancelling a purchase."""
        purchase = Purchase.objects.create(customer_id=1)
        
        purchase.cancel()
        
        assert purchase.status == Purchase.STATUS_CANCELLED
    
    def test_cancel_confirmed_purchase_raises_error(self):
        """Test that cancelling confirmed purchase raises error."""
        purchase = Purchase.objects.create(
            customer_id=1,
            status=Purchase.STATUS_CONFIRMED
        )
        
        with pytest.raises(ValueError):
            purchase.cancel()
    
    def test_fail_purchase(self):
        """Test failing a purchase."""
        purchase = Purchase.objects.create(customer_id=1)
        
        purchase.fail('Test error message')
        
        assert purchase.status == Purchase.STATUS_FAILED
        assert purchase.error_message == 'Test error message'
    
    def test_status_checks(self):
        """Test status check methods."""
        purchase = Purchase.objects.create(customer_id=1)
        
        assert purchase.is_pending()
        assert not purchase.is_confirmed()
        assert not purchase.is_cancelled()
        assert not purchase.is_failed()
        
        purchase.confirm()
        assert not purchase.is_pending()
        assert purchase.is_confirmed()


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseDetailModel:
    """Tests for PurchaseDetail model."""
    
    def test_create_detail(self):
        """Test creating a purchase detail."""
        purchase = Purchase.objects.create(customer_id=1)
        
        detail = PurchaseDetail.objects.create(
            purchase=purchase,
            product_id=1,
            quantity=2,
            unit_price=Decimal('10.00')
        )
        
        assert detail.id is not None
        assert detail.purchase == purchase
        assert detail.product_id == 1
        assert detail.quantity == 2
        assert detail.unit_price == Decimal('10.00')
    
    def test_detail_str(self):
        """Test string representation."""
        purchase = Purchase.objects.create(customer_id=1)
        detail = PurchaseDetail.objects.create(
            purchase=purchase,
            product_id=1,
            quantity=2,
            unit_price=Decimal('10.00')
        )
        
        expected = f"Detail for Purchase #{purchase.id} - Product 1"
        assert str(detail) == expected
    
    def test_get_subtotal(self):
        """Test subtotal calculation."""
        purchase = Purchase.objects.create(customer_id=1)
        detail = PurchaseDetail.objects.create(
            purchase=purchase,
            product_id=1,
            quantity=3,
            unit_price=Decimal('15.50')
        )
        
        subtotal = detail.get_subtotal()
        
        assert subtotal == Decimal('46.50')
    
    def test_cascade_delete(self):
        """Test that details are deleted when purchase is deleted."""
        purchase = Purchase.objects.create(customer_id=1)
        PurchaseDetail.objects.create(
            purchase=purchase,
            product_id=1,
            quantity=2,
            unit_price=Decimal('10.00')
        )
        
        purchase_id = purchase.id
        purchase.delete()
        
        # Check that details are also deleted
        assert not PurchaseDetail.objects.filter(
            purchase_id=purchase_id
        ).exists()
