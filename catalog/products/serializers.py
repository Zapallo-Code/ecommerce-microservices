"""
Serializers for catalog microservice.
Provides structured data transformation following DRF best practices.
"""

from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Handles serialization of product data for API responses.
    """
    
    product_id = serializers.IntegerField(source='id', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=True)
    
    class Meta:
        model = Product
        fields = ['product_id', 'name', 'description', 'price', 'category', 'stock']
        read_only_fields = ['product_id']


class ProductRandomSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for random product endpoint.
    Returns only essential fields needed by the orchestrator.
    """
    
    product_id = serializers.IntegerField(source='id', read_only=True)
    price = serializers.CharField(source='price', read_only=True)  # Return as string for consistency
    
    class Meta:
        model = Product
        fields = ['product_id', 'name', 'description', 'price', 'category', 'stock']
