"""URL configuration for inventory app."""
from django.urls import path
from .views import (
    DecreaseInventoryView,
    CompensateInventoryView,
    InventoryDetailView,
    HealthCheckView
)

urlpatterns = [
    path('decrease/', DecreaseInventoryView.as_view(), name='decrease-inventory'),
    path('compensate/', CompensateInventoryView.as_view(), name='compensate-inventory'),
    path('<int:product_id>/', InventoryDetailView.as_view(), name='inventory-detail'),
    path('health/', HealthCheckView.as_view(), name='health-check'),
]
