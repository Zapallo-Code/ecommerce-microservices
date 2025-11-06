"""
Serializers para el microservicio de pagos (Saga pattern).
"""
from rest_framework import serializers
from .models import Payment


class PaymentRequestSerializer(serializers.Serializer):
    """
    Serializer para validar requests de procesamiento y compensación de pagos.
    Campos opcionales para flexibilidad en la Saga.
    """
    transaction_id = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="ID único de la transacción. Se genera automáticamente si no se provee."
    )
    order_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text="ID de la orden asociada al pago"
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Monto del pago"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Información adicional del pago"
    )


class PaymentResponseSerializer(serializers.Serializer):
    """
    Serializer para las respuestas de los endpoints de pago.
    """
    status = serializers.ChoiceField(
        choices=['success', 'error', 'compensado'],
        help_text="Estado de la operación"
    )
    message = serializers.CharField(
        help_text="Mensaje descriptivo del resultado"
    )
    transaction_id = serializers.CharField(
        required=False,
        help_text="ID de la transacción procesada"
    )
    order_id = serializers.CharField(
        required=False,
        help_text="ID de la orden asociada"
    )
    amount = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Monto del pago"
    )


class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Payment (usado para consultas).
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'transaction_id',
            'order_id',
            'amount',
            'status',
            'status_display',
            'message',
            'metadata',
            'created_at',
            'updated_at',
            'compensated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
