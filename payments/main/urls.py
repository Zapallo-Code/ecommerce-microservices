from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint for Docker and monitoring."""
    return JsonResponse({"status": "healthy", "service": "payments"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health"),
    path(
        "", include("app.urls")
    ),  # Endpoints: /payments and /payments/{payment_id}/refund
]
