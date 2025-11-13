"""Health check view for the purchases microservice."""

from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """Simple health check endpoint."""

    def get(self, request):
        """Return a simple health check response."""
        return JsonResponse({"status": "healthy", "service": "purchases"})
