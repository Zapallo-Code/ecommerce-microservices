"""
Unit tests for Product model
"""
from django.test import TestCase
from decimal import Decimal
from products.models import Product


class ProductModelTest(TestCase):
    """Test cases for the Product model"""
    
    def setUp(self):
        """Set up test data"""
        self.product = Product.objects.create(
            name="Test Laptop",
            description="High performance laptop for testing",
            price=Decimal("1500.00"),
            category="Computing",
            stock=10,
            is_active=True
        )
    
    def test_product_creation(self):
        """Test that a product is created correctly"""
        self.assertEqual(self.product.name, "Test Laptop")
        self.assertEqual(self.product.description, "High performance laptop for testing")
        self.assertEqual(self.product.price, Decimal("1500.00"))
        self.assertEqual(self.product.category, "Computing")
        self.assertEqual(self.product.stock, 10)
        self.assertTrue(self.product.is_active)
    
    def test_product_str_representation(self):
        """Test the string representation of a product"""
        self.assertEqual(str(self.product), "Test Laptop")
    
    def test_product_is_available_with_stock(self):
        """Test that product is available when active and has stock"""
        self.assertTrue(self.product.is_available)
    
    def test_product_not_available_without_stock(self):
        """Test that product is not available when stock is 0"""
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available)
    
    def test_product_not_available_when_inactive(self):
        """Test that product is not available when inactive"""
        self.product.is_active = False
        self.product.save()
        self.assertFalse(self.product.is_available)
    
    def test_product_default_values(self):
        """Test default values for product fields"""
        product = Product.objects.create(
            name="Simple Product",
            description="Test product",
            price=Decimal("100.00")
        )
        self.assertEqual(product.category, "General")
        self.assertEqual(product.stock, 0)
        self.assertTrue(product.is_active)
    
    def test_product_timestamps(self):
        """Test that timestamps are set automatically"""
        self.assertIsNotNone(self.product.created_at)
        self.assertIsNotNone(self.product.updated_at)
    
    def test_product_price_decimal_places(self):
        """Test that price handles decimal places correctly"""
        product = Product.objects.create(
            name="Precision Product",
            description="Test",
            price=Decimal("99.99"),
            category="Test"
        )
        self.assertEqual(product.price, Decimal("99.99"))
