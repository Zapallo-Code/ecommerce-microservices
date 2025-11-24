"""
Purchase domain models for the microservice.
Implements the Purchase entity for Saga pattern orchestration.
Simplified model according to KISS and SOLID principles.
"""

from __future__ import annotations

from enum import StrEnum

from django.db import models
from django.utils import timezone


class PurchaseStatus(StrEnum):
    """Enum for purchase status values in Saga pattern."""

    PENDING = "pending"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    FAILED = "failed"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Generate Django choices from enum."""
        return [(status.value, status.name.title()) for status in cls]


class Purchase(models.Model):
    """
    Purchase entity for Saga pattern orchestration.

    Represents a single purchase transaction in the distributed system.
    Uses simplified model with single item per purchase for KISS principle.

    Attributes:
        transaction_id: Unique identifier from orchestrator
        user_id: Customer/user identifier
        product_id: Product being purchased
        quantity: Number of items purchased
        payment_id: Payment transaction reference
        amount: Total purchase amount
        status: Current status in Saga flow
        error_message: Error details if transaction failed
        created_at: Transaction creation timestamp
        updated_at: Last modification timestamp
    """

    # Backwards compatibility: Status constants as class attributes
    STATUS_PENDING = PurchaseStatus.PENDING
    STATUS_SUCCESS = PurchaseStatus.SUCCESS
    STATUS_CANCELLED = PurchaseStatus.CANCELLED
    STATUS_FAILED = PurchaseStatus.FAILED
    STATUS_CHOICES = PurchaseStatus.choices()

    # Core fields required by Saga orchestrator
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique transaction ID from orchestrator",
    )
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="User/customer identifier",
    )
    product_id = models.CharField(
        max_length=255,
        help_text="Product identifier",
    )
    quantity = models.IntegerField(
        default=1,
        help_text="Quantity of products purchased",
    )
    payment_id = models.CharField(
        max_length=255,
        help_text="Payment transaction identifier",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Purchase amount",
    )

    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=PurchaseStatus.choices(),
        default=PurchaseStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata configuration."""

        db_table = "purchases"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        """String representation of the purchase."""
        return (
            f"Purchase {self.transaction_id} - "
            f"User {self.user_id} - {self.status}"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"<Purchase(transaction_id={self.transaction_id!r}, "
            f"status={self.status!r})>"
        )

    # Status transition methods (DRY pattern)

    def _update_status(
        self,
        new_status: PurchaseStatus,
        error_message: str | None = None,
    ) -> None:
        """
        Internal method to update purchase status (DRY principle).

        Args:
            new_status: The new status to set
            error_message: Optional error message for failed transactions
        """
        self.status = new_status
        if error_message:
            self.error_message = error_message
        self.updated_at = timezone.now()
        
        fields_to_update = ["status", "updated_at"]
        if error_message:
            fields_to_update.append("error_message")
        
        self.save(update_fields=fields_to_update)

    def mark_success(self) -> None:
        """Mark the purchase as successful (Saga success path)."""
        self._update_status(PurchaseStatus.SUCCESS)

    def mark_failed(self, error_message: str | None = None) -> None:
        """
        Mark the purchase as failed (Saga failure path).

        Args:
            error_message: Optional description of the failure reason
        """
        self._update_status(PurchaseStatus.FAILED, error_message)

    def cancel(self) -> None:
        """Cancel the purchase (Saga compensation)."""
        self._update_status(PurchaseStatus.CANCELLED)

    # Status checkers as properties (more Pythonic)

    @property
    def is_pending(self) -> bool:
        """Check if purchase is in pending status."""
        return self.status == PurchaseStatus.PENDING

    @property
    def is_success(self) -> bool:
        """Check if purchase is successful."""
        return self.status == PurchaseStatus.SUCCESS

    @property
    def is_cancelled(self) -> bool:
        """Check if purchase is cancelled."""
        return self.status == PurchaseStatus.CANCELLED

    @property
    def is_failed(self) -> bool:
        """Check if purchase is failed."""
        return self.status == PurchaseStatus.FAILED
