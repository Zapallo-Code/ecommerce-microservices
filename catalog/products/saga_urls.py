"""
URLs para endpoints del patrón Saga en el microservicio de Catálogo

Estas rutas son utilizadas por el orquestador del Saga para coordinar
transacciones distribuidas relacionadas con productos.
"""

from django.urls import path
from .saga_views import (
    SagaRandomProductView,
    SagaReserveProductView,
    SagaConfirmProductView,
    SagaCompensateProductView,
    SagaProductStatusView,
)

urlpatterns = [
    # Obtener producto aleatorio para el Saga
    path('random/', SagaRandomProductView.as_view(), name='saga-random-product'),
    
    # Reservar stock de producto (fase de preparación)
    path('reserve/', SagaReserveProductView.as_view(), name='saga-reserve-product'),
    
    # Confirmar reserva de producto (fase de confirmación)
    path('confirm/', SagaConfirmProductView.as_view(), name='saga-confirm-product'),
    
    # Compensar (revertir) reserva de producto (fase de compensación)
    path('compensate/', SagaCompensateProductView.as_view(), name='saga-compensate-product'),
    
    # Consultar estado de un producto
    path('<int:product_id>/status/', SagaProductStatusView.as_view(), name='saga-product-status'),
]
