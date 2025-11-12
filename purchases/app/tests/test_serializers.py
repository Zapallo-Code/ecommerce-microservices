"""
Unit tests for Purchase Serializers (simplified Saga pattern).
"""
import pytest
from decimal import Decimal
from app.serializers import (
    PurchaseRequestSerializer,
    PurchaseSuccessResponseSerializer,
    PurchaseErrorResponseSerializer,
    CancelResponseSerializer
)


@pytest.mark.unit
class TestPurchaseRequestSerializer:
    """Tests for PurchaseRequestSerializer."""
    
    def test_valid_data(self, sample_purchase_data):
        """Test serializer with valid data."""
        serializer = PurchaseRequestSerializer(data=sample_purchase_data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['transaction_id'] == 'test-txn-001'
        assert serializer.validated_data['user_id'] == 'user-123'
        assert serializer.validated_data['product_id'] == 'prod-456'
        assert serializer.validated_data['payment_id'] == 'pay-789'
        assert serializer.validated_data['amount'] == Decimal('100.50')
    
    def test_invalid_amount_zero(self):
        """Test with zero amount."""
        data = {
            'transaction_id': 'test-001',
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 0
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors
    
    def test_invalid_amount_negative(self):
        """Test with negative amount."""
        data = {
            'transaction_id': 'test-001',
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': -50.00
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'amount' in serializer.errors
    
    def test_missing_transaction_id(self):
        """Test with missing transaction_id."""
        data = {
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 100.50
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'transaction_id' in serializer.errors
    
    def test_missing_user_id(self):
        """Test with missing user_id."""
        data = {
            'transaction_id': 'test-001',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 100.50
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'user_id' in serializer.errors


@pytest.mark.unit
class TestPurchaseSuccessResponseSerializer:
    """Tests for PurchaseSuccessResponseSerializer."""
    
    def test_serialize_success_response(self, created_purchase):
        """Test serializing successful purchase response."""
        # Mark purchase as success for this test
        created_purchase.mark_success()
        
        serializer = PurchaseSuccessResponseSerializer(created_purchase)
        
        data = serializer.data
        
        assert data['status'] == 'success'
        assert data['purchase_id'] == created_purchase.id
        assert data['transaction_id'] == created_purchase.transaction_id


@pytest.mark.unit
class TestPurchaseErrorResponseSerializer:
    """Tests for PurchaseErrorResponseSerializer."""
    
    def test_serialize_error_response(self):
        """Test serializing error response."""
        data = {
            'status': 'error',
            'message': 'Purchase failed',
            'error': 'CONFLICT'
        }
        serializer = PurchaseErrorResponseSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == 'error'
        assert serializer.validated_data['message'] == 'Purchase failed'
        assert serializer.validated_data['error'] == 'CONFLICT'


@pytest.mark.unit
class TestCancelResponseSerializer:
    """Tests for CancelResponseSerializer."""
    
    def test_serialize_cancel_response(self):
        """Test serializing cancel response."""
        data = {
            'status': 'success',
            'message': 'Purchase cancelled successfully',
            'transaction_id': 'test-txn-001'
        }
        serializer = CancelResponseSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['status'] == 'success'
        assert (serializer.validated_data['message'] ==
                'Purchase cancelled successfully')
        assert serializer.validated_data['transaction_id'] == 'test-txn-001'
