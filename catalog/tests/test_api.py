"""
Tests para los endpoints de la API del microservicio de Catálogo
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from products.models import Product
import json


class ProductAPITest(TestCase):
    """Tests para los endpoints de productos"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        
        # Crear productos de prueba
        self.product1 = Product.objects.create(
            name='Laptop HP',
            description='Laptop de prueba',
            price=Decimal('899.99'),
            category='Computadoras',
            stock=10,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            name='Mouse Logitech',
            description='Mouse inalámbrico',
            price=Decimal('29.99'),
            category='Accesorios',
            stock=50,
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            name='Teclado Mecánico',
            description='Teclado mecánico RGB',
            price=Decimal('79.99'),
            category='Accesorios',
            stock=0,
            is_active=True
        )
    
    def test_list_products(self):
        """Test GET /api/products/ - Listar productos"""
        response = self.client.get('/api/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_retrieve_product(self):
        """Test GET /api/products/{id}/ - Obtener un producto específico"""
        response = self.client.get(f'/api/products/{self.product1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Laptop HP')
        self.assertEqual(Decimal(response.data['price']), Decimal('899.99'))
    
    def test_create_product(self):
        """Test POST /api/products/ - Crear un producto"""
        data = {
            'name': 'Nuevo Producto',
            'description': 'Descripción del nuevo producto',
            'price': '149.99',
            'category': 'Test',
            'stock': 20,
            'is_active': True
        }
        
        response = self.client.post('/api/products/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Nuevo Producto')
        self.assertEqual(Product.objects.count(), 4)
    
    def test_update_product(self):
        """Test PUT /api/products/{id}/ - Actualizar un producto"""
        data = {
            'name': 'Laptop HP Actualizada',
            'description': 'Descripción actualizada',
            'price': '999.99',
            'category': 'Computadoras',
            'stock': 15,
            'is_active': True
        }
        
        response = self.client.put(
            f'/api/products/{self.product1.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Laptop HP Actualizada')
        
        # Verificar en la base de datos
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.name, 'Laptop HP Actualizada')
    
    def test_partial_update_product(self):
        """Test PATCH /api/products/{id}/ - Actualizar parcialmente un producto"""
        data = {'stock': 25}
        
        response = self.client.patch(
            f'/api/products/{self.product1.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stock'], 25)
        self.assertEqual(response.data['name'], 'Laptop HP')  # No cambió
    
    def test_delete_product(self):
        """Test DELETE /api/products/{id}/ - Eliminar un producto"""
        response = self.client.delete(f'/api/products/{self.product1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 2)
        
        # Verificar que no existe
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=self.product1.id)
    
    def test_filter_by_category(self):
        """Test filtrar productos por categoría"""
        response = self.client.get('/api/products/?category=Accesorios')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_by_is_active(self):
        """Test filtrar productos por estado activo"""
        # Crear un producto inactivo
        Product.objects.create(
            name='Producto Inactivo',
            description='Test',
            price=Decimal('50.00'),
            is_active=False
        )
        
        response = self.client.get('/api/products/?is_active=true')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_search_products(self):
        """Test buscar productos por nombre o descripción"""
        response = self.client.get('/api/products/?search=Laptop')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_low_stock_action(self):
        """Test GET /api/products/low_stock/ - Productos con stock bajo"""
        # Crear producto con stock bajo
        Product.objects.create(
            name='Producto Stock Bajo',
            description='Test',
            price=Decimal('10.00'),
            stock=5,
            is_active=True
        )
        
        response = self.client.get('/api/products/low_stock/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_out_of_stock_action(self):
        """Test GET /api/products/out_of_stock/ - Productos sin stock"""
        response = self.client.get('/api/products/out_of_stock/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # product3 tiene stock=0
    
    def test_random_product_action(self):
        """Test GET /api/products/random/ - Producto aleatorio"""
        response = self.client.get('/api/products/random/')
        
        # Puede ser 200 (éxito) o 500 (error simulado)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])
        
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('product_id', response.data)
            self.assertIn('name', response.data)
            self.assertIn('price', response.data)
    
    def test_create_product_invalid_price(self):
        """Test crear producto con precio inválido"""
        data = {
            'name': 'Producto Inválido',
            'description': 'Test',
            'price': '-10.00',  # Precio negativo
            'category': 'Test',
            'stock': 10
        }
        
        response = self.client.post('/api/products/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_product_invalid_stock(self):
        """Test crear producto con stock inválido"""
        data = {
            'name': 'Producto Inválido',
            'description': 'Test',
            'price': '10.00',
            'category': 'Test',
            'stock': -5  # Stock negativo
        }
        
        response = self.client.post('/api/products/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_retrieve_nonexistent_product(self):
        """Test obtener un producto que no existe"""
        response = self.client.get('/api/products/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HealthCheckAPITest(TestCase):
    """Tests para los endpoints de health check"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
    
    def test_basic_health_check(self):
        """Test GET /catalog/health/ - Health check básico"""
        response = self.client.get('/api/catalog/health/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
        self.assertEqual(response.data['service'], 'catalog')
        self.assertIn('timestamp', response.data)
    
    def test_detailed_health_check(self):
        """Test GET /catalog/health/detailed/ - Health check detallado"""
        response = self.client.get('/api/catalog/health/detailed/')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertEqual(response.data['service'], 'catalog')
        self.assertIn('checks', response.data)
        self.assertIn('database', response.data['checks'])
    
    def test_readiness_check(self):
        """Test GET /catalog/health/ready/ - Readiness check"""
        response = self.client.get('/api/catalog/health/ready/')
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertEqual(response.data['service'], 'catalog')
    
    def test_liveness_check(self):
        """Test GET /catalog/health/live/ - Liveness check"""
        response = self.client.get('/api/catalog/health/live/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'alive')
        self.assertEqual(response.data['service'], 'catalog')


class SagaAPITest(TestCase):
    """Tests para los endpoints del Saga"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = APIClient()
        
        # Crear productos de prueba
        self.product = Product.objects.create(
            name='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category='Test',
            stock=20,
            is_active=True
        )
    
    def test_saga_random_product(self):
        """Test GET /api/saga/products/random/ - Producto aleatorio para Saga"""
        response = self.client.get('/api/saga/products/random/')
        
        # Puede ser 200 (éxito) o 500 (error simulado)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])
    
    def test_saga_reserve_product(self):
        """Test POST /api/saga/products/reserve/ - Reservar stock"""
        data = {
            'product_id': self.product.id,
            'quantity': 2,
            'saga_transaction_id': 'test-transaction-123'
        }
        
        response = self.client.post('/api/saga/products/reserve/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity_reserved'], 2)
        
        # Verificar que el stock se redujo
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 18)
    
    def test_saga_reserve_insufficient_stock(self):
        """Test reservar más stock del disponible"""
        data = {
            'product_id': self.product.id,
            'quantity': 30,  # Más del stock disponible (20)
            'saga_transaction_id': 'test-transaction-456'
        }
        
        response = self.client.post('/api/saga/products/reserve/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
    
    def test_saga_confirm_product(self):
        """Test POST /api/saga/products/confirm/ - Confirmar reserva"""
        data = {
            'product_id': self.product.id,
            'quantity': 2,
            'saga_transaction_id': 'test-transaction-789'
        }
        
        response = self.client.post('/api/saga/products/confirm/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_saga_compensate_product(self):
        """Test POST /api/saga/products/compensate/ - Compensar (revertir) reserva"""
        # Primero reservar
        original_stock = self.product.stock
        self.product.stock -= 5
        self.product.save()
        
        # Luego compensar
        data = {
            'product_id': self.product.id,
            'quantity': 5,
            'saga_transaction_id': 'test-transaction-compensate'
        }
        
        response = self.client.post('/api/saga/products/compensate/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity_restored'], 5)
        
        # Verificar que el stock se restauró
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, original_stock)
    
    def test_saga_product_status(self):
        """Test GET /api/saga/products/{id}/status/ - Estado del producto"""
        response = self.client.get(f'/api/saga/products/{self.product.id}/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], self.product.id)
        self.assertIn('is_available', response.data)
