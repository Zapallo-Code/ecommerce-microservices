"""
Tests for product views and endpoints.
"""

from django.test import TestCase, Client
from django.urls import reverse


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
