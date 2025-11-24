"""
Tests for Purchase serializers.
Tests request/response serialization and validation.
"""

from decimal import Decimal
from django.test import TestCase
from app.serializers.purchase_serializer import (
    PurchaseRequestSerializer,
    PurchaseSuccessResponseSerializer,
    PurchaseErrorResponseSerializer,
    CancelResponseSerializer,
)
from app.models.purchase import Purchase


class PurchaseRequestSerializerTests(TestCase):
    """Test cases for PurchaseRequestSerializer."""

    def test_valid_purchase_request(self):
        """Test serialization of valid purchase request."""
        data = {
            "transaction_id": "txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 2,
            "payment_id": "pay-789",
            "amount": "199.98",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["transaction_id"], "txn-001")
        self.assertEqual(serializer.validated_data["quantity"], 2)

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        data = {
            "user_id": "user-123",
            "product_id": "prod-456",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("transaction_id", serializer.errors)
        self.assertIn("payment_id", serializer.errors)
        self.assertIn("amount", serializer.errors)

    def test_invalid_quantity_negative(self):
        """Test validation fails for negative quantity."""
        data = {
            "transaction_id": "txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": -1,
            "payment_id": "pay-789",
            "amount": "199.98",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_invalid_quantity_zero(self):
        """Test validation fails for zero quantity."""
        data = {
            "transaction_id": "txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 0,
            "payment_id": "pay-789",
            "amount": "199.98",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("quantity", serializer.errors)

    def test_invalid_amount_negative(self):
        """Test validation fails for negative amount."""
        data = {
            "transaction_id": "txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 1,
            "payment_id": "pay-789",
            "amount": "-50.00",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_invalid_amount_zero(self):
        """Test validation fails for zero amount."""
        data = {
            "transaction_id": "txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 1,
            "payment_id": "pay-789",
            "amount": "0.00",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_default_quantity(self):
        """Test that quantity defaults to 1 when not provided."""
        data = {
            "transaction_id": "txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "payment_id": "pay-789",
            "amount": "99.99",
        }
        
        serializer = PurchaseRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["quantity"], 1)


class PurchaseSuccessResponseSerializerTests(TestCase):
    """Test cases for PurchaseSuccessResponseSerializer."""

    def test_serialize_success_response(self):
        """Test serialization of successful purchase response."""
        purchase = Purchase.objects.create(
            transaction_id="txn-success-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=1,
            amount=99.99,
            payment_id="pay-789",
            status=Purchase.STATUS_SUCCESS,
        )
        
        serializer = PurchaseSuccessResponseSerializer(purchase)
        data = serializer.data
        
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["purchase_id"], purchase.id)
        self.assertEqual(data["transaction_id"], "txn-success-001")


class PurchaseErrorResponseSerializerTests(TestCase):
    """Test cases for PurchaseErrorResponseSerializer."""

    def test_serialize_error_response(self):
        """Test serialization of error response."""
        error_data = {
            "status": "error",
            "message": "Purchase failed",
            "error": "CONFLICT",
        }
        
        serializer = PurchaseErrorResponseSerializer(data=error_data)
        self.assertTrue(serializer.is_valid())
        
        data = serializer.validated_data
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "Purchase failed")
        self.assertEqual(data["error"], "CONFLICT")


class CancelResponseSerializerTests(TestCase):
    """Test cases for CancelResponseSerializer."""

    def test_serialize_cancel_response(self):
        """Test serialization of cancel response."""
        cancel_data = {
            "status": "success",
            "message": "Purchase cancelled successfully",
            "transaction_id": "txn-001",
        }
        
        serializer = CancelResponseSerializer(data=cancel_data)
        self.assertTrue(serializer.is_valid())
        
        data = serializer.validated_data
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Purchase cancelled successfully")
        self.assertEqual(data["transaction_id"], "txn-001")
