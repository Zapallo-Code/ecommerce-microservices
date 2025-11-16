"""
Repository layer for Purchase entity (simplified Saga pattern).
Provides data access abstraction following the Repository pattern.
"""
from typing import Optional, List
from app.models import Purchase


class PurchaseRepository:
    """
    Repository for Purchase entity operations.
    Encapsulates data access logic and provides clean interface.
    Note: This is a minimal implementation. For the simplified Saga pattern,
    most operations are handled directly on the Purchase model.
    """
    
    @staticmethod
    def get_by_transaction_id(transaction_id: str) -> Optional[Purchase]:
        """
        Retrieve a purchase by transaction ID.
        
        Args:
            transaction_id: Transaction ID from orchestrator
            
        Returns:
            Purchase instance or None
        """
        try:
            return Purchase.objects.get(transaction_id=transaction_id)
        except Purchase.DoesNotExist:
            return None
    
    @staticmethod
    def get_by_user(
        user_id: str,
        limit: int = 100
    ) -> List[Purchase]:
        """
        Get purchases for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            List of Purchase instances
        """
        return list(
            Purchase.objects.filter(user_id=user_id)[:limit]
        )
