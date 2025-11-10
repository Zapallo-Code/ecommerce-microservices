"""
Purchase domain models for the microservice.
Implements the Purchase and PurchaseDetail entities with business logic.
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Purchase(models.Model):
    """
    Main Purchase entity representing a customer purchase transaction.
    Implements the Saga pattern with status transitions.
    """
    
    # Status choices for the Saga pattern
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    # Fields
    customer_id = models.IntegerField(db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata for Saga orchestration
    saga_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'purchases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer_id', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['saga_id']),
        ]
    
    def __str__(self):
        return f"Purchase #{self.id} - Customer {self.customer_id} - {self.status}"
    
    def calculate_total(self):
        """Calculate total amount from all purchase details."""
        total = sum(
            detail.quantity * detail.unit_price 
            for detail in self.details.all()
        )
        self.total_amount = Decimal(str(total))
        return self.total_amount
    
    def confirm(self):
        """Confirm the purchase (Saga success)."""
        if self.status != self.STATUS_PENDING:
            raise ValueError(f"Cannot confirm purchase with status: {self.status}")
        self.status = self.STATUS_CONFIRMED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])
    
    def cancel(self):
        """Cancel the purchase (Saga compensation)."""
        if self.status == self.STATUS_CONFIRMED:
            raise ValueError("Cannot cancel a confirmed purchase")
        self.status = self.STATUS_CANCELLED
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])
    
    def fail(self, error_message: str = None):
        """Mark the purchase as failed (Saga failure)."""
        self.status = self.STATUS_FAILED
        if error_message:
            self.error_message = error_message
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'updated_at'])
    
    def is_pending(self) -> bool:
        """Check if purchase is in pending status."""
        return self.status == self.STATUS_PENDING
    
    def is_confirmed(self) -> bool:
        """Check if purchase is confirmed."""
        return self.status == self.STATUS_CONFIRMED
    
    def is_cancelled(self) -> bool:
        """Check if purchase is cancelled."""
        return self.status == self.STATUS_CANCELLED
    
    def is_failed(self) -> bool:
        """Check if purchase is failed."""
        return self.status == self.STATUS_FAILED


class PurchaseDetail(models.Model):
    """
    Purchase detail line items.
    Represents individual products in a purchase.
    """
    
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='details'
    )
    product_id = models.IntegerField(db_index=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'purchase_details'
        indexes = [
            models.Index(fields=['purchase', 'product_id']),
        ]
    
    def __str__(self):
        return f"Detail for Purchase #{self.purchase_id} - Product {self.product_id}"
    
    def get_subtotal(self) -> Decimal:
        """Calculate subtotal for this detail line."""
        return Decimal(str(self.quantity * self.unit_price))
