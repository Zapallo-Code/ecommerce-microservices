from django.test import TestCase

from app.models.purchase import Purchase


class PurchaseModelTests(TestCase):
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
        purchase = Purchase.objects.create(**self.purchase_data)
        self.assertEqual(purchase.transaction_id, "test-txn-001")
        self.assertEqual(purchase.user_id, "user-123")
        self.assertEqual(purchase.quantity, 2)
        self.assertEqual(float(purchase.amount), 199.98)
        self.assertEqual(purchase.status, Purchase.STATUS_SUCCESS)

    def test_purchase_str_representation(self):
        purchase = Purchase.objects.create(**self.purchase_data)
        self.assertIn("test-txn-001", str(purchase))

    def test_purchase_status_choices(self):
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
        Purchase.objects.create(**self.purchase_data)
        with self.assertRaises(Exception):
            Purchase.objects.create(**self.purchase_data)
