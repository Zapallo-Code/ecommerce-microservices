"""URL configuration for inventory microservice."""

from django.contrib import admin
from django.urls import path, include
from inventory.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("inventory/", include("inventory.urls")),
    # Health check at root level for Docker/Traefik
    path("health/", HealthCheckView.as_view(), name="root-health-check"),
]
