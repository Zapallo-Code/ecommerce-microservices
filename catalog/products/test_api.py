"""
API tests for the products endpoints
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from products.models import Product


class ProductAPITest(TestCase):
    """Test cases for the Product API endpoints"""
    
    def setUp(self):
        """Set up test client and initial data"""
        self.client = APIClient()
        self.product1 = Product.objects.create(
            name="Laptop Dell XPS 15",
            description="High performance laptop",
            price=Decimal("1500.00"),
            category="Computing",
            stock=10,
            is_active=True
        )
        self.product2 = Product.objects.create(
            name="iPhone 15 Pro",
            description="Latest iPhone model",
            price=Decimal("999.99"),
            category="Electronics",
            stock=5,
            is_active=True
        )
        self.product3 = Product.objects.create(
            name="Out of Stock Product",
            description="This product has no stock",
            price=Decimal("500.00"),
            category="Electronics",
            stock=0,
            is_active=True
        )
    
    def test_get_all_products(self):
        """Test retrieving all products"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # REST Framework uses pagination, so check 'results' key
        self.assertEqual(len(response.data['results']), 3)
    
    def test_get_single_product(self):
        """Test retrieving a single product by ID"""
        response = self.client.get(f'/api/products/{self.product1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Laptop Dell XPS 15")
        self.assertEqual(response.data['category'], "Computing")
    
    def test_create_product(self):
        """Test creating a new product"""
        data = {
            'name': 'Samsung Galaxy S24',
            'description': 'Latest Samsung flagship',
            'price': '899.99',
            'category': 'Electronics',
            'stock': 15,
            'is_active': True
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 4)
        self.assertEqual(response.data['name'], 'Samsung Galaxy S24')
    
    def test_create_product_invalid_data(self):
        """Test creating a product with invalid data"""
        data = {
            'name': '',  # Empty name should fail
            'description': 'Test',
            'price': 'invalid_price',  # Invalid price
            'category': 'Test'
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_update_product(self):
        """Test updating an existing product"""
        data = {
            'name': 'Updated Laptop Name',
            'description': 'Updated description',
            'price': '1600.00',
            'category': 'Computing',
            'stock': 8,
            'is_active': True
        }
        response = self.client.put(
            f'/api/products/{self.product1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Updated Laptop Name')
        self.assertEqual(self.product1.price, Decimal('1600.00'))
    
    def test_partial_update_product(self):
        """Test partially updating a product"""
        data = {'stock': 20}
        response = self.client.patch(
            f'/api/products/{self.product1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 20)
        # Other fields should remain unchanged
        self.assertEqual(self.product1.name, 'Laptop Dell XPS 15')
    
    def test_delete_product(self):
        """Test deleting a product"""
        response = self.client.delete(f'/api/products/{self.product1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_filter_products_by_category(self):
        """Test filtering products by category"""
        response = self.client.get('/api/products/?category=Electronics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return product2 and product3
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_available_products(self):
        """Test filtering only available products (stock > 0)"""
        response = self.client.get('/api/products/?available=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only products with stock > 0
        for product in response.data['results']:
            self.assertGreater(product['stock'], 0)
    
    def test_search_products_by_name(self):
        """Test searching products by name"""
        response = self.client.get('/api/products/?search=laptop')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        # Results should contain 'laptop' in the name (case-insensitive)
    
    def test_product_not_found(self):
        """Test requesting a non-existent product"""
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_deactivate_product(self):
        """Test deactivating a product"""
        data = {'is_active': False}
        response = self.client.patch(
            f'/api/products/{self.product1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product1.refresh_from_db()
        self.assertFalse(self.product1.is_active)
        self.assertFalse(self.product1.is_available)
