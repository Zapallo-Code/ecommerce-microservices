"""
Product model for catalog microservice.
Simplified to essential fields only.
"""

from django.db import models


class Product(models.Model):
    """
    Product entity for catalog microservice.
    Stores basic product information for the Saga pattern.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, default="General")
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
