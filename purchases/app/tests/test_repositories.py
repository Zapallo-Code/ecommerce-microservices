"""
Tests for the Purchase repository layer.
Tests data access operations and queries.
"""

from django.db.models import QuerySet
from django.test import TestCase

from app.models.purchase import Purchase
from app.repositories.purchase_repository import PurchaseRepository


class PurchaseRepositoryTests(TestCase):
    """Test cases for the PurchaseRepository."""

    def setUp(self):
        """Set up test data."""
        self.repository = PurchaseRepository()
        
        # Create test purchases
        self.purchase1 = Purchase.objects.create(
            transaction_id="repo-test-001",
            user_id="user-123",
            product_id="prod-456",
            quantity=2,
            amount=199.98,
            payment_id="pay-789",
            status=Purchase.STATUS_SUCCESS,
        )
        
        self.purchase2 = Purchase.objects.create(
            transaction_id="repo-test-002",
            user_id="user-123",
            product_id="prod-789",
            quantity=1,
            amount=99.99,
            payment_id="pay-123",
            status=Purchase.STATUS_PENDING,
        )
        
        self.purchase3 = Purchase.objects.create(
            transaction_id="repo-test-003",
            user_id="user-456",
            product_id="prod-123",
            quantity=3,
            amount=299.97,
            payment_id="pay-456",
            status=Purchase.STATUS_CANCELLED,
        )

    def test_get_by_transaction_id_found(self):
        """Test retrieving purchase by transaction ID when it exists."""
        purchase = self.repository.get_by_transaction_id("repo-test-001")
        
        self.assertIsNotNone(purchase)
        self.assertEqual(purchase.transaction_id, "repo-test-001")
        self.assertEqual(purchase.user_id, "user-123")
        self.assertEqual(purchase.product_id, "prod-456")

    def test_get_by_transaction_id_not_found(self):
        """Test retrieving purchase by transaction ID when it doesn't exist."""
        purchase = self.repository.get_by_transaction_id("nonexistent-001")
        
        self.assertIsNone(purchase)

    def test_get_by_user_single_user(self):
        """Test retrieving all purchases for a specific user."""
        purchases = self.repository.get_by_user("user-123")
        
        self.assertEqual(len(purchases), 2)
        transaction_ids = [p.transaction_id for p in purchases]
        self.assertIn("repo-test-001", transaction_ids)
        self.assertIn("repo-test-002", transaction_ids)

    def test_get_by_user_no_purchases(self):
        """Test retrieving purchases for user with no purchases."""
        purchases = self.repository.get_by_user("user-999")
        
        self.assertEqual(len(purchases), 0)

    def test_get_by_user_with_limit(self):
        """Test retrieving purchases with limit parameter."""
        # Create more purchases for user
        for i in range(5):
            Purchase.objects.create(
                transaction_id=f"repo-limit-{i}",
                user_id="user-limit",
                product_id="prod-001",
                quantity=1,
                amount=10.00,
                payment_id=f"pay-{i}",
                status=Purchase.STATUS_SUCCESS,
            )
        
        purchases = self.repository.get_by_user("user-limit", limit=3)
        
        self.assertEqual(len(purchases), 3)

    def test_get_by_user_returns_queryset(self):
        """Test that get_by_user returns a QuerySet (lazy evaluation)."""
        purchases = self.repository.get_by_user("user-123")
        
        # Should return QuerySet, not list (better performance)
        self.assertIsInstance(purchases, QuerySet)
        
        # But should be iterable and countable
        self.assertEqual(len(purchases), 2)
