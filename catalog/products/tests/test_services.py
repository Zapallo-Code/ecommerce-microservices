from unittest.mock import Mock, MagicMock
from django.test import TestCase
from django.db.utils import DatabaseError
from products.models import Product
from products.services import ProductService
from products.repositories import IProductRepository


class ProductServiceTest(TestCase):
    def setUp(self):
        self.mock_repository = Mock(spec=IProductRepository)
        self.service = ProductService(repository=self.mock_repository)

    def test_get_random_product_success(self):
        # Create mock product
        mock_product = Mock(spec=Product)
        mock_product.id = 1
        mock_product.name = "Test Product"
        mock_product.price = 10.50

        self.mock_repository.get_random_active_product.return_value = mock_product

        # Call service
        product = self.service.get_random_product()

        # Verify
        self.assertIsNotNone(product)
        self.assertEqual(product.id, 1)
        self.assertEqual(product.name, "Test Product")
        self.mock_repository.get_random_active_product.assert_called_once()

    def test_get_random_product_no_products(self):
        self.mock_repository.get_random_active_product.return_value = None

        product = self.service.get_random_product()

        self.assertIsNone(product)
        self.mock_repository.get_random_active_product.assert_called_once()

    def test_get_random_product_database_error(self):
        self.mock_repository.get_random_active_product.side_effect = DatabaseError(
            "DB connection failed"
        )

        with self.assertRaises(DatabaseError):
            self.service.get_random_product()

    def test_get_random_product_unexpected_error(self):
        self.mock_repository.get_random_active_product.side_effect = Exception(
            "Unexpected error"
        )

        with self.assertRaises(Exception):
            self.service.get_random_product()

    def test_service_uses_default_repository(self):
        service = ProductService()
        self.assertIsNotNone(service.repository)
