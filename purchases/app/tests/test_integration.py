import json

from django.test import Client, TestCase
from django.urls import reverse

from app.models.purchase import Purchase


class PurchaseIntegrationTests(TestCase):  # noqa: D101
    def setUp(self):  # noqa: D102
        self.client = Client()

    def test_purchase_lifecycle(self):  # noqa: D102
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
            reverse(
                "purchase-cancel",
                kwargs={"transaction_id": "lifecycle-test-001"},
            )
        )

        self.assertEqual(cancel_response.status_code, 200)

        # Verify purchase was cancelled
        purchase.refresh_from_db()
        self.assertEqual(purchase.status, Purchase.STATUS_CANCELLED)

    def test_multiple_purchases_same_user(self):  # noqa: D102
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

    def test_purchases_urls_configured(self):  # noqa: D102
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

    def test_purchase_data_integrity(self):  # noqa: D102
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
