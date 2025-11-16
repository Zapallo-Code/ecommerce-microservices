"""
API views for inventory microservice.
Implements Saga pattern with decrease operation only.
According to requirements, inventory does NOT need compensation.
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .services import InventoryService
from .serializers import DecreaseInventorySerializer

logger = logging.getLogger(__name__)


class DecreaseInventoryView(APIView):
    """
    Decrease product stock (Saga transaction step).

    POST /inventory/decrease/

    Request body:
    {
        "product_id": "string",
        "quantity": 1,
        "transaction_id": "string" (optional)
    }

    Returns:
    - 200 OK: Stock decreased successfully
    - 400 Bad Request: Invalid data
    - 409 Conflict: Insufficient stock or random failure
    - 500 Internal Server Error: Server error
    """

    def post(self, request):
        serializer = DecreaseInventorySerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Invalid data for decrease inventory: {serializer.errors}")
            return Response(
                {
                    "status": "error",
                    "message": "Invalid data",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        product_id = serializer.validated_data["product_id"]
        quantity = serializer.validated_data["quantity"]
        transaction_id = request.data.get("transaction_id")

        logger.info(
            f"Decrease inventory request - product_id: {product_id}, quantity: {quantity}, transaction_id: {transaction_id}"
        )

        try:
            with transaction.atomic():
                result = InventoryService.decrease_inventory(
                    product_id=product_id,
                    quantity=quantity,
                    transaction_id=transaction_id,
                )

                logger.info(
                    f"Inventory decreased successfully - product_id: {product_id}, operation_id: {result.get('operation_id')}"
                )
                return Response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.error(
                f"Insufficient stock or random failure - product_id: {product_id}, error: {str(e)}"
            )
            return Response(
                {"status": "error", "message": str(e)}, status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            logger.error(
                f"Error decreasing inventory - product_id: {product_id}, error: {str(e)}"
            )
            return Response(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HealthCheckView(APIView):
    """
    GET /inventory/health/
    Health check endpoint for orchestrator/Traefik.
    """

    def get(self, request):
        return Response(
            {"status": "healthy", "service": "inventory", "version": "1.0.0"},
            status=status.HTTP_200_OK,
        )
