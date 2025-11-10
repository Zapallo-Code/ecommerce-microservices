"""
Repository layer for Purchase entity.
Provides data access abstraction following the Repository pattern.
"""
from typing import Optional, List
from django.db import transaction
from app.models import Purchase, PurchaseDetail


class PurchaseRepository:
    """
    Repository for Purchase entity operations.
    Encapsulates data access logic and provides clean interface.
    """
    
    @staticmethod
    def create_purchase(
        customer_id: int,
        items: List[dict],
        saga_id: Optional[str] = None
    ) -> Purchase:
        """
        Create a new purchase with its details atomically.
        
        Args:
            customer_id: ID of the customer making the purchase
            items: List of dicts with product_id, quantity, unit_price
            saga_id: Optional Saga orchestration ID
            
        Returns:
            Created Purchase instance
        """
        with transaction.atomic():
            purchase = Purchase.objects.create(
                customer_id=customer_id,
                saga_id=saga_id
            )
            
            # Create purchase details
            details = [
                PurchaseDetail(
                    purchase=purchase,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price']
                )
                for item in items
            ]
            PurchaseDetail.objects.bulk_create(details)
            
            # Calculate and save total
            purchase.calculate_total()
            purchase.save(update_fields=['total_amount'])
            
            return purchase
    
    @staticmethod
    def get_by_id(purchase_id: int) -> Optional[Purchase]:
        """
        Retrieve a purchase by ID with its details.
        
        Args:
            purchase_id: Purchase ID
            
        Returns:
            Purchase instance or None
        """
        try:
            return Purchase.objects.prefetch_related('details').get(
                id=purchase_id
            )
        except Purchase.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_saga_id(saga_id: str) -> Optional[Purchase]:
        """
        Retrieve a purchase by Saga ID.
        
        Args:
            saga_id: Saga orchestration ID
            
        Returns:
            Purchase instance or None
        """
        try:
            return Purchase.objects.prefetch_related('details').get(
                saga_id=saga_id
            )
        except Purchase.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_customer(
        customer_id: int,
        limit: int = 100
    ) -> List[Purchase]:
        """
        Get purchases for a specific customer.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of results
            
        Returns:
            List of Purchase instances
        """
        return list(
            Purchase.objects.filter(
                customer_id=customer_id
            ).prefetch_related('details')[:limit]
        )
    
    @staticmethod
    def confirm_purchase(purchase_id: int) -> bool:
        """
        Confirm a purchase (Saga success).
        
        Args:
            purchase_id: Purchase ID
            
        Returns:
            True if confirmed, False if not found or invalid status
        """
        try:
            purchase = Purchase.objects.get(id=purchase_id)
            purchase.confirm()
            return True
        except (Purchase.DoesNotExist, ValueError):
            return False
    
    @staticmethod
    def cancel_purchase(purchase_id: int) -> bool:
        """
        Cancel a purchase (Saga compensation).
        
        Args:
            purchase_id: Purchase ID
            
        Returns:
            True if cancelled, False if not found or invalid status
        """
        try:
            purchase = Purchase.objects.get(id=purchase_id)
            purchase.cancel()
            return True
        except (Purchase.DoesNotExist, ValueError):
            return False
    
    @staticmethod
    def fail_purchase(
        purchase_id: int,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Mark a purchase as failed (Saga failure).
        
        Args:
            purchase_id: Purchase ID
            error_message: Optional error description
            
        Returns:
            True if marked as failed, False if not found
        """
        try:
            purchase = Purchase.objects.get(id=purchase_id)
            purchase.fail(error_message)
            return True
        except Purchase.DoesNotExist:
            return False
    
    @staticmethod
    def get_all(limit: int = 100) -> List[Purchase]:
        """
        Get all purchases with pagination.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of Purchase instances
        """
        return list(
            Purchase.objects.prefetch_related('details')[:limit]
        )
