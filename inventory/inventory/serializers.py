"""
Serializers for inventory API.
"""
from rest_framework import serializers


class DecreaseInventorySerializer(serializers.Serializer):
    """Serializer compatible con orchestrator."""
    product_id = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(default=1, min_value=1)


class RestoreInventorySerializer(serializers.Serializer):
    """Serializer para compensación."""
    quantity = serializers.IntegerField(default=1, min_value=1)


class InventorySerializer(serializers.Serializer):
    """Serializer for inventory response."""
    product_id = serializers.CharField()
    stock = serializers.IntegerField()
    reserved = serializers.IntegerField()
    available = serializers.IntegerField()
