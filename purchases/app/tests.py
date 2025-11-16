"""
Tests for the purchases microservice.
Tests purchase creation, cancellation, and health checks.
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


class PurchaseModelTests(TestCase):
    """Test cases for the Purchase model."""

    def setUp(self):
        self.purchase_data = {
            "transaction_id": "test-txn-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 2,
            "amount": 199.98,
            "payment_id": "pay-789",
            "status": Purchase.STATUS_SUCCESS,
        }

    def test_purchase_creation(self):
        """Test creating a purchase record."""
        purchase = Purchase.objects.create(**self.purchase_data)
        self.assertEqual(purchase.transaction_id, "test-txn-001")
        self.assertEqual(purchase.user_id, "user-123")
        self.assertEqual(purchase.quantity, 2)
        self.assertEqual(float(purchase.amount), 199.98)
        self.assertEqual(purchase.status, Purchase.STATUS_SUCCESS)

    def test_purchase_str_representation(self):
        """Test the string representation of purchase."""
        purchase = Purchase.objects.create(**self.purchase_data)
        self.assertIn("test-txn-001", str(purchase))

    def test_purchase_status_choices(self):
        """Test all purchase status choices."""
        statuses = [
            Purchase.STATUS_SUCCESS,
            Purchase.STATUS_FAILED,
            Purchase.STATUS_CANCELLED,
        ]
        for status in statuses:
            purchase = Purchase.objects.create(
                transaction_id=f"test-{status}",
                user_id="user-123",
                product_id="prod-456",
                quantity=1,
                amount=99.99,
                payment_id="pay-123",
                status=status,
            )
            self.assertEqual(purchase.status, status)

    def test_purchase_unique_transaction_id(self):
        """Test that transaction_id is unique."""
        Purchase.objects.create(**self.purchase_data)
        with self.assertRaises(Exception):
            Purchase.objects.create(**self.purchase_data)


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


class PurchaseIntegrationTests(TestCase):
    """Integration tests for the purchases service."""

    def setUp(self):
        self.client = Client()

    def test_purchase_lifecycle(self):
        """Test complete purchase lifecycle: create -> cancel."""
        # 1. Create purchase
        create_data = {
            "transaction_id": "lifecycle-test-001",
            "user_id": "user-123",
            "product_id": "prod-456",
            "quantity": 5,
            "amount": 499.95,
            "payment_id": "pay-789",
        }

        create_response = self.client.post(
            reverse("purchase-create"),
            data=json.dumps(create_data),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        purchase_id = create_response.json()["purchase_id"]

        # Verify purchase exists with success status
        purchase = Purchase.objects.get(id=purchase_id)
        self.assertEqual(purchase.status, Purchase.STATUS_SUCCESS)

        # 2. Cancel purchase
        cancel_response = self.client.delete(
            reverse("purchase-cancel", kwargs={"transaction_id": "lifecycle-test-001"})
        )

        self.assertEqual(cancel_response.status_code, 200)

        # Verify purchase was cancelled
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, Purchase.STATUS_CANCELLED)

    def test_multiple_purchases_same_user(self):
        """Test creating multiple purchases for the same user."""
        base_data = {
            "user_id": "user-multi",
            "product_id": "prod-456",
            "quantity": 1,
            "amount": 99.99,
            "payment_id": "pay-123",
        }

        for i in range(3):
            data = {**base_data, "transaction_id": f"multi-{i}"}
            response = self.client.post(
                reverse("purchase-create"),
                data=json.dumps(data),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 201)

        # Verify all 3 purchases were created
        purchases = Purchase.objects.filter(user_id="user-multi")
        self.assertEqual(purchases.count(), 3)

    def test_purchases_urls_configured(self):
        """Test that all purchase URLs are properly configured."""
        # Health check
        health_response = self.client.get(reverse("health-check"))
        self.assertNotEqual(health_response.status_code, 404)

        # Create purchase (will fail validation but URL exists)
        create_response = self.client.post(
            reverse("purchase-create"),
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertNotEqual(create_response.status_code, 404)

    def test_purchase_data_integrity(self):
        """Test that purchase data maintains integrity."""
        data = {
            "transaction_id": "integrity-test",
            "user_id": "user-integrity",
            "product_id": "prod-integrity",
            "quantity": 10,
            "amount": 999.90,
            "payment_id": "pay-integrity",
        }

        response = self.client.post(
            reverse("purchase-create"),
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        # Verify all data was saved correctly
        purchase = Purchase.objects.get(transaction_id="integrity-test")
        self.assertEqual(purchase.user_id, "user-integrity")
        self.assertEqual(purchase.product_id, "prod-integrity")
        self.assertEqual(purchase.quantity, 10)
        self.assertEqual(float(purchase.amount), 999.90)
        self.assertEqual(purchase.payment_id, "pay-integrity")
