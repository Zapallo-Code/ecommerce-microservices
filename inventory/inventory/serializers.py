"""
Serializers for inventory API.
"""
from rest_framework import serializers


class DecreaseInventorySerializer(serializers.Serializer):
    """Serializer for decrease inventory request."""
    operation_id = serializers.UUIDField(required=True)
    product_id = serializers.IntegerField(required=True, min_value=1)
    quantity = serializers.IntegerField(required=True, min_value=1)
    metadata = serializers.JSONField(required=False, default=dict)


class CompensateInventorySerializer(serializers.Serializer):
    """Serializer for compensate inventory request."""
    operation_id = serializers.UUIDField(required=True)
    product_id = serializers.IntegerField(required=True, min_value=1)
    quantity = serializers.IntegerField(required=True, min_value=1)
    metadata = serializers.JSONField(required=False, default=dict)


class InventorySerializer(serializers.Serializer):
    """Serializer for inventory response."""
    product_id = serializers.IntegerField()
    stock = serializers.IntegerField()
    reserved = serializers.IntegerField()
    available = serializers.IntegerField()
