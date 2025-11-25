"""
Tests for product views and endpoints.
"""

from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.db import DatabaseError
from products.models import Product


class RandomProductViewTests(TestCase):
    """Test cases for the random product endpoint."""

    def setUp(self):
        self.client = Client()
        self.random_product_url = reverse("random-product")

    def test_random_product_success(self):
        """Test successful random product retrieval."""
        response = self.client.get(self.random_product_url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("product_id", data)
        self.assertIn("name", data)
        self.assertIn("price", data)
        self.assertIn("category", data)
        self.assertIn("stock", data)

    def test_random_product_response_structure(self):
        """Test that the response has the correct structure."""
        response = self.client.get(self.random_product_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            "product_id",
            "name",
            "description",
            "price",
            "category",
            "stock",
        ]
        for field in required_fields:
            self.assertIn(field, data)

    def test_random_product_endpoint_exists(self):
        """Test that the random product endpoint is accessible."""
        response = self.client.get(self.random_product_url)
        # Should not return 404
        self.assertNotEqual(response.status_code, 404)

    def test_random_product_creates_when_none_exist(self):
        """Test that a product is created when none exist."""
        # Ensure no products exist
        Product.objects.all().delete()
        
        response = self.client.get(self.random_product_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify a product was created
        self.assertEqual(Product.objects.count(), 1)
        
        created_product = Product.objects.first()
        self.assertTrue(created_product.is_active)
        self.assertGreater(created_product.stock, 0)

    def test_random_product_with_existing_products(self):
        """Test random product selection from existing products."""
        # Create multiple products
        for i in range(3):
            Product.objects.create(
                name=f"Product {i}",
                description=f"Description {i}",
                price=Decimal(f"{i+10}.99"),
                category="Electronics",
                stock=10,
                is_active=True
            )
        
        response = self.client.get(self.random_product_url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Should return one of the created products
        self.assertIn("Product", data["name"])

    def test_random_product_price_is_string(self):
        """Test that price is returned as string."""
        response = self.client.get(self.random_product_url)
        data = response.json()
        
        self.assertIsInstance(data["price"], str)

    @patch('products.models.Product.objects.filter')
    def test_random_product_database_error(self, mock_filter):
        """Test handling of database errors."""
        # Mock database error
        mock_filter.side_effect = DatabaseError("Database connection failed")
        
        response = self.client.get(self.random_product_url)
        
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Database error occurred")

    @patch('products.views.Product.objects.filter')
    def test_random_product_unexpected_error(self, mock_filter):
        """Test handling of unexpected errors."""
        # Mock unexpected error
        mock_filter.side_effect = Exception("Unexpected error")
        
        response = self.client.get(self.random_product_url)
        
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Internal server error")

    def test_random_product_only_returns_active(self):
        """Test that only active products are returned."""
        # Create active and inactive products
        Product.objects.create(
            name="Active Product",
            description="Test",
            price=Decimal("99.99"),
            stock=10,
            is_active=True
        )
        Product.objects.create(
            name="Inactive Product",
            description="Test",
            price=Decimal("99.99"),
            stock=10,
            is_active=False
        )
        
        response = self.client.get(self.random_product_url)
        data = response.json()
        
        # Should return the active product
        self.assertEqual(data["name"], "Active Product")

    def test_random_product_only_returns_with_stock(self):
        """Test that only products with stock > 0 are returned."""
        # Create products with and without stock
        Product.objects.create(
            name="In Stock",
            description="Test",
            price=Decimal("99.99"),
            stock=10,
            is_active=True
        )
        Product.objects.create(
            name="Out of Stock",
            description="Test",
            price=Decimal("99.99"),
            stock=0,
            is_active=True
        )
        
        response = self.client.get(self.random_product_url)
        data = response.json()
        
        # Should return the product with stock
        self.assertEqual(data["name"], "In Stock")


class CatalogHealthCheckTests(TestCase):
    """Test cases for the catalog health check endpoint."""

    def setUp(self):
        self.client = Client()
        self.health_url = reverse("catalog-health")

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_correct_data(self):
        """Test that health check returns correct JSON data."""
        response = self.client.get(self.health_url)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "catalog")

    def test_health_check_json_format(self):
        """Test that health check returns JSON."""
        response = self.client.get(self.health_url)
        self.assertEqual(response["Content-Type"], "application/json")

