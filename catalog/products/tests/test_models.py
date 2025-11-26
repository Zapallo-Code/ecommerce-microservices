"""
Tests for Product model.
"""

from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from products.models import Product


class ProductModelTests(TestCase):
    """Test cases for the Product model."""

    def test_create_product(self):
        """Test creating a product with valid data."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            category="Electronics",
            stock=10,
            is_active=True
        )
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.price, Decimal("99.99"))
        self.assertEqual(product.stock, 10)
        self.assertTrue(product.is_active)

    def test_product_string_representation(self):
        """Test the string representation of a product."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99"),
            category="Electronics",
            stock=10
        )
        self.assertEqual(str(product), "Test Product")

    def test_product_default_values(self):
        """Test default values for product fields."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99")
        )
        self.assertEqual(product.category, "General")
        self.assertEqual(product.stock, 0)
        self.assertTrue(product.is_active)

    def test_product_timestamps(self):
        """Test that created_at and updated_at are set automatically."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99")
        )
        self.assertIsNotNone(product.created_at)
        self.assertIsNotNone(product.updated_at)

    def test_update_product(self):
        """Test updating a product."""
        product = Product.objects.create(
            name="Original Name",
            description="Original description",
            price=Decimal("99.99"),
            stock=10
        )
        
        original_created_at = product.created_at
        
        # Update product
        product.name = "Updated Name"
        product.stock = 5
        product.save()
        
        # Refresh from database
        product.refresh_from_db()
        
        self.assertEqual(product.name, "Updated Name")
        self.assertEqual(product.stock, 5)
        self.assertEqual(product.created_at, original_created_at)
        self.assertGreaterEqual(product.updated_at, original_created_at)

    def test_delete_product(self):
        """Test deleting a product."""
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            price=Decimal("99.99")
        )
        product_id = product.id
        product.delete()
        
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=product_id)

    def test_filter_active_products(self):
        """Test filtering active products."""
        Product.objects.create(
            name="Active Product",
            description="Test",
            price=Decimal("99.99"),
            is_active=True
        )
        Product.objects.create(
            name="Inactive Product",
            description="Test",
            price=Decimal("99.99"),
            is_active=False
        )
        
        active_products = Product.objects.filter(is_active=True)
        self.assertEqual(active_products.count(), 1)
        self.assertEqual(active_products.first().name, "Active Product")

    def test_filter_products_with_stock(self):
        """Test filtering products with stock."""
        Product.objects.create(
            name="In Stock",
            description="Test",
            price=Decimal("99.99"),
            stock=10
        )
        Product.objects.create(
            name="Out of Stock",
            description="Test",
            price=Decimal("99.99"),
            stock=0
        )
        
        in_stock = Product.objects.filter(stock__gt=0)
        self.assertEqual(in_stock.count(), 1)
        self.assertEqual(in_stock.first().name, "In Stock")

    def test_filter_products_by_category(self):
        """Test filtering products by category."""
        Product.objects.create(
            name="Electronics Item",
            description="Test",
            price=Decimal("99.99"),
            category="Electronics"
        )
        Product.objects.create(
            name="Book Item",
            description="Test",
            price=Decimal("19.99"),
            category="Books"
        )
        
        electronics = Product.objects.filter(category="Electronics")
        self.assertEqual(electronics.count(), 1)
        self.assertEqual(electronics.first().name, "Electronics Item")

    def test_product_ordering(self):
        """Test that products are ordered by created_at descending."""
        product1 = Product.objects.create(
            name="First Product",
            description="Test",
            price=Decimal("99.99")
        )
        product2 = Product.objects.create(
            name="Second Product",
            description="Test",
            price=Decimal("99.99")
        )
        
        products = Product.objects.all()
        self.assertEqual(products.first().id, product2.id)
        self.assertEqual(products.last().id, product1.id)

    def test_price_decimal_places(self):
        """Test that price accepts decimal values."""
        product = Product.objects.create(
            name="Test Product",
            description="Test",
            price=Decimal("99.99")
        )
        self.assertEqual(product.price, Decimal("99.99"))

    def test_bulk_create_products(self):
        """Test creating multiple products at once."""
        products = [
            Product(
                name=f"Product {i}",
                description=f"Description {i}",
                price=Decimal(f"{i}.99"),
                stock=i
            )
            for i in range(1, 6)
        ]
        Product.objects.bulk_create(products)
        
        self.assertEqual(Product.objects.count(), 5)
