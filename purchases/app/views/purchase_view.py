"""
API Views for Purchase endpoints.
Implements REST API for purchase operations with Saga pattern.
Uses APIView instead of ViewSet for cleaner endpoint definitions.
"""

import logging
from typing import Any

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app.serializers.purchase_serializer import (
    CancelResponseSerializer,
    PurchaseErrorResponseSerializer,
    PurchaseRequestSerializer,
    PurchaseSuccessResponseSerializer,
)
from app.services.purchase_service import PurchaseService

logger = logging.getLogger(__name__)


class BasePurchaseView(APIView):
    """
    Base view for purchase operations.
    Provides common functionality following DRY principle.
    """

    permission_classes = [AllowAny]
    service_class = PurchaseService

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._service: PurchaseService | None = None

    @property
    def service(self) -> PurchaseService:
        """Lazy initialization of service (improves performance)."""
        if self._service is None:
            self._service = self.service_class()
        return self._service

    def _build_response(
        self,
        serializer_class: type,
        data: dict[str, Any],
        status_code: int,
    ) -> Response:
        """
        Build and validate response (DRY helper method).

        Args:
            serializer_class: Serializer class to use
            data: Data to serialize
            status_code: HTTP status code

        Returns:
            Response object with serialized data
        """
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=False)
        return Response(serializer.data, status=status_code)


class PurchaseCreateView(BasePurchaseView):
    """
    API endpoint for creating a purchase transaction.
    POST /purchases

    Implements Saga pattern with random success/failure (50%).
    Returns 201 CREATED for success or 409 CONFLICT for failure.
    """

    def post(self, request: Request) -> Response:
        """
        Create a new purchase transaction.

        Request body:
        {
            "transaction_id": "uuid",
            "user_id": "string",
            "product_id": "string",
            "payment_id": "string",
            "amount": 100.50,
            "quantity": 1  // optional, defaults to 1
        }

        Response 201 CREATED:
        {
            "status": "success",
            "purchase_id": "generated-id",
            "transaction_id": "uuid"
        }

        Response 409 CONFLICT:
        {
            "status": "error",
            "message": "Purchase failed",
            "error": "CONFLICT"
        }
        """
        # Validate request
        serializer = PurchaseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Invalid purchase request: %s", serializer.errors)
            return Response(
                {
                    "status": "error",
                    "message": "Invalid request data",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process purchase
        validated_data = serializer.validated_data
        result = self.service.create_purchase(
            transaction_id=validated_data["transaction_id"],
            user_id=validated_data["user_id"],
            product_id=validated_data["product_id"],
            payment_id=validated_data["payment_id"],
            amount=validated_data["amount"],
            quantity=validated_data.get("quantity", 1),
        )

        # Return response based on result
        if result["status"] == "success":
            logger.info(
                "Purchase created successfully: %s", result["transaction_id"]
            )
            return self._build_response(
                PurchaseSuccessResponseSerializer,
                result,
                status.HTTP_201_CREATED,
            )

        logger.warning(
            "Purchase failed: %s", result.get("transaction_id", "N/A")
        )
        return self._build_response(
            PurchaseErrorResponseSerializer,
            result,
            status.HTTP_409_CONFLICT,
        )


class PurchaseCancelView(BasePurchaseView):
    """
    API endpoint for cancelling a purchase (compensation).
    DELETE /purchases/<transaction_id>/cancel

    Part of Saga compensation flow.
    Always returns 200 OK.
    """

    def delete(self, _request: Request, transaction_id: str) -> Response:
        """
        Cancel a purchase transaction (compensation).

        Args:
            transaction_id: Transaction ID to cancel

        Response 200 OK (always):
        {
            "status": "success",
            "message": "Purchase cancelled successfully",
            "transaction_id": "uuid"
        }
        """
        logger.info("Cancellation requested for: %s", transaction_id)

        # Execute cancellation
        result = self.service.cancel_purchase(transaction_id)

        logger.info("Cancellation completed for: %s", transaction_id)

        # Always return 200 OK for compensation
        return self._build_response(
            CancelResponseSerializer,
            result,
            status.HTTP_200_OK,
        )
