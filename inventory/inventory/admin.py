from django.contrib import admin
from .models import Inventory, InventoryOperation


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'stock', 'reserved', 'available', 'updated_at']
    search_fields = ['product_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InventoryOperation)
class InventoryOperationAdmin(admin.ModelAdmin):
    list_display = ['operation_id', 'product_id', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['operation_id', 'product_id']
    readonly_fields = ['created_at']
