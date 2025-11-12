from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Max
from random import randint
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
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """
        Obtiene un producto aleatorio del catálogo
        
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
            404: Si no hay productos disponibles en la base de datos
        """
        # Contar total de productos
        count = Product.objects.count()
        
        if count == 0:
            return Response(
                {
                    "error": "No hay productos disponibles en el catálogo",
                    "detail": "La base de datos no contiene productos para seleccionar"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Método eficiente para obtener un producto aleatorio en bases grandes
        max_id = Product.objects.aggregate(max_id=Max('id'))['max_id']
        
        # Intentar obtener un producto válido
        producto = None
        intentos = 0
        max_intentos = 10
        
        while not producto and intentos < max_intentos:
            random_id = randint(1, max_id)
            producto = Product.objects.filter(id__gte=random_id).first()
            intentos += 1
        
        # Fallback: si no se encuentra después de varios intentos
        if not producto:
            producto = Product.objects.first()
        
        serializer = ProductRandomSerializer(producto)
        return Response(serializer.data, status=status.HTTP_200_OK)

