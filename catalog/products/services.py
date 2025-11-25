"""
Service layer for Product business logic.
Orchestrates operations between views and repositories.
"""
import logging
from typing import Optional, Protocol
from django.db.utils import DatabaseError
from .models import Product
from .repositories import ProductRepository, IProductRepository


logger = logging.getLogger(__name__)


class IProductService(Protocol):
    """Interface for Product service operations."""
    
    def get_random_product(self) -> Optional[Product]:
        """Get a random active product with stock."""
        ...


class ProductService:
    """
    Service for Product business logic.
    Handles validation, error handling, and orchestrates repository operations.
    """
    
    def __init__(self, repository: Optional[IProductRepository] = None):
        """
        Initialize the service with a repository.
        
        Args:
            repository: Product repository instance (defaults to ProductRepository)
        """
        self.repository = repository or ProductRepository()
    
    def get_random_product(self) -> Optional[Product]:
        """
        Get a random active product with stock.
        Handles logging and error scenarios.
        
        Returns:
            Product instance or None if no products available
            
        Raises:
            DatabaseError: When database operation fails
        """
        logger.info("Fetching random active product")
        
        try:
            product = self.repository.get_random_active_product()
            
            if product:
                logger.info(
                    f"Selected product: {product.name} "
                    f"(ID: {product.id}, Price: {product.price})"
                )
            else:
                logger.warning("No active products with stock available")
            
            return product
            
        except DatabaseError as e:
            logger.error(f"Database error retrieving random product: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving random product: {e}")
            raise
