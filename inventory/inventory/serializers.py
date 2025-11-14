"""
Serializers for inventory API.
Simplified - removed RestoreInventorySerializer as inventory doesn't need compensation.
"""

from rest_framework import serializers


class DecreaseInventorySerializer(serializers.Serializer):
    """Serializer for decreasing inventory (compatible with orchestrator)."""

    product_id = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(default=1, min_value=1)

    def validate_quantity(self, value):
        """Validate that quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value
