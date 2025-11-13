"""URL configuration for inventory microservice."""

from django.contrib import admin
from django.urls import path, include
from inventory.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("inventory/", include("inventory.urls")),
    path("api/health/", HealthCheckView.as_view(), name="health-check"),
]
