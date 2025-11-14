"""
Admin configuration for inventory microservice.
Simplified following KISS principle.
"""

from django.contrib import admin
from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    """Admin interface for Inventory model."""

    list_display = ["product_id", "stock", "updated_at"]
    search_fields = ["product_id"]
    readonly_fields = ["created_at", "updated_at"]
    list_filter = ["created_at"]
