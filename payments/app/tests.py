from django.test import TestCase
from decimal import Decimal
from .models import Payment, PaymentMethod


class PaymentMethodModelTest(TestCase):
    """Tests para el modelo PaymentMethod"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.payment_method = PaymentMethod.objects.create(
            name='Tarjeta de Crédito',
            description='Pago con tarjeta de crédito',
            is_active=True
        )

    def test_payment_method_creation(self):
        """Test: Crear un método de pago correctamente"""
        self.assertEqual(self.payment_method.name, 'Tarjeta de Crédito')
        self.assertTrue(self.payment_method.is_active)
        self.assertIsNotNone(self.payment_method.created_at)

    def test_payment_method_str(self):
        """Test: String representation del método de pago"""
        self.assertEqual(str(self.payment_method), 'Tarjeta de Crédito')

    def test_payment_method_unique_name(self):
        """Test: El nombre del método de pago debe ser único"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            PaymentMethod.objects.create(name='Tarjeta de Crédito')


class PaymentModelTest(TestCase):
    """Tests para el modelo Payment"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.payment_method = PaymentMethod.objects.create(
            name='Tarjeta de Débito',
            is_active=True
        )
        
        self.payment = Payment.objects.create(
            order_id='ORDER-123',
            amount=Decimal('1500.50'),
            currency='ARS',
            status=Payment.Status.PENDING,
            payment_method=self.payment_method
        )

    def test_payment_creation(self):
        """Test: Crear un pago correctamente"""
        self.assertEqual(self.payment.order_id, 'ORDER-123')
        self.assertEqual(self.payment.amount, Decimal('1500.50'))
        self.assertEqual(self.payment.status, Payment.Status.PENDING)
        self.assertEqual(self.payment.currency, 'ARS')

    def test_payment_str(self):
        """Test: String representation del pago"""
        expected = f"Payment {self.payment.id} - Order ORDER-123 - pending"
        self.assertEqual(str(self.payment), expected)

    def test_payment_default_status(self):
        """Test: El estado por defecto debe ser PENDING"""
        new_payment = Payment.objects.create(
            order_id='ORDER-456',
            amount=Decimal('500.00'),
            payment_method=self.payment_method
        )
        self.assertEqual(new_payment.status, Payment.Status.PENDING)

    def test_payment_is_successful(self):
        """Test: Método is_successful() funciona correctamente"""
        self.assertFalse(self.payment.is_successful())
        
        self.payment.status = Payment.Status.COMPLETED
        self.payment.save()
        
        self.assertTrue(self.payment.is_successful())

    def test_payment_can_be_refunded(self):
        """Test: Solo pagos completados pueden ser reembolsados"""
        self.assertFalse(self.payment.can_be_refunded())
        
        self.payment.status = Payment.Status.COMPLETED
        self.payment.save()
        
        self.assertTrue(self.payment.can_be_refunded())

    def test_payment_status_choices(self):
        """Test: Todos los estados posibles son válidos"""
        valid_statuses = [
            Payment.Status.PENDING,
            Payment.Status.PROCESSING,
            Payment.Status.COMPLETED,
            Payment.Status.FAILED,
            Payment.Status.REFUNDED,
            Payment.Status.CANCELLED,
        ]
        
        for status in valid_statuses:
            self.payment.status = status
            self.payment.save()
            self.assertEqual(self.payment.status, status)

    def test_payment_metadata_default(self):
        """Test: metadata debe ser un dict vacío por defecto"""
        self.assertEqual(self.payment.metadata, {})
        
    def test_payment_with_metadata(self):
        """Test: Guardar metadata adicional"""
        payment = Payment.objects.create(
            order_id='ORDER-789',
            amount=Decimal('2000.00'),
            payment_method=self.payment_method,
            metadata={'customer_id': '123', 'notes': 'VIP customer'}
        )
        self.assertEqual(payment.metadata['customer_id'], '123')

    def test_payment_transaction_id_unique(self):
        """Test: transaction_id debe ser único"""
        from django.db import IntegrityError
        
        Payment.objects.create(
            order_id='ORDER-001',
            amount=Decimal('100.00'),
            payment_method=self.payment_method,
            transaction_id='TXN-123456'
        )
        
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                order_id='ORDER-002',
                amount=Decimal('200.00'),
                payment_method=self.payment_method,
                transaction_id='TXN-123456'  # Mismo transaction_id
            )
