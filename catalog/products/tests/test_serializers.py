"""
Tests for product serializers.
"""

from decimal import Decimal
from django.test import TestCase
from products.models import Product
from products.serializers import ProductSerializer, ProductRandomSerializer


class ProductSerializerTests(TestCase):
    """Test cases for ProductSerializer."""

    def setUp(self):
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test description',
            'price': Decimal('99.99'),
            'category': 'Electronics',
            'stock': 10
        }
        self.product = Product.objects.create(**self.product_data)

    def test_serializer_contains_expected_fields(self):
        """Test that serializer contains all expected fields."""
        serializer = ProductSerializer(instance=self.product)
        data = serializer.data
        
        expected_fields = {'product_id', 'name', 'description', 'price', 'category', 'stock'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_product_id_field(self):
        """Test that product_id is mapped from id."""
        serializer = ProductSerializer(instance=self.product)
        self.assertEqual(serializer.data['product_id'], self.product.id)

    def test_serializer_price_as_string(self):
        """Test that price is returned as string with proper formatting."""
        serializer = ProductSerializer(instance=self.product)
        # ProductSerializer uses coerce_to_string=True
        self.assertEqual(serializer.data['price'], '99.99')

    def test_serializer_with_multiple_products(self):
        """Test serializer with multiple products."""
        Product.objects.create(
            name='Product 2',
            description='Description 2',
            price=Decimal('49.99'),
            category='Books',
            stock=5
        )
        
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        
        self.assertEqual(len(serializer.data), 2)

    def test_serializer_read_only_fields(self):
        """Test that product_id is read-only."""
        serializer = ProductSerializer(instance=self.product)
        # product_id should be in read_only_fields
        self.assertIn('product_id', serializer.Meta.read_only_fields)


class ProductRandomSerializerTests(TestCase):
    """Test cases for ProductRandomSerializer."""

    def setUp(self):
        self.product = Product.objects.create(
            name='Random Product',
            description='Random description',
            price=Decimal('79.99'),
            category='Electronics',
            stock=15
        )

    def test_random_serializer_contains_expected_fields(self):
        """Test that random serializer contains all expected fields."""
        serializer = ProductRandomSerializer(instance=self.product)
        data = serializer.data
        
        expected_fields = {'product_id', 'name', 'description', 'price', 'category', 'stock'}
        self.assertEqual(set(data.keys()), expected_fields)

    def test_random_serializer_product_id_mapping(self):
        """Test that product_id is correctly mapped from id."""
        serializer = ProductRandomSerializer(instance=self.product)
        self.assertEqual(serializer.data['product_id'], self.product.id)

    def test_random_serializer_price_as_string(self):
        """Test that price is converted to string in to_representation."""
        serializer = ProductRandomSerializer(instance=self.product)
        # ProductRandomSerializer overrides to_representation to convert price to string
        self.assertIsInstance(serializer.data['price'], str)
        self.assertEqual(serializer.data['price'], '79.99')

    def test_random_serializer_with_decimal_price(self):
        """Test random serializer with various decimal prices."""
        test_cases = [
            (Decimal('10.00'), '10.00'),
            (Decimal('99.99'), '99.99'),
            (Decimal('1.50'), '1.50'),
            (Decimal('100'), '100.00'),
        ]
        
        for price_value, expected_string in test_cases:
            product = Product.objects.create(
                name='Test',
                description='Test',
                price=price_value,
                stock=10
            )
            serializer = ProductRandomSerializer(instance=product)
            self.assertEqual(serializer.data['price'], expected_string)
            product.delete()

    def test_random_serializer_all_fields_present(self):
        """Test that all fields are properly serialized."""
        serializer = ProductRandomSerializer(instance=self.product)
        data = serializer.data
        
        self.assertEqual(data['product_id'], self.product.id)
        self.assertEqual(data['name'], 'Random Product')
        self.assertEqual(data['description'], 'Random description')
        self.assertEqual(data['price'], '79.99')
        self.assertEqual(data['category'], 'Electronics')
        self.assertEqual(data['stock'], 15)

    def test_serializer_with_inactive_product(self):
        """Test serializer with inactive product."""
        inactive_product = Product.objects.create(
            name='Inactive Product',
            description='Test',
            price=Decimal('50.00'),
            stock=0,
            is_active=False
        )
        
        serializer = ProductRandomSerializer(instance=inactive_product)
        # Serializer should still work, just serialize the data
        self.assertEqual(serializer.data['name'], 'Inactive Product')
        self.assertEqual(serializer.data['stock'], 0)
