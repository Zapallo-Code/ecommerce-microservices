"""
Inventory models for saga orchestration.
Simplified - removed InventoryOperation as it's not required.
"""

from django.db import models


class Inventory(models.Model):
    """
    Product inventory model.
    Manages stock levels for products.
    """

    product_id = models.CharField(max_length=255, unique=True, db_index=True)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory"
        verbose_name = "Inventory"
        verbose_name_plural = "Inventories"

    def __str__(self):
        return f"Product {self.product_id}: {self.stock} units"
