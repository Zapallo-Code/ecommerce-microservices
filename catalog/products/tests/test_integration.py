"""
Integration tests for the catalog service.
"""

from django.test import TestCase, Client
from django.urls import reverse


class CatalogIntegrationTests(TestCase):
    """Integration tests for the catalog service."""

    def setUp(self):
        self.client = Client()

    def test_catalog_urls_are_configured(self):
        """Test that all catalog URLs are properly configured."""
        # Health check URL
        health_response = self.client.get(reverse("catalog-health"))
        self.assertNotEqual(health_response.status_code, 404)

        # Random product URL
        random_response = self.client.get(reverse("random-product"))
        self.assertNotEqual(random_response.status_code, 404)

    def test_catalog_returns_json_responses(self):
        """Test that all endpoints return JSON responses."""
        health_response = self.client.get(reverse("catalog-health"))
        self.assertEqual(health_response["Content-Type"], "application/json")

        # Note: random-product might fail but should still return JSON
        random_response = self.client.get(reverse("random-product"))
        self.assertEqual(random_response["Content-Type"], "application/json")
