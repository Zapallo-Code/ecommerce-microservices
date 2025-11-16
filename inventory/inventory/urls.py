"""
URL configuration for inventory app.
Simplified - only decrease endpoint, no compensation needed per requirements.
"""

from django.urls import path
from .views import DecreaseInventoryView, HealthCheckView

urlpatterns = [
    path("decrease/", DecreaseInventoryView.as_view(), name="decrease-inventory"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
