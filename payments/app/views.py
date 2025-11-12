"""
Views for the payments microservice.
Implements the Saga pattern with processing and compensation endpoints.
"""
import random
import time
import uuid
from datetime import datetime

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .models import Payment
from .serializers import PaymentRequestSerializer


@api_view(["POST"])
def process_payment(request):
    """
    Procesa un pago en una transacción distribuida (Saga).
    
    Endpoint: POST /payments
    Payload esperado: {"user_id": str, "amount": decimal, "product_id": str}
    
    Returns:
    - 200 OK: Pago procesado exitosamente (retorna payment_id)
    - 409 CONFLICT: Error procesando el pago (fallo aleatorio)
    
    Simula latencia realista y registra la transacción en la base de datos.
    """
    # Validar request
    serializer = PaymentRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "message": "Invalid data",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Extraer datos validados
    data = serializer.validated_data
    user_id = data.get('user_id')
    amount = data.get('amount')
    product_id = data.get('product_id')
    transaction_id = data.get('transaction_id') or str(uuid.uuid4())
    order_id = data.get('order_id')
    
    # Simular latencia de procesamiento (0.5 a 2 segundos)
    time.sleep(random.uniform(0.5, 2.0))
    
    # Decisión aleatoria: éxito o fallo (50/50)
    is_success = random.choice([True, False])
    
    if is_success:
        # Registrar pago exitoso
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            user_id=user_id,
            product_id=product_id,
            order_id=order_id,
            amount=amount,
            status=Payment.Status.SUCCESS,
            message="Payment processed successfully",
            metadata={
                "processed_at": datetime.now().isoformat(),
                "request_data": request.data
            }
        )
        
        response_data = {
            "payment_id": payment.id,  # ← CRÍTICO: orchestrator espera payment_id
            "status": "success",
            "message": "Payment processed successfully",
            "transaction_id": transaction_id,
            "user_id": user_id,
            "product_id": product_id,
            "amount": str(amount)
        }
        
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )
    else:
        # Registrar fallo del pago
        payment = Payment.objects.create(
            transaction_id=transaction_id,
            user_id=user_id,
            product_id=product_id,
            order_id=order_id,
            amount=amount,
            status=Payment.Status.ERROR,
            message="Error processing payment",
            metadata={
                "failed_at": datetime.now().isoformat(),
                "request_data": request.data,
                "error_type": "random_failure"
            }
        )
        
        response_data = {
            "payment_id": payment.id,  # ← Retornar payment_id incluso en error
            "status": "error",
            "message": "Error processing payment",
            "transaction_id": transaction_id,
            "user_id": user_id,
            "product_id": product_id
        }
        
        return Response(
            response_data,
            status=status.HTTP_409_CONFLICT
        )


@api_view(["POST"])
def refund_payment(request, payment_id):
    """
    Realiza la compensación (reversión) de un pago en una transacción Saga.
    
    Endpoint: POST /payments/{payment_id}/refund
    Payload esperado: {"reason": str} (opcional)
    
    Siempre retorna 200 OK para garantizar la reversión de la transacción.
    Simula latencia de compensación (0.2 a 1 segundo).
    
    Este endpoint es llamado cuando un paso posterior en la Saga falla
    y es necesario revertir un pago procesado previamente.
    """
    # Importar el serializer
    from .serializers import RefundRequestSerializer
    
    # Validar request (flexible, no bloquea compensación)
    serializer = RefundRequestSerializer(data=request.data)
    if not serializer.is_valid():
        # Incluso con datos inválidos, compensamos exitosamente
        # para no bloquear la reversión de la Saga
        reason = "Transaction failed"
    else:
        reason = serializer.validated_data.get('reason', 'Transaction failed')
    
    # Simular latencia de compensación (0.2 a 1 segundo)
    time.sleep(random.uniform(0.2, 1.0))
    
    # Buscar el pago original y actualizarlo
    try:
        payment = Payment.objects.get(id=payment_id)
        payment.status = Payment.Status.COMPENSATED
        payment.message = f"Payment refunded: {reason}"
        payment.compensated_at = datetime.now()
        payment.metadata["compensated_at"] = datetime.now().isoformat()
        payment.metadata["refund_reason"] = reason
        payment.save()
        
        response_data = {
            "status": "compensated",
            "message": "Payment refunded successfully",
            "payment_id": payment.id,
            "transaction_id": payment.transaction_id,
            "user_id": payment.user_id,
            "amount": str(payment.amount) if payment.amount else None
        }
    except Payment.DoesNotExist:
        # Si el pago no existe, igual retornamos 200 OK
        # para no bloquear la compensación de la Saga
        response_data = {
            "status": "compensated",
            "message": f"Payment {payment_id} not found, but compensation acknowledged",
            "payment_id": payment_id,
            "note": "Original payment not found"
        }
    
    return Response(
        response_data,
        status=status.HTTP_200_OK
    )
