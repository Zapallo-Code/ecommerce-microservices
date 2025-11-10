"""
Serializers for Purchase API endpoints.
Handles request/response serialization and validation.
"""
from rest_framework import serializers
from app.models import Purchase, PurchaseDetail


class PurchaseDetailSerializer(serializers.ModelSerializer):
    """Serializer for purchase detail items."""
    
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseDetail
        fields = [
            'id',
            'product_id',
            'quantity',
            'unit_price',
            'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']
    
    def get_subtotal(self, obj):
        """Calculate subtotal for the detail."""
        return obj.get_subtotal()


class PurchaseDetailRequestSerializer(serializers.Serializer):
    """Serializer for purchase detail in requests."""
    
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0
    )


class PurchaseRequestSerializer(serializers.Serializer):
    """Serializer for creating a purchase."""
    
    customer_id = serializers.IntegerField(min_value=1)
    items = PurchaseDetailRequestSerializer(many=True, min_length=1)
    
    def validate_items(self, value):
        """Validate that items list is not empty."""
        if not value:
            raise serializers.ValidationError(
                "At least one item is required"
            )
        return value


class PurchaseResponseSerializer(serializers.ModelSerializer):
    """Serializer for purchase responses."""
    
    details = PurchaseDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Purchase
        fields = [
            'id',
            'customer_id',
            'total_amount',
            'status',
            'saga_id',
            'created_at',
            'updated_at',
            'details',
            'error_message'
        ]
        read_only_fields = fields


class PurchaseListSerializer(serializers.ModelSerializer):
    """Simplified serializer for purchase lists."""
    
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Purchase
        fields = [
            'id',
            'customer_id',
            'total_amount',
            'status',
            'saga_id',
            'created_at',
            'items_count'
        ]
        read_only_fields = fields
    
    def get_items_count(self, obj):
        """Get count of items in purchase."""
        return obj.details.count()


class CompensateRequestSerializer(serializers.Serializer):
    """Serializer for compensation requests."""
    
    purchase_id = serializers.IntegerField(
        required=False,
        min_value=1
    )
    saga_id = serializers.CharField(
        required=False,
        max_length=100
    )
    
    def validate(self, data):
        """Validate that at least one identifier is provided."""
        if not data.get('purchase_id') and not data.get('saga_id'):
            raise serializers.ValidationError(
                "Either purchase_id or saga_id must be provided"
            )
        return data


class CompensateResponseSerializer(serializers.Serializer):
    """Serializer for compensation responses."""
    
    success = serializers.BooleanField()
    status = serializers.CharField(required=False)
    purchase_id = serializers.IntegerField(required=False)
    saga_id = serializers.CharField(required=False)
    message = serializers.CharField()
    error = serializers.CharField(required=False)
