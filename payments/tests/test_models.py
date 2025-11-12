"""
Unit tests for the Payment model.
"""
import json
from decimal import Decimal
from django.test import TestCase
from app.models import Payment


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
