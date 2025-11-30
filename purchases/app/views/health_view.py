from django.http import JsonResponse
from django.views import View


class HealthCheckView(View):
    def get(self, _request) -> JsonResponse:
        return JsonResponse({"status": "healthy", "service": "purchases"})
