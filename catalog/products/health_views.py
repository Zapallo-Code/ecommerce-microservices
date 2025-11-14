from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class CatalogHealthCheckView(APIView):
    def get(self, request):
        return Response(
            {"status": "healthy", "service": "catalog"}, status=status.HTTP_200_OK
        )
