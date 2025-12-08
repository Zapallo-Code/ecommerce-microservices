from django.test import TestCase

from app.models.purchase import Purchase
from app.serializers.purchase_serializer import (
    CancelResponseSerializer,
    PurchaseErrorResponseSerializer,
    PurchaseRequestSerializer,
    PurchaseSuccessResponseSerializer,
)


class PurchaseRequestSerializerTests(TestCase):
    def test_valid_purchase_request(self):
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
        self.assertEqual(
            serializer.validated_data["transaction_id"], "txn-001"
        )
        self.assertEqual(serializer.validated_data["quantity"], 2)

    def test_missing_required_fields(self):
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
    def test_serialize_success_response(self):
        purchase = Purchase.objects.create(
            transaction_id="txn-success-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=1,
            amount=99.99,
            payment_id="pay-789",
            status=Purchase.STATUS_SUCCESS,
        )

        # The serializer expects a dict, not a model instance
        response_data = {
            "status": "success",
            "purchase_id": purchase.id,
            "transaction_id": purchase.transaction_id,
        }

        serializer = PurchaseSuccessResponseSerializer(data=response_data)
        self.assertTrue(serializer.is_valid())

        data = serializer.validated_data
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["purchase_id"], purchase.id)
        self.assertEqual(data["transaction_id"], "txn-success-001")


class PurchaseErrorResponseSerializerTests(TestCase):
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
    def test_serialize_cancel_response(self):
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
