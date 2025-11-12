"""
Unit tests for the payments microservice.
Tests the Payment model and API endpoints implementing the Saga pattern.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from .models import Payment


# ============================================================================
# MODEL TESTS
# ============================================================================

class PaymentModelTest(TestCase):
    """Test suite for the Payment model"""

    def setUp(self):
        """Set up test data for each test method"""
        self.payment = Payment.objects.create(
            transaction_id='TXN-TEST-001',
            order_id='ORDER-123',
            amount=Decimal('1500.50'),
            status=Payment.Status.SUCCESS,
            message='Test payment'
        )

    def test_create_payment(self):
        """Test creating a payment with all fields"""
        self.assertEqual(self.payment.transaction_id, 'TXN-TEST-001')
        self.assertEqual(self.payment.order_id, 'ORDER-123')
        self.assertEqual(self.payment.amount, Decimal('1500.50'))
        self.assertEqual(self.payment.status, Payment.Status.SUCCESS)
        self.assertEqual(self.payment.message, 'Test payment')

    def test_payment_string_representation(self):
        """Test the __str__ method returns correct format"""
        expected = "Payment TXN-TEST-001 - success"
        self.assertEqual(str(self.payment), expected)

    def test_payment_status_transitions(self):
        """Test that payment can transition between all valid statuses"""
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
        """Test that metadata field defaults to empty dictionary"""
        payment = Payment.objects.create(
            transaction_id='TXN-002',
            order_id='ORDER-456'
        )
        self.assertEqual(payment.metadata, {})
        
    def test_payment_can_store_custom_metadata(self):
        """Test storing custom data in metadata JSONField"""
        payment = Payment.objects.create(
            transaction_id='TXN-003',
            order_id='ORDER-789',
            amount=Decimal('2000.00'),
            status=Payment.Status.SUCCESS,
            metadata={
                'customer_id': '123',
                'notes': 'VIP customer',
                'payment_method': 'credit_card'
            }
        )
        self.assertEqual(payment.metadata['customer_id'], '123')
        self.assertEqual(payment.metadata['notes'], 'VIP customer')
        self.assertEqual(payment.metadata['payment_method'], 'credit_card')

    def test_transaction_id_must_be_unique(self):
        """Test that duplicate transaction_id raises IntegrityError"""
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                transaction_id='TXN-TEST-001',  # Duplicate
                order_id='ORDER-002',
                amount=Decimal('200.00')
            )

    def test_payment_can_be_compensated(self):
        """Test transitioning a payment to compensated status"""
        self.payment.status = Payment.Status.COMPENSATED
        self.payment.save()
        self.payment.refresh_from_db()
        
        self.assertEqual(self.payment.status, Payment.Status.COMPENSATED)


# ============================================================================
# API ENDPOINT TESTS
# ============================================================================

class PaymentAPITest(TestCase):
    """Test suite for Payment API endpoints (Saga pattern)"""

    def setUp(self):
        """Set up test client for each test method"""
        self.client = Client()

    # ------------------------------------------------------------------------
    # POST /payments/ - Process Payment
    # ------------------------------------------------------------------------

    def test_process_payment_returns_success_or_error(self):
        """Test POST /payments/ returns either 200 (success) or 409 (error)"""
        response = self.client.post(
            '/payments/',
            data=json.dumps({
                'user_id': 'USER-001',
                'amount': '1500.50',
                'product_id': 'PROD-001'
            }),
            content_type='application/json'
        )
        
        # Random behavior: should return either success or error
        self.assertIn(response.status_code, [200, 409])
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn(data['status'], ['success', 'error'])

    def test_process_payment_with_invalid_data(self):
        """Test POST /payments/ with invalid amount returns 400"""
        response = self.client.post(
            '/payments/',
            data=json.dumps({
                'order_id': 'ORDER-API-002',
                'amount': 'invalid'  # Invalid amount format
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)

    def test_process_payment_with_missing_user_id(self):
        """Test POST /payments/ without required user_id returns 400"""
        response = self.client.post(
            '/payments/',
            data=json.dumps({
                'amount': '1500.50',
                'product_id': 'PROD-001'
                # Missing user_id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------------
    # POST /payments/{id}/refund/ - Refund Payment (Compensation)
    # ------------------------------------------------------------------------

    def test_refund_existing_payment(self):
        """Test POST /payments/{id}/refund/ successfully refunds a payment"""
        # Create a payment first
        payment = Payment.objects.create(
            transaction_id='TXN-REFUND-001',
            order_id='ORDER-REFUND-001',
            amount=Decimal('1000.00'),
            status=Payment.Status.SUCCESS
        )
        
        # Refund it
        response = self.client.post(
            f'/payments/{payment.id}/refund/',
            data=json.dumps({
                'reason': 'Customer requested refund'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'compensated')
        
        # Verify the payment was updated in database
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.COMPENSATED)

    def test_refund_nonexistent_payment_always_succeeds(self):
        """Test POST /payments/9999/refund/ - Saga always compensates (idempotent)"""
        # In Saga pattern, compensation must always succeed to not block rollback
        response = self.client.post(
            '/payments/9999/refund/',
            data=json.dumps({
                'reason': 'Transaction rollback'
            }),
            content_type='application/json'
        )
        
        # Should return 200 even if payment doesn't exist
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'compensated')

        self.assertEqual(data['status'], 'compensated')

