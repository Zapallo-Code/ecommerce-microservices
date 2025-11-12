"""
URLs para el microservicio de pagos (patrón Saga).
Configuradas para coincidir con el contrato del orchestrator.
"""
from django.urls import path
from .views import process_payment, refund_payment

urlpatterns = [
    # POST /payments/ - Procesar pago (llamado por orchestrator)
    path('payments/', process_payment, name='process_payment'),
    
    # POST /payments/{payment_id}/refund/ - Reembolsar/compensar pago
    path('payments/<int:payment_id>/refund/', refund_payment, name='refund_payment'),
]