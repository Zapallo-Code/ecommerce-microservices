import json
from decimal import Decimal
from django.test import TestCase, Client
from .models import Payment


class PaymentModelTest(TestCase):
    def setUp(self):
        self.payment = Payment.objects.create(
            transaction_id="TXN-TEST-001",
            amount=Decimal("1500.50"),
            status=Payment.Status.SUCCESS,
            message="Test payment",
        )

    def test_create_payment(self):
        self.assertEqual(self.payment.transaction_id, "TXN-TEST-001")
        self.assertEqual(self.payment.amount, Decimal("1500.50"))
        self.assertEqual(self.payment.status, Payment.Status.SUCCESS)
        self.assertEqual(self.payment.message, "Test payment")

    def test_payment_string_representation(self):
        expected = "Payment TXN-TEST-001 - success"
        self.assertEqual(str(self.payment), expected)

    def test_payment_status_transitions(self):
        valid_statuses = [
            Payment.Status.SUCCESS,
            Payment.Status.ERROR,
            Payment.Status.COMPENSATED,
        ]

        for status in valid_statuses:
            self.payment.status = status
            self.payment.save()
            self.payment.refresh_from_db()
            self.assertEqual(self.payment.status, status)

    def test_payment_metadata_defaults_to_empty_dict(self):
        payment = Payment.objects.create(
            transaction_id="TXN-002",
        )
        self.assertEqual(payment.metadata, {})

    def test_payment_can_store_custom_metadata(self):
        payment = Payment.objects.create(
            transaction_id="TXN-003",
            amount=Decimal("2000.00"),
            status=Payment.Status.SUCCESS,
            metadata={
                "customer_id": "123",
                "notes": "VIP customer",
                "payment_method": "credit_card",
            },
        )
        self.assertEqual(payment.metadata["customer_id"], "123")
        self.assertEqual(payment.metadata["notes"], "VIP customer")
        self.assertEqual(payment.metadata["payment_method"], "credit_card")

    def test_transaction_id_must_be_unique(self):
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                transaction_id="TXN-TEST-001",  # Duplicate
                amount=Decimal("200.00"),
            )

    def test_payment_can_be_compensated(self):
        self.payment.status = Payment.Status.COMPENSATED
        self.payment.save()
        self.payment.refresh_from_db()

        self.assertEqual(self.payment.status, Payment.Status.COMPENSATED)


class PaymentAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_process_payment_returns_success_or_error(self):
        response = self.client.post(
            "/payments/",
            data=json.dumps(
                {"user_id": "USER-001", "amount": "1500.50", "product_id": "PROD-001"}
            ),
            content_type="application/json",
        )

        # Random behavior: should return either success or error
        self.assertIn(response.status_code, [200, 409])

        data = response.json()
        self.assertIn("status", data)
        self.assertIn(data["status"], ["success", "error"])

    def test_process_payment_with_invalid_data(self):
        response = self.client.post(
            "/payments/",
            data=json.dumps(
                {
                    "amount": "invalid"  # Invalid amount format
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_process_payment_with_missing_user_id(self):
        response = self.client.post(
            "/payments/",
            data=json.dumps(
                {
                    "amount": "1500.50",
                    "product_id": "PROD-001",
                    # Missing user_id
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_refund_existing_payment(self):
        # Create a payment first
        payment = Payment.objects.create(
            transaction_id="TXN-REFUND-001",
            amount=Decimal("1000.00"),
            status=Payment.Status.SUCCESS,
        )

        # Refund it
        response = self.client.post(
            f"/payments/{payment.id}/refund/",
            data=json.dumps({"reason": "Customer requested refund"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "compensated")

        # Verify the payment was updated in database
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.COMPENSATED)

    def test_refund_nonexistent_payment_always_succeeds(self):
        # In Saga pattern, compensation must always succeed to not block rollback
        response = self.client.post(
            "/payments/9999/refund/",
            data=json.dumps({"reason": "Transaction rollback"}),
            content_type="application/json",
        )

        # Should return 200 even if payment doesn't exist
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "compensated")

        self.assertEqual(data["status"], "compensated")
