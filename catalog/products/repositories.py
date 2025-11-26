"""
Repository pattern implementation for Product data access.
Abstracts database operations following the Repository pattern.
"""
from typing import List, Optional, Protocol
from django.db.models import QuerySet
from .models import Product


class IProductRepository(Protocol):
    """Interface for Product repository operations."""
    
    def get_random_active_product(self) -> Optional[Product]:
        """Get a random active product with stock."""
        ...
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get a product by its ID."""
        ...
    
    def filter_active_with_stock(self) -> QuerySet[Product]:
        """Filter products that are active and have stock."""
        ...
    
    def all(self) -> QuerySet[Product]:
        """Get all products."""
        ...
    
    def create(self, **kwargs) -> Product:
        """Create a new product."""
        ...
    
    def update(self, product: Product, **kwargs) -> Product:
        """Update an existing product."""
        ...
    
    def delete(self, product: Product) -> None:
        """Delete a product."""
        ...


class ProductRepository:
    """
    Repository for Product data access operations.
    Encapsulates all database queries related to Product model.
    """
    
    def get_random_active_product(self) -> Optional[Product]:
        """
        Get a random active product with stock.
        
        Returns:
            Product instance or None if no products available
        """
        return Product.objects.filter(
            is_active=True,
            stock__gt=0
        ).order_by('?').first()
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a product by its ID.
        
        Args:
            product_id: The ID of the product
            
        Returns:
            Product instance or None if not found
        """
        try:
            return Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return None
    
    def filter_active_with_stock(self) -> QuerySet[Product]:
        """
        Filter products that are active and have stock.
        
        Returns:
            QuerySet of active products with stock
        """
        return Product.objects.filter(
            is_active=True,
            stock__gt=0
        )
    
    def all(self) -> QuerySet[Product]:
        """
        Get all products.
        
        Returns:
            QuerySet of all products
        """
        return Product.objects.all()
    
    def create(self, **kwargs) -> Product:
        """
        Create a new product.
        
        Args:
            **kwargs: Product fields
            
        Returns:
            Created Product instance
        """
        return Product.objects.create(**kwargs)
    
    def update(self, product: Product, **kwargs) -> Product:
        """
        Update an existing product.
        
        Args:
            product: Product instance to update
            **kwargs: Fields to update
            
        Returns:
            Updated Product instance
        """
        for field, value in kwargs.items():
            setattr(product, field, value)
        product.save()
        return product
    
    def delete(self, product: Product) -> None:
        """
        Delete a product.
        
        Args:
            product: Product instance to delete
        """
        product.delete()
