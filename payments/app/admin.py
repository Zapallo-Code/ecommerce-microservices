"""
Admin panel configuration for the payments microservice (Saga).
"""
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment"""
    list_display = [
        'id',
        'transaction_id',
        'order_id',
        'amount',
        'status',
        'created_at',
        'compensated_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['transaction_id', 'order_id']
    readonly_fields = ['created_at', 'updated_at', 'compensated_at']
    ordering = ['-created_at']
