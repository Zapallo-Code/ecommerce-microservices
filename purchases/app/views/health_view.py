"""Health check view for the purchases microservice."""

from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    """Simple health check endpoint."""

    def get(self, _request) -> JsonResponse:
        """Return a simple health check response."""
        return JsonResponse({"status": "healthy", "service": "purchases"})
