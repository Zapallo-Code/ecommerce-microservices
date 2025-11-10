"""
Django admin configuration for Purchase models.
"""
from django.contrib import admin
from app.models import Purchase, PurchaseDetail


class PurchaseDetailInline(admin.TabularInline):
    """Inline admin for purchase details."""
    model = PurchaseDetail
    extra = 0
    fields = ['product_id', 'quantity', 'unit_price']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Admin configuration for Purchase model."""
    
    list_display = [
        'id',
        'customer_id',
        'status',
        'total_amount',
        'saga_id',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'customer_id', 'saga_id']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']
    inlines = [PurchaseDetailInline]
    
    fieldsets = (
        ('Purchase Information', {
            'fields': (
                'customer_id',
                'total_amount',
                'status'
            )
        }),
        ('Saga Information', {
            'fields': (
                'saga_id',
                'error_message'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )


@admin.register(PurchaseDetail)
class PurchaseDetailAdmin(admin.ModelAdmin):
    """Admin configuration for PurchaseDetail model."""
    
    list_display = [
        'id',
        'purchase',
        'product_id',
        'quantity',
        'unit_price'
    ]
    list_filter = ['purchase__status']
    search_fields = ['purchase__id', 'product_id']
