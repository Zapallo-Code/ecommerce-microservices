from django.contrib import admin
from django.urls import path
from django.http import JsonResponse


def health_check(request):
    """Health check endpoint for Docker and monitoring."""
    return JsonResponse({"status": "healthy", "service": "purchases"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health"),
]
