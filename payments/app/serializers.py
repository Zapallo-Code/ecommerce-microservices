"""
Serializers para el microservicio de pagos (Saga pattern).
"""
from rest_framework import serializers
from .models import Payment


class PaymentRequestSerializer(serializers.Serializer):
    """
    Serializer para validar requests de procesamiento de pagos desde orchestrator.
    Acepta: user_id, amount, product_id (según contrato con orchestrator)
    """
    user_id = serializers.CharField(
        max_length=100,
        required=True,
        help_text="ID del usuario que realiza el pago"
    )
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        help_text="Monto del pago"
    )
    product_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="ID del producto asociado al pago"
    )
    
    # Campos opcionales para flexibilidad
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
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Información adicional del pago"
    )


class PaymentResponseSerializer(serializers.Serializer):
    """
    Serializer para las respuestas de los endpoints de pago.
    Retorna payment_id según lo que espera el orchestrator.
    """
    payment_id = serializers.IntegerField(
        help_text="ID del pago procesado (requerido por orchestrator)"
    )
    status = serializers.ChoiceField(
        choices=['success', 'error', 'compensated'],
        help_text="Estado de la operación"
    )
    message = serializers.CharField(
        help_text="Mensaje descriptivo del resultado"
    )
    transaction_id = serializers.CharField(
        required=False,
        help_text="ID de la transacción procesada"
    )
    user_id = serializers.CharField(
        required=False,
        help_text="ID del usuario"
    )
    product_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="ID del producto"
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
            'user_id',
            'product_id',
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


class RefundRequestSerializer(serializers.Serializer):
    """
    Serializer para requests de reembolso/compensación desde orchestrator.
    """
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Transaction failed",
        help_text="Razón del reembolso"
    )
