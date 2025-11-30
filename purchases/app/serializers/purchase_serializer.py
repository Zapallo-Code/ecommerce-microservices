from decimal import Decimal

from rest_framework import serializers


class PurchaseRequestSerializer(serializers.Serializer):  # noqa: D101
    transaction_id = serializers.CharField(max_length=100)
    user_id = serializers.CharField(max_length=255)
    product_id = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    payment_id = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )


class PurchaseSuccessResponseSerializer(serializers.Serializer):  # noqa: D101
    status = serializers.CharField()
    purchase_id = serializers.IntegerField()
    transaction_id = serializers.CharField()


class PurchaseErrorResponseSerializer(serializers.Serializer):  # noqa: D101
    status = serializers.CharField()
    message = serializers.CharField()
    error = serializers.CharField()
    current_status = serializers.CharField(required=False)


class CancelResponseSerializer(serializers.Serializer):  # noqa: D101
    status = serializers.CharField()
    message = serializers.CharField()
    transaction_id = serializers.CharField()
