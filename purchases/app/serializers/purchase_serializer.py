"""
Serializers for Purchase API endpoints.
Handles request/response serialization and validation for Saga pattern.
"""

from decimal import Decimal
from rest_framework import serializers


class PurchaseRequestSerializer(serializers.Serializer):
    """
    Serializer for creating a purchase (Saga transaction).

    Expected request from orchestrator:
    {
        "transaction_id": "uuid",
        "user_id": "string",
        "product_id": "string",
        "payment_id": "string",
        "amount": 100.50
    }
    """

    transaction_id = serializers.CharField(max_length=100)
    user_id = serializers.CharField(max_length=255)
    product_id = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    payment_id = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )

    def validate_amount(self, value):
        """Validate that amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def validate_quantity(self, value):
        """Validate that quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value


class PurchaseSuccessResponseSerializer(serializers.Serializer):
    """
    Serializer for successful purchase response (200 OK).

    Response format:
    {
        "status": "success",
        "purchase_id": "generated-id",
        "transaction_id": "uuid"
    }
    """

    status = serializers.CharField(default="success")
    purchase_id = serializers.IntegerField(source="id")
    transaction_id = serializers.CharField()


class PurchaseErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for failed purchase response (409 Conflict).

    Response format:
    {
        "status": "error",
        "message": "Purchase failed",
        "error": "CONFLICT"
    }
    """

    status = serializers.CharField(default="error")
    message = serializers.CharField()
    error = serializers.CharField()


class CancelResponseSerializer(serializers.Serializer):
    """
    Serializer for cancel/compensation response (200 OK).

    Response format:
    {
        "status": "success",
        "message": "Purchase cancelled successfully",
        "transaction_id": "uuid"
    }
    """

    status = serializers.CharField()
    message = serializers.CharField()
    transaction_id = serializers.CharField()
