"""
Unit tests for Purchase Serializers.
"""
import pytest
from decimal import Decimal
from app.serializers import (
    PurchaseDetailSerializer,
    PurchaseDetailRequestSerializer,
    PurchaseRequestSerializer,
    PurchaseResponseSerializer,
    PurchaseListSerializer,
    CompensateRequestSerializer,
    CompensateResponseSerializer
)
from app.models import Purchase, PurchaseDetail


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseDetailSerializer:
    """Tests for PurchaseDetailSerializer."""
    
    def test_serialize_purchase_detail(self, created_purchase):
        """Test serializing a purchase detail."""
        detail = created_purchase.details.first()
        serializer = PurchaseDetailSerializer(detail)
        
        data = serializer.data
        
        assert 'id' in data
        assert data['product_id'] == detail.product_id
        assert data['quantity'] == detail.quantity
        assert Decimal(data['unit_price']) == detail.unit_price
        assert 'subtotal' in data
    
    def test_subtotal_calculation(self, created_purchase):
        """Test that subtotal is calculated correctly."""
        detail = created_purchase.details.first()
        serializer = PurchaseDetailSerializer(detail)
        
        expected_subtotal = detail.quantity * detail.unit_price
        assert Decimal(serializer.data['subtotal']) == expected_subtotal


@pytest.mark.unit
class TestPurchaseDetailRequestSerializer:
    """Tests for PurchaseDetailRequestSerializer."""
    
    def test_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'product_id': 1,
            'quantity': 2,
            'unit_price': '29.99'
        }
        serializer = PurchaseDetailRequestSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['product_id'] == 1
        assert serializer.validated_data['quantity'] == 2
        assert serializer.validated_data['unit_price'] == Decimal('29.99')
    
    def test_invalid_product_id(self):
        """Test with invalid product_id."""
        data = {
            'product_id': 0,  # Invalid: must be >= 1
            'quantity': 2,
            'unit_price': '29.99'
        }
        serializer = PurchaseDetailRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'product_id' in serializer.errors
    
    def test_invalid_quantity(self):
        """Test with invalid quantity."""
        data = {
            'product_id': 1,
            'quantity': 0,  # Invalid: must be >= 1
            'unit_price': '29.99'
        }
        serializer = PurchaseDetailRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'quantity' in serializer.errors
    
    def test_invalid_unit_price(self):
        """Test with negative unit_price."""
        data = {
            'product_id': 1,
            'quantity': 2,
            'unit_price': '-10.00'  # Invalid: must be >= 0
        }
        serializer = PurchaseDetailRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'unit_price' in serializer.errors


@pytest.mark.unit
class TestPurchaseRequestSerializer:
    """Tests for PurchaseRequestSerializer."""
    
    def test_valid_data(self, sample_purchase_data):
        """Test serializer with valid data."""
        serializer = PurchaseRequestSerializer(data=sample_purchase_data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['customer_id'] == 1
        assert len(serializer.validated_data['items']) == 2
    
    def test_invalid_customer_id(self):
        """Test with invalid customer_id."""
        data = {
            'customer_id': 0,  # Invalid
            'items': [
                {
                    'product_id': 1,
                    'quantity': 1,
                    'unit_price': '10.00'
                }
            ]
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'customer_id' in serializer.errors
    
    def test_empty_items(self):
        """Test with empty items list."""
        data = {
            'customer_id': 1,
            'items': []
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'items' in serializer.errors
    
    def test_missing_items(self):
        """Test with missing items field."""
        data = {
            'customer_id': 1
        }
        serializer = PurchaseRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'items' in serializer.errors


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseResponseSerializer:
    """Tests for PurchaseResponseSerializer."""
    
    def test_serialize_purchase(self, created_purchase):
        """Test serializing a complete purchase."""
        serializer = PurchaseResponseSerializer(created_purchase)
        
        data = serializer.data
        
        assert data['id'] == created_purchase.id
        assert data['customer_id'] == created_purchase.customer_id
        assert Decimal(data['total_amount']) == created_purchase.total_amount
        assert data['status'] == created_purchase.status
        assert data['saga_id'] == created_purchase.saga_id
        assert 'created_at' in data
        assert 'updated_at' in data
        assert 'details' in data
        assert len(data['details']) == 2
    
    def test_all_fields_read_only(self):
        """Test that all fields are read-only."""
        serializer = PurchaseResponseSerializer()
        
        for field_name in serializer.fields:
            field = serializer.fields[field_name]
            assert field.read_only


@pytest.mark.django_db
@pytest.mark.unit
class TestPurchaseListSerializer:
    """Tests for PurchaseListSerializer."""
    
    def test_serialize_purchase_list(self, created_purchase):
        """Test serializing purchase for list view."""
        serializer = PurchaseListSerializer(created_purchase)
        
        data = serializer.data
        
        assert data['id'] == created_purchase.id
        assert data['customer_id'] == created_purchase.customer_id
        assert 'items_count' in data
        assert data['items_count'] == 2
    
    def test_items_count_calculation(self, created_purchase):
        """Test items_count is calculated correctly."""
        serializer = PurchaseListSerializer(created_purchase)
        
        assert serializer.data['items_count'] == created_purchase.details.count()


@pytest.mark.unit
class TestCompensateRequestSerializer:
    """Tests for CompensateRequestSerializer."""
    
    def test_valid_with_purchase_id(self):
        """Test with valid purchase_id."""
        data = {'purchase_id': 1}
        serializer = CompensateRequestSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['purchase_id'] == 1
    
    def test_valid_with_saga_id(self):
        """Test with valid saga_id."""
        data = {'saga_id': 'test-saga-123'}
        serializer = CompensateRequestSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['saga_id'] == 'test-saga-123'
    
    def test_valid_with_both(self):
        """Test with both purchase_id and saga_id."""
        data = {
            'purchase_id': 1,
            'saga_id': 'test-saga-123'
        }
        serializer = CompensateRequestSerializer(data=data)
        
        assert serializer.is_valid()
    
    def test_invalid_without_identifiers(self):
        """Test validation fails without identifiers."""
        data = {}
        serializer = CompensateRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
    
    def test_invalid_purchase_id(self):
        """Test with invalid purchase_id."""
        data = {'purchase_id': 0}
        serializer = CompensateRequestSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'purchase_id' in serializer.errors


@pytest.mark.unit
class TestCompensateResponseSerializer:
    """Tests for CompensateResponseSerializer."""
    
    def test_serialize_success_response(self):
        """Test serializing successful compensation."""
        data = {
            'success': True,
            'status': 'cancelled',
            'purchase_id': 1,
            'saga_id': 'test-saga-123',
            'message': 'Compensated successfully'
        }
        serializer = CompensateResponseSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['success'] is True
        assert serializer.validated_data['status'] == 'cancelled'
    
    def test_serialize_error_response(self):
        """Test serializing error compensation."""
        data = {
            'success': False,
            'message': 'Purchase not found',
            'error': 'NOT_FOUND'
        }
        serializer = CompensateResponseSerializer(data=data)
        
        assert serializer.is_valid()
        assert serializer.validated_data['success'] is False
        assert 'error' in serializer.validated_data
