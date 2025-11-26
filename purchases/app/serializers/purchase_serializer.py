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


class PurchaseSuccessResponseSerializer(serializers.Serializer):
    """
    Serializer for successful purchase response (201 CREATED).

    Response format:
    {
        "status": "success",
        "purchase_id": "generated-id",
        "transaction_id": "uuid"
    }
    """

    status = serializers.CharField()
    purchase_id = serializers.IntegerField()
    transaction_id = serializers.CharField()


class PurchaseErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for failed purchase response (409 CONFLICT).

    Response format:
    {
        "status": "error",
        "message": "Purchase failed",
        "error": "CONFLICT",
        "current_status": "failed"  # Optional, only for duplicates
    }
    """

    status = serializers.CharField()
    message = serializers.CharField()
    error = serializers.CharField()
    current_status = serializers.CharField(required=False)


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
