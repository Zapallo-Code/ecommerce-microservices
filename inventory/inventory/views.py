import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import InventoryService, InsufficientStockError
from .serializers import (
    DecreaseInventorySerializer,
    CompensateInventorySerializer,
    InventorySerializer,
)

logger = logging.getLogger(__name__)


class DecreaseInventoryView(APIView):
    def post(self, request):
        serializer = DecreaseInventorySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            result = InventoryService.decrease_stock(
                operation_id=data["operation_id"],
                product_id=data["product_id"],
                quantity=data["quantity"],
                metadata=data.get("metadata"),
            )
            return Response(result, status=status.HTTP_200_OK)

        except InsufficientStockError as e:
            logger.warning(f"Insufficient stock: {str(e)}")
            return Response(
                {
                    "status": "no_stock",
                    "product_id": data["product_id"],
                    "message": str(e),
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            logger.error(f"Error in decrease_stock: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CompensateInventoryView(APIView):
    def post(self, request):
        serializer = CompensateInventorySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            result = InventoryService.compensate(
                operation_id=data["operation_id"],
                product_id=data["product_id"],
                quantity=data["quantity"],
                metadata=data.get("metadata"),
            )
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in compensate: {str(e)}", exc_info=True)
            # Even on error, compensate should return 200 to avoid saga loop
            return Response(
                {
                    "status": "compensated",
                    "product_id": data["product_id"],
                    "error": str(e),
                },
                status=status.HTTP_200_OK,
            )


class InventoryDetailView(APIView):
    def get(self, request, product_id):
        result = InventoryService.get_inventory(product_id)

        if result is None:
            return Response(
                {"error": f"Product {product_id} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = InventorySerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    def get(self, request):
        return Response(
            {"status": "healthy", "service": "inventory", "version": "1.0.0"},
            status=status.HTTP_200_OK,
        )
