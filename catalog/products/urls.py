"""
URL configuration for catalog microservice.
Simplified to only expose the required random product endpoint.
"""

from django.urls import path
from .views import RandomProductView
from .health_views import CatalogHealthCheckView

urlpatterns = [
    # Random product endpoint (required by orchestrator)
    path("products/random/", RandomProductView.as_view(), name="random-product"),
    # Basic health check
    path("health/", CatalogHealthCheckView.as_view(), name="catalog-health"),
]
