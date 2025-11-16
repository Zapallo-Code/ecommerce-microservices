from django.db import models


class Payment(models.Model):
    """
    Model for recording payment transactions in the context of a distributed Saga.
    Stores information about processed and compensated payments.
    """
    
    # Possible payment states
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Success'
        ERROR = 'error', 'Error'
        COMPENSATED = 'compensated', 'Compensated'

    # Unique transaction ID for the payment
    transaction_id = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)
    
    # User ID (requerido por orchestrator)
    user_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    
    # Product ID (requerido por orchestrator)
    product_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Relation with the order (from purchases/orchestrator microservice) - OPCIONAL
    order_id = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    
    # Payment amount
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Payment status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUCCESS,
        db_index=True
    )
    
    # Message associated with the status
    message = models.TextField(blank=True)
    
    # Additional metadata (request information)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    compensated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['order_id', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"
