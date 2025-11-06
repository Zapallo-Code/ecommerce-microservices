from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product
from .serializers import ProductSerializer


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

