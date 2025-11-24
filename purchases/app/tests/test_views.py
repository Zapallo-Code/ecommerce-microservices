"""
Tests for purchase views and API endpoints.
Tests purchase creation and cancellation endpoints.
"""

from django.test import TestCase, Client
from django.urls import reverse
from app.models.purchase import Purchase
import json


class PurchaseHealthCheckTests(TestCase):
    """Test cases for the purchases health check endpoint."""

    def setUp(self):
        self.client = Client()
        self.health_url = reverse("health-check")

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_correct_data(self):
        """Test that health check returns correct JSON data."""
        response = self.client.get(self.health_url)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "purchases")


class PurchaseCreateViewTests(TestCase):
    """Test cases for the purchase creation endpoint."""

    def setUp(self):
        self.client = Client()
        self.create_url = reverse("purchase-create")

    def test_create_purchase_success(self):
        """Test successful purchase creation."""
        data = {
            "transaction_id": "create-test-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 3,
            "amount": 299.97,
            "payment_id": "pay-789",
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertIn("purchase_id", response_data)
        self.assertEqual(response_data["transaction_id"], "create-test-001")

        # Verify purchase was saved to database
        purchase = Purchase.objects.get(transaction_id="create-test-001")
        self.assertEqual(purchase.status, Purchase.STATUS_SUCCESS)
        self.assertEqual(purchase.quantity, 3)

    def test_create_purchase_missing_fields(self):
        """Test purchase creation with missing required fields."""
        # Missing transaction_id
        data = {
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 1,
            "amount": 99.99,
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data["status"], "error")

    def test_create_purchase_invalid_quantity(self):
        """Test purchase creation with invalid quantity."""
        data = {
            "transaction_id": "invalid-qty-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": -1,  # Negative quantity
            "amount": 99.99,
            "payment_id": "pay-123",
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_create_purchase_invalid_amount(self):
        """Test purchase creation with invalid amount."""
        data = {
            "transaction_id": "invalid-amt-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 1,
            "amount": -50.00,  # Negative amount
            "payment_id": "pay-123",
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_create_purchase_duplicate_transaction(self):
        """Test creating purchase with duplicate transaction_id (idempotency)."""
        data = {
            "transaction_id": "duplicate-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 1,
            "amount": 99.99,
            "payment_id": "pay-123",
        }

        # First creation
        response1 = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 201)

        # Second creation with same transaction_id (should be idempotent)
        response2 = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type="application/json",
        )
        # SAGA pattern: should return same response for idempotency
        self.assertEqual(response2.status_code, 201)


class PurchaseCancelViewTests(TestCase):
    """Test cases for the purchase cancellation endpoint."""

    def setUp(self):
        self.client = Client()
        self.purchase = Purchase.objects.create(
            transaction_id="cancel-test-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=2,
            amount=199.98,
            payment_id="pay-789",
            status=Purchase.STATUS_SUCCESS,
        )

    def test_cancel_purchase_success(self):
        """Test successful purchase cancellation."""
        cancel_url = reverse(
            "purchase-cancel", kwargs={"transaction_id": "cancel-test-001"}
        )

        response = self.client.delete(cancel_url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["message"], "Purchase cancelled successfully")
        self.assertEqual(response_data["transaction_id"], "cancel-test-001")

        # Verify purchase status was updated
        self.purchase.refresh_from_db()
        self.assertEqual(self.purchase.status, Purchase.STATUS_CANCELLED)

    def test_cancel_nonexistent_purchase(self):
        """Test cancelling a non-existent purchase."""
        cancel_url = reverse(
            "purchase-cancel", kwargs={"transaction_id": "nonexistent-999"}
        )

        response = self.client.delete(cancel_url)

        # Should return 200 OK for idempotency (SAGA pattern)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")

    def test_cancel_already_cancelled_purchase(self):
        """Test cancelling an already cancelled purchase."""
        # First cancellation
        self.purchase.status = Purchase.STATUS_CANCELLED
        self.purchase.save()

        cancel_url = reverse(
            "purchase-cancel", kwargs={"transaction_id": "cancel-test-001"}
        )

        response = self.client.delete(cancel_url)

        # Should still succeed (idempotent)
        self.assertEqual(response.status_code, 200)

    def test_cancel_failed_purchase(self):
        """Test cancelling a failed purchase."""
        self.purchase.status = Purchase.STATUS_FAILED
        self.purchase.save()

        cancel_url = reverse(
            "purchase-cancel", kwargs={"transaction_id": "cancel-test-001"}
        )

        response = self.client.delete(cancel_url)

        # Should succeed
        self.assertEqual(response.status_code, 200)

        # Verify status is now cancelled
        self.purchase.refresh_from_db()
        self.assertEqual(self.purchase.status, Purchase.STATUS_CANCELLED)
