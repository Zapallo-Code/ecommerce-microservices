from rest_framework import serializers


class BaseInventoryOperationSerializer(serializers.Serializer):
    """Base serializer for inventory operations."""

    operation_id = serializers.UUIDField(required=True)
    product_id = serializers.IntegerField(required=True, min_value=1)
    quantity = serializers.IntegerField(required=True, min_value=1)
    metadata = serializers.JSONField(required=False, default=dict)


class DecreaseInventorySerializer(BaseInventoryOperationSerializer):
    """Serializer for decrease inventory request."""

    pass


class CompensateInventorySerializer(BaseInventoryOperationSerializer):
    """Serializer for compensate inventory request."""

    pass


class InventorySerializer(serializers.Serializer):
    """Serializer for inventory response."""

    product_id = serializers.IntegerField()
    stock = serializers.IntegerField()
    reserved = serializers.IntegerField()
    available = serializers.IntegerField()
