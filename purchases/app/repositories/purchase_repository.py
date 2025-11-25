"""
Repository layer for Purchase entity (simplified Saga pattern).
Provides data access abstraction following the Repository pattern.
"""

from __future__ import annotations

from django.db.models import QuerySet

from app.models import Purchase


class PurchaseRepository:
    """
    Repository for Purchase entity operations.

    Encapsulates data access logic and provides clean interface.
    Uses minimal implementation following KISS and YAGNI principles.
    For the simplified Saga pattern, most operations are handled
    directly on the Purchase model.
    """

    @classmethod
    def get_by_transaction_id(cls, transaction_id: str) -> Purchase | None:
        """
        Retrieve a purchase by transaction ID.

        Args:
            transaction_id: Unique transaction ID from orchestrator

        Returns:
            Purchase instance if found, None otherwise
        """
        try:
            return Purchase.objects.get(transaction_id=transaction_id)
        except Purchase.DoesNotExist:
            return None

    @classmethod
    def get_by_user(
        cls,
        user_id: str,
        limit: int = 100,
    ) -> QuerySet[Purchase]:
        """
        Get purchases for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of results (default: 100)

        Returns:
            QuerySet of Purchase instances (lazy evaluation)
        """
        return Purchase.objects.filter(user_id=user_id)[:limit]

    @classmethod
    def create(
        cls,
        transaction_id: str,
        user_id: str,
        product_id: str,
        payment_id: str,
        amount: float,
        quantity: int = 1,
        status: str | None = None,
    ) -> Purchase:
        """
        Create a new purchase.

        Args:
            transaction_id: Unique transaction ID from orchestrator
            user_id: User identifier
            product_id: Product identifier
            payment_id: Payment transaction identifier
            amount: Purchase amount
            quantity: Quantity of items (default: 1)
            status: Initial status (default: PENDING)

        Returns:
            Created Purchase instance
        """
        return Purchase.objects.create(
            transaction_id=transaction_id,
            user_id=user_id,
            product_id=product_id,
            payment_id=payment_id,
            amount=amount,
            quantity=quantity,
            status=status if status else Purchase.STATUS_PENDING,
        )
