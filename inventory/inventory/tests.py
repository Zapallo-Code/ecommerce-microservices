"""
Tests for the inventory microservice.
Tests inventory decrease operations and health checks.
"""

from django.test import TestCase, Client
from django.urls import reverse
from inventory.models import Inventory
import json


class InventoryHealthCheckTests(TestCase):
    """Test cases for the inventory health check endpoint."""

    def setUp(self):
        self.client = Client()
        self.health_url = reverse("health-check")

    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = self.client.get(self.health_url)
        self.assertEqual(response.status_code, 200)

    def test_health_check_returns_correct_data(self):
        """Test that health check returns correct JSON data."""
        response = self.client.get(self.health_url)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "inventory")
        self.assertEqual(data["version"], "1.0.0")


class InventoryModelTests(TestCase):
    """Test cases for the Inventory model."""

    def setUp(self):
        self.inventory = Inventory.objects.create(product_id="TEST-001", stock=100)

    def test_inventory_creation(self):
        """Test creating an inventory record."""
        self.assertEqual(self.inventory.product_id, "TEST-001")
        self.assertEqual(self.inventory.stock, 100)

    def test_inventory_str_representation(self):
        """Test the string representation of inventory."""
        expected = "Product TEST-001: 100 units"
        self.assertEqual(str(self.inventory), expected)

    def test_inventory_unique_product_id(self):
        """Test that product_id is unique."""
        with self.assertRaises(Exception):
            Inventory.objects.create(product_id="TEST-001", stock=50)


class DecreaseInventoryViewTests(TestCase):
    """Test cases for the decrease inventory endpoint."""

    def setUp(self):
        self.client = Client()
        self.decrease_url = reverse("decrease-inventory")
        self.inventory = Inventory.objects.create(product_id="1", stock=100)

    def test_decrease_inventory_success(self):
        """Test successful inventory decrease."""
        data = {"product_id": "1", "quantity": 10}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data["message"], "Inventory decreased successfully")
        self.assertEqual(response_data["product_id"], "1")
        self.assertEqual(response_data["quantity"], 10)
        self.assertEqual(response_data["previous_stock"], 100)
        self.assertEqual(response_data["current_stock"], 90)

        # Verify database was updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 90)

    def test_decrease_inventory_insufficient_stock(self):
        """Test decreasing inventory with insufficient stock."""
        data = {"product_id": "1", "quantity": 150}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        response_data = response.json()

        self.assertEqual(response_data["status"], "error")
        self.assertIn("Insufficient stock", response_data["message"])

        # Verify stock was not changed
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 100)

    def test_decrease_inventory_product_not_found(self):
        """Test decreasing inventory for non-existent product creates it with default stock."""
        data = {"product_id": "999", "quantity": 10}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        # Service uses get_or_create, so new products are created with stock 100
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data["product_id"], "999")
        self.assertEqual(response_data["previous_stock"], 100)
        self.assertEqual(response_data["current_stock"], 90)
        self.assertEqual(response_data["message"], "Inventory decreased successfully")

    def test_decrease_inventory_invalid_quantity(self):
        """Test decreasing inventory with invalid quantity."""
        data = {"product_id": "1", "quantity": -5}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data["status"], "error")

    def test_decrease_inventory_missing_fields(self):
        """Test decreasing inventory with missing required fields."""
        # Missing quantity - should default to 1 and succeed
        data = {"product_id": "1"}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["quantity"], 1)

        # Missing product_id - should fail
        data = {"quantity": 10}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_decrease_inventory_zero_quantity(self):
        """Test decreasing inventory with zero quantity."""
        data = {"product_id": "1", "quantity": 0}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_decrease_inventory_with_transaction_id(self):
        """Test decreasing inventory with transaction ID."""
        data = {"product_id": "1", "quantity": 5, "transaction_id": "test-txn-123"}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("operation_id", response_data)

    def test_decrease_inventory_includes_latency(self):
        """Test that response includes latency information."""
        data = {"product_id": "1", "quantity": 5}
        response = self.client.post(
            self.decrease_url,
            data=json.dumps(data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("latency_seconds", response_data)
        # In test environment, latency is 0.0
        self.assertEqual(response_data["latency_seconds"], 0.0)


class InventoryIntegrationTests(TestCase):
    """Integration tests for the inventory service."""

    def setUp(self):
        self.client = Client()
        Inventory.objects.create(product_id="1", stock=100)
        Inventory.objects.create(product_id="2", stock=50)

    def test_multiple_decreases_on_same_product(self):
        """Test multiple decrease operations on the same product."""
        data = {"product_id": "1", "quantity": 10}

        # First decrease
        response1 = self.client.post(
            reverse("decrease-inventory"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.json()["current_stock"], 90)

        # Second decrease
        response2 = self.client.post(
            reverse("decrease-inventory"),
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()["current_stock"], 80)

        # Verify final stock
        inventory = Inventory.objects.get(product_id="1")
        self.assertEqual(inventory.stock, 80)

    def test_concurrent_product_operations(self):
        """Test operations on different products."""
        data1 = {"product_id": "1", "quantity": 20}
        data2 = {"product_id": "2", "quantity": 15}

        response1 = self.client.post(
            reverse("decrease-inventory"),
            data=json.dumps(data1),
            content_type="application/json",
        )
        response2 = self.client.post(
            reverse("decrease-inventory"),
            data=json.dumps(data2),
            content_type="application/json",
        )

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Verify both products updated correctly
        inv1 = Inventory.objects.get(product_id="1")
        inv2 = Inventory.objects.get(product_id="2")
        self.assertEqual(inv1.stock, 80)
        self.assertEqual(inv2.stock, 35)

    def test_inventory_urls_configured(self):
        """Test that all inventory URLs are properly configured."""
        health_response = self.client.get(reverse("health-check"))
        self.assertNotEqual(health_response.status_code, 404)

        decrease_response = self.client.post(
            reverse("decrease-inventory"),
            data=json.dumps({"product_id": "1", "quantity": 1}),
            content_type="application/json",
        )
        self.assertNotEqual(decrease_response.status_code, 404)
