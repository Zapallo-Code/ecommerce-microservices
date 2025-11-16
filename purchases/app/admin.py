"""
Django admin configuration for Purchase models.
"""
from django.contrib import admin
from app.models import Purchase


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Admin configuration for Purchase model."""
    
    list_display = [
        'id',
        'transaction_id',
        'user_id',
        'product_id',
        'amount',
        'status',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'transaction_id', 'user_id', 'product_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'transaction_id',
                'user_id',
                'product_id',
                'payment_id',
                'amount',
                'status'
            )
        }),
        ('Error Information', {
            'fields': (
                'error_message',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            )
        }),
    )
