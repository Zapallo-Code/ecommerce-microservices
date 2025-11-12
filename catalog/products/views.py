from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max
from random import randint, uniform
import random
import time
from .models import Product
from .serializers import ProductSerializer, ProductRandomSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations
    
    Provides:
    - list: GET /api/products/
    - create: POST /api/products/
    - retrieve: GET /api/products/{id}/
    - update: PUT /api/products/{id}/
    - partial_update: PATCH /api/products/{id}/
    - destroy: DELETE /api/products/{id}/
    """
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Optionally filter products by availability
        """
        queryset = super().get_queryset()
        
        # Filter by availability (stock > 0 and is_active=True)
        available = self.request.query_params.get('available', None)
        if available is not None:
            if available.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(stock__gt=0, is_active=True)
            elif available.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(stock=0) | queryset.filter(is_active=False)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock (less than 10 units)"""
        low_stock_products = self.queryset.filter(stock__lt=10, stock__gt=0)
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get products that are out of stock"""
        out_of_stock_products = self.queryset.filter(stock=0)
        serializer = self.get_serializer(out_of_stock_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='random')
    def random(self, request):
        """
        Endpoint requerido por el patrón Saga.
        Retorna un producto aleatorio con datos disponibles.
        Simula latencia y posibles errores.
        
        Returns:
            Response: JSON con el formato:
            {
                "product_id": 123,
                "name": "Producto X",
                "price": 29.99,
                "description": "...",
                "stock": 10
            }
        
        Raises:
            404: Si no hay productos disponibles (activos y con stock)
            500: Simulación aleatoria de error interno del servidor (10% probabilidad)
        """
        # Simular latencia de procesamiento entre 0.1 y 0.5 segundos
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simular error aleatorio con 10% de probabilidad
        if random.random() < 0.1:
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Obtener productos activos con stock disponible
        products = Product.objects.filter(
            is_active=True,
            stock__gt=0
        )
        
        if not products.exists():
            return Response(
                {"error": "No products available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Seleccionar un producto aleatorio
        product = random.choice(list(products))
        serializer = ProductRandomSerializer(product)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

