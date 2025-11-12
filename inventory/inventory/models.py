"""
Inventory models for saga orchestration.
"""
from django.db import models
import uuid


class Inventory(models.Model):
    """
    Product inventory model.
    Manages stock levels for products.
    """
    product_id = models.IntegerField(unique=True, db_index=True)
    stock = models.IntegerField(default=0)
    reserved = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'

    def __str__(self):
        return f"Product {self.product_id}: {self.stock} units"

    @property
    def available(self):
        """Available stock (not reserved)."""
        return self.stock - self.reserved


class InventoryOperation(models.Model):
    """
    Track inventory operations for idempotency and audit.
    """
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('reverted', 'Reverted'),
        ('failed', 'Failed'),
    ]

    operation_id = models.UUIDField(unique=True, db_index=True)
    product_id = models.IntegerField(db_index=True)
    quantity = models.IntegerField()  # negative for decrease, positive for compensate
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'inventory_operation'
        verbose_name = 'Inventory Operation'
        verbose_name_plural = 'Inventory Operations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.operation_id}: {self.status}"
