"""
Tests for inventory microservice.
"""
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from inventory.models import Inventory, InventoryOperation
from inventory.services import InventoryService, InsufficientStockError
import uuid


class InventoryModelTest(TestCase):
    """Test inventory models."""
    
    def setUp(self):
        self.inventory = Inventory.objects.create(
            product_id=1,
            stock=100,
            reserved=0
        )
    
    def test_create_inventory(self):
        """Test inventory creation."""
        self.assertEqual(self.inventory.product_id, 1)
        self.assertEqual(self.inventory.stock, 100)
        self.assertEqual(self.inventory.available, 100)
    
    def test_available_stock(self):
        """Test available stock calculation."""
        self.inventory.reserved = 20
        self.inventory.save()
        self.assertEqual(self.inventory.available, 80)


class InventoryServiceTest(TestCase):
    """Test inventory service logic."""
    
    def setUp(self):
        # Disable random failures for deterministic tests
        settings.NO_STOCK_RATE = 0.0
        settings.SIMULATE_LATENCY = False
        
        self.inventory = Inventory.objects.create(
            product_id=1,
            stock=100
        )
    
    def test_decrease_stock_success(self):
        """Test successful stock decrease."""
        operation_id = uuid.uuid4()
        result = InventoryService.decrease_stock(
            operation_id=operation_id,
            product_id=1,
            quantity=10
        )
        
        self.assertEqual(result['status'], 'updated')
        self.assertEqual(result['remaining'], 90)
        
        # Verify database
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 90)
        
        # Verify operation recorded
        op = InventoryOperation.objects.get(operation_id=operation_id)
        self.assertEqual(op.status, 'applied')
        self.assertEqual(op.quantity, -10)
    
    def test_decrease_stock_insufficient(self):
        """Test decrease with insufficient stock."""
        operation_id = uuid.uuid4()
        
        with self.assertRaises(InsufficientStockError):
            InventoryService.decrease_stock(
                operation_id=operation_id,
                product_id=1,
                quantity=150
            )
        
        # Verify stock unchanged
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 100)
    
    def test_decrease_stock_idempotency(self):
        """Test idempotent decrease."""
        operation_id = uuid.uuid4()
        
        # First call
        result1 = InventoryService.decrease_stock(
            operation_id=operation_id,
            product_id=1,
            quantity=10
        )
        
        # Second call with same operation_id
        result2 = InventoryService.decrease_stock(
            operation_id=operation_id,
            product_id=1,
            quantity=10
        )
        
        # Stock should only decrease once
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 90)
        
        # Should have only one operation
        self.assertEqual(InventoryOperation.objects.filter(operation_id=operation_id).count(), 1)
    
    def test_compensate_success(self):
        """Test successful compensation."""
        # First decrease stock
        decrease_op_id = uuid.uuid4()
        InventoryService.decrease_stock(
            operation_id=decrease_op_id,
            product_id=1,
            quantity=30
        )
        
        # Then compensate
        compensate_op_id = uuid.uuid4()
        result = InventoryService.compensate(
            operation_id=compensate_op_id,
            product_id=1,
            quantity=30
        )
        
        self.assertEqual(result['status'], 'compensated')
        self.assertEqual(result['new_stock'], 100)
        
        # Verify database
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 100)
        
        # Verify compensation recorded
        op = InventoryOperation.objects.get(operation_id=compensate_op_id)
        self.assertEqual(op.status, 'reverted')
        self.assertEqual(op.quantity, 30)
    
    def test_compensate_idempotency(self):
        """Test idempotent compensation."""
        compensate_op_id = uuid.uuid4()
        
        # First compensation
        result1 = InventoryService.compensate(
            operation_id=compensate_op_id,
            product_id=1,
            quantity=20
        )
        
        # Second compensation with same operation_id
        result2 = InventoryService.compensate(
            operation_id=compensate_op_id,
            product_id=1,
            quantity=20
        )
        
        # Stock should only increase once
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock, 120)
        
        # Should have only one compensation operation
        self.assertEqual(InventoryOperation.objects.filter(
            operation_id=compensate_op_id,
            status='reverted'
        ).count(), 1)


class InventoryAPITest(TestCase):
    """Test inventory API endpoints."""
    
    def setUp(self):
        settings.NO_STOCK_RATE = 0.0
        settings.SIMULATE_LATENCY = False
        
        self.client = APIClient()
        self.inventory = Inventory.objects.create(
            product_id=1,
            stock=100
        )
    
    def test_decrease_endpoint_success(self):
        """Test POST /inventory/decrease/ success."""
        data = {
            'operation_id': str(uuid.uuid4()),
            'product_id': 1,
            'quantity': 10
        }
        
        response = self.client.post('/inventory/decrease/', data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'updated')
        self.assertEqual(response.json()['remaining'], 90)
    
    def test_decrease_endpoint_no_stock(self):
        """Test POST /inventory/decrease/ with insufficient stock."""
        data = {
            'operation_id': str(uuid.uuid4()),
            'product_id': 1,
            'quantity': 150
        }
        
        response = self.client.post('/inventory/decrease/', data, format='json')
        
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['status'], 'no_stock')
    
    def test_compensate_endpoint(self):
        """Test POST /inventory/compensate/."""
        data = {
            'operation_id': str(uuid.uuid4()),
            'product_id': 1,
            'quantity': 20
        }
        
        response = self.client.post('/inventory/compensate/', data, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'compensated')
        self.assertEqual(response.json()['new_stock'], 120)
    
    def test_get_inventory_endpoint(self):
        """Test GET /inventory/{product_id}/."""
        response = self.client.get('/inventory/1/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['product_id'], 1)
        self.assertEqual(data['stock'], 100)
    
    def test_health_check_endpoint(self):
        """Test GET /inventory/health/."""
        response = self.client.get('/inventory/health/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')
        self.assertEqual(response.json()['service'], 'inventory')
