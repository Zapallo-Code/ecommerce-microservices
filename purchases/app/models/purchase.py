"""
Purchase domain models for the microservice.
Implements the Purchase entity for Saga pattern orchestration.
Simplified model according to KISS and SOLID principles.
"""
from django.db import models
from django.utils import timezone


class Purchase(models.Model):
    """
    Purchase entity for Saga pattern orchestration.
    Represents a single purchase transaction in the distributed system.
    
    Fields align with orchestrator contract:
    - transaction_id: Unique identifier from orchestrator
    - user_id: Customer/user identifier
    - product_id: Product being purchased
    - payment_id: Payment transaction reference
    - amount: Purchase amount
    """
    
    # Status choices for the Saga pattern
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_CANCELLED = 'cancelled'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Core fields required by Saga orchestrator
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Unique transaction ID from orchestrator"
    )
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="User/customer identifier"
    )
    product_id = models.CharField(
        max_length=255,
        help_text="Product identifier"
    )
    payment_id = models.CharField(
        max_length=255,
        help_text="Payment transaction identifier"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Purchase amount"
    )
    
    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return (
            f"Purchase {self.transaction_id} - "
            f"User {self.user_id} - {self.status}"
        )
    
    def mark_success(self):
        """Mark the purchase as successful (Saga success path)."""
        self.status = self.STATUS_SUCCESS
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_failed(self, error_message: str = None):
        """Mark the purchase as failed (Saga failure path)."""
        self.status = self.STATUS_FAILED
        if error_message:
            self.error_message = error_message
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'updated_at'])
    
    def cancel(self):
        """Cancel the purchase (Saga compensation)."""
        self.status = self.STATUS_CANCELLED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])
    
    def is_pending(self) -> bool:
        """Check if purchase is in pending status."""
        return self.status == self.STATUS_PENDING
    
    def is_success(self) -> bool:
        """Check if purchase is successful."""
        return self.status == self.STATUS_SUCCESS
    
    def is_cancelled(self) -> bool:
        """Check if purchase is cancelled."""
        return self.status == self.STATUS_CANCELLED
    
    def is_failed(self) -> bool:
        """Check if purchase is failed."""
        return self.status == self.STATUS_FAILED
