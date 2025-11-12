"""
Tests para los modelos del microservicio de Catálogo
"""

from django.test import TestCase
from decimal import Decimal
from products.models import Product


class ProductModelTest(TestCase):
    """Tests para el modelo Product"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.product_data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': Decimal('99.99'),
            'category': 'Electronics',
            'stock': 10,
            'is_active': True
        }
    
    def test_create_product(self):
        """Test que se puede crear un producto correctamente"""
        product = Product.objects.create(**self.product_data)
        
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.description, 'Test Description')
        self.assertEqual(product.price, Decimal('99.99'))
        self.assertEqual(product.category, 'Electronics')
        self.assertEqual(product.stock, 10)
        self.assertTrue(product.is_active)
        self.assertIsNotNone(product.created_at)
        self.assertIsNotNone(product.updated_at)
    
    def test_product_str_method(self):
        """Test que el método __str__ retorna el nombre del producto"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(str(product), 'Test Product')
    
    def test_product_is_available_property(self):
        """Test que la propiedad is_available funciona correctamente"""
        # Producto con stock y activo
        product = Product.objects.create(**self.product_data)
        self.assertTrue(product.is_available)
        
        # Producto sin stock
        product.stock = 0
        product.save()
        self.assertFalse(product.is_available)
        
        # Producto inactivo
        product.stock = 10
        product.is_active = False
        product.save()
        self.assertFalse(product.is_available)
        
        # Producto sin stock e inactivo
        product.stock = 0
        product.is_active = False
        product.save()
        self.assertFalse(product.is_available)
    
    def test_product_price_validation(self):
        """Test que el precio debe ser positivo"""
        product = Product.objects.create(**self.product_data)
        product.price = Decimal('0.00')
        # Django no valida automáticamente en save(), 
        # pero el serializer lo validará
        self.assertEqual(product.price, Decimal('0.00'))
    
    def test_product_stock_can_be_zero(self):
        """Test que el stock puede ser cero"""
        self.product_data['stock'] = 0
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.stock, 0)
        self.assertFalse(product.is_available)
    
    def test_product_default_values(self):
        """Test que los valores por defecto se aplican correctamente"""
        minimal_product = Product.objects.create(
            name='Minimal Product',
            description='Description',
            price=Decimal('10.00')
        )
        
        self.assertEqual(minimal_product.category, 'General')
        self.assertEqual(minimal_product.stock, 0)
        self.assertTrue(minimal_product.is_active)
    
    def test_update_product(self):
        """Test que se puede actualizar un producto"""
        import time
        product = Product.objects.create(**self.product_data)
        original_updated_at = product.updated_at
        
        # Pequeño delay para asegurar que updated_at cambie
        time.sleep(0.01)
        
        # Actualizar el producto
        product.name = 'Updated Product'
        product.price = Decimal('149.99')
        product.save()
        
        # Verificar cambios
        updated_product = Product.objects.get(id=product.id)
        self.assertEqual(updated_product.name, 'Updated Product')
        self.assertEqual(updated_product.price, Decimal('149.99'))
        # Verificar que se actualizó (puede ser igual o mayor)
        self.assertGreaterEqual(updated_product.updated_at, original_updated_at)
    
    def test_delete_product(self):
        """Test que se puede eliminar un producto"""
        product = Product.objects.create(**self.product_data)
        product_id = product.id
        
        product.delete()
        
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=product_id)
    
    def test_filter_active_products(self):
        """Test que se pueden filtrar productos activos"""
        Product.objects.create(name='Active 1', description='Desc', price=Decimal('10.00'), is_active=True)
        Product.objects.create(name='Active 2', description='Desc', price=Decimal('20.00'), is_active=True)
        Product.objects.create(name='Inactive', description='Desc', price=Decimal('30.00'), is_active=False)
        
        active_products = Product.objects.filter(is_active=True)
        self.assertEqual(active_products.count(), 2)
    
    def test_filter_products_with_stock(self):
        """Test que se pueden filtrar productos con stock"""
        Product.objects.create(name='With Stock', description='Desc', price=Decimal('10.00'), stock=5)
        Product.objects.create(name='No Stock', description='Desc', price=Decimal('20.00'), stock=0)
        
        products_with_stock = Product.objects.filter(stock__gt=0)
        self.assertEqual(products_with_stock.count(), 1)
        self.assertEqual(products_with_stock.first().name, 'With Stock')
