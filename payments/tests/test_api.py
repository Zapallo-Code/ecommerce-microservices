"""
Integration tests for Payment API endpoints.
Tests the Saga pattern implementation.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from app.models import Payment


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
