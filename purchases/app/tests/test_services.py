"""
Tests for Purchase service layer.
Tests business logic and Saga pattern implementation.
"""

from django.test import TestCase
from app.models.purchase import Purchase
from app.services.purchase_service import PurchaseService


class PurchaseServiceTests(TestCase):
    """Test cases for PurchaseService."""

    def setUp(self):
        """Set up test service."""
        self.service = PurchaseService()

    def test_create_purchase_success(self):
        """Test successful purchase creation."""
        result = self.service.create_purchase(
            transaction_id="svc-test-001",
            user_id="user-123",
            product_id="prod-456",
            payment_id="pay-789",
            amount=199.98,
            quantity=2,
        )
        
        self.assertEqual(result["status"], "success")
        self.assertIn("purchase_id", result)
        self.assertEqual(result["transaction_id"], "svc-test-001")
        
        # Verify purchase was created in database
        purchase = Purchase.objects.get(transaction_id="svc-test-001")
        self.assertEqual(purchase.user_id, "user-123")
        self.assertEqual(purchase.status, Purchase.STATUS_SUCCESS)

    def test_create_purchase_idempotency_success(self):
        """
        Test idempotent behavior with existing successful purchase.
        """
        # Create first purchase
        Purchase.objects.create(
            transaction_id="idempotent-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=1,
            amount=99.99,
            payment_id="pay-789",
            status=Purchase.STATUS_SUCCESS,
        )
        
        # Try to create again
        result = self.service.create_purchase(
            transaction_id="idempotent-001",
            user_id="user-123",
            product_id="prod-456",
            payment_id="pay-789",
            amount=99.99,
            quantity=1,
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["transaction_id"], "idempotent-001")

    def test_create_purchase_idempotency_failed(self):
        """
        Test idempotent behavior with existing failed purchase.
        """
        # Create failed purchase
        Purchase.objects.create(
            transaction_id="idempotent-failed-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=1,
            amount=99.99,
            payment_id="pay-789",
            status=Purchase.STATUS_FAILED,
        )
        
        # Try to create again
        result = self.service.create_purchase(
            transaction_id="idempotent-failed-001",
            user_id="user-123",
            product_id="prod-456",
            payment_id="pay-789",
            amount=99.99,
            quantity=1,
        )
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(
            result["message"],
            "Transaction already exists with status: failed"
        )
        self.assertEqual(result["current_status"], Purchase.STATUS_FAILED)

    def test_cancel_purchase_success(self):
        """Test successful purchase cancellation."""
        # Create purchase to cancel
        purchase = Purchase.objects.create(
            transaction_id="cancel-svc-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=1,
            amount=99.99,
            payment_id="pay-789",
            status=Purchase.STATUS_SUCCESS,
        )
        
        result = self.service.cancel_purchase("cancel-svc-001")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["transaction_id"], "cancel-svc-001")
        
        # Verify purchase was cancelled
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, Purchase.STATUS_CANCELLED)

    def test_cancel_purchase_not_found(self):
        """Test cancelling non-existent purchase (idempotent behavior)."""
        result = self.service.cancel_purchase("nonexistent-999")

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["message"], "Purchase not found or already cancelled"
        )

    def test_cancel_already_cancelled(self):
        """Test cancelling already cancelled purchase (idempotent)."""
        # Create cancelled purchase
        purchase = Purchase.objects.create(
            transaction_id="already-cancelled-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=1,
            amount=99.99,
            payment_id="pay-789",
            status=Purchase.STATUS_CANCELLED,
        )
        
        result = self.service.cancel_purchase("already-cancelled-001")
        
        self.assertEqual(result["status"], "success")
        
        # Verify status remains cancelled
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, Purchase.STATUS_CANCELLED)

    def test_is_testing_detection(self):
        """Test that service detects test environment."""
        self.assertTrue(PurchaseService._is_testing())

    def test_should_succeed_always_true_in_tests(self):
        """Test that operations always succeed in test environment."""
        # In test environment, should always return True
        for _ in range(10):
            self.assertTrue(PurchaseService._should_succeed())

    def test_simulate_latency_skipped_in_tests(self):
        """Test that latency simulation is skipped in tests."""
        import time
        
        start = time.time()
        PurchaseService._simulate_latency()
        elapsed = time.time() - start
        
        # Should be nearly instant in tests (< 10ms)
        self.assertLess(elapsed, 0.01)
