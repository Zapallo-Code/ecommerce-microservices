from django.test import TestCase
from products.models import Product
from products.repositories import ProductRepository


class ProductRepositoryTest(TestCase):
    def setUp(self):
        self.repository = ProductRepository()

        # Create test products
        self.product1 = Product.objects.create(
            name="Test Product 1",
            description="Description 1",
            price=10.50,
            category="Electronics",
            stock=5,
            is_active=True,
        )
        self.product2 = Product.objects.create(
            name="Test Product 2",
            description="Description 2",
            price=20.00,
            category="Books",
            stock=0,
            is_active=True,
        )
        self.product3 = Product.objects.create(
            name="Inactive Product",
            description="Description 3",
            price=15.00,
            category="Toys",
            stock=10,
            is_active=False,
        )

    def test_get_random_active_product_returns_product(self):
        product = self.repository.get_random_active_product()

        self.assertIsNotNone(product)
        self.assertTrue(product.is_active)
        self.assertGreater(product.stock, 0)
        self.assertEqual(product.id, self.product1.id)

    def test_get_random_active_product_no_products(self):
        Product.objects.all().delete()

        product = self.repository.get_random_active_product()
        self.assertIsNone(product)

    def test_get_by_id_existing_product(self):
        product = self.repository.get_by_id(self.product1.id)

        self.assertIsNotNone(product)
        self.assertEqual(product.id, self.product1.id)
        self.assertEqual(product.name, "Test Product 1")

    def test_get_by_id_non_existing_product(self):
        product = self.repository.get_by_id(99999)
        self.assertIsNone(product)

    def test_filter_active_with_stock(self):
        products = self.repository.filter_active_with_stock()

        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().id, self.product1.id)

    def test_all_returns_all_products(self):
        products = self.repository.all()
        self.assertEqual(products.count(), 3)

    def test_create_product(self):
        product = self.repository.create(
            name="New Product",
            description="New Description",
            price=25.00,
            category="Clothing",
            stock=15,
            is_active=True,
        )

        self.assertIsNotNone(product.id)
        self.assertEqual(product.name, "New Product")
        self.assertEqual(Product.objects.count(), 4)

    def test_update_product(self):
        updated_product = self.repository.update(
            self.product1, name="Updated Product", price=30.00
        )

        self.assertEqual(updated_product.id, self.product1.id)
        self.assertEqual(updated_product.name, "Updated Product")
        self.assertEqual(updated_product.price, 30.00)

        # Verify in database
        product = Product.objects.get(id=self.product1.id)
        self.assertEqual(product.name, "Updated Product")

    def test_delete_product(self):
        self.repository.delete(self.product1)

        self.assertEqual(Product.objects.count(), 2)
        self.assertIsNone(self.repository.get_by_id(self.product1.id))
