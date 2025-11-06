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
    Simulates payment processing in a distributed transaction (Saga).
    
    Returns:
    - 200 OK: Payment processed successfully
    - 409 CONFLICT: Error processing payment (random failure)
    
    Simulates realistic latency and records the transaction in the database.
    """
    # Validate request
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
    
    # Extract validated data
    data = serializer.validated_data
    transaction_id = data.get('transaction_id') or str(uuid.uuid4())
    order_id = data.get('order_id')
    amount = data.get('amount')
    
    # Simulate processing latency (0.5 to 2 seconds)
    time.sleep(random.uniform(0.5, 2.0))
    
    # Random decision: success or failure (50/50)
    is_success = random.choice([True, False])
    
    if is_success:
        # Record successful payment
        payment = Payment.objects.create(
            transaction_id=transaction_id,
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
            "status": "success",
            "message": "Payment processed successfully",
            "transaction_id": transaction_id,
            "order_id": order_id,
            "amount": str(amount) if amount else None
        }
        
        return Response(
            response_data,
            status=status.HTTP_200_OK
        )
    else:
        # Record payment failure
        payment = Payment.objects.create(
            transaction_id=transaction_id,
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
            "status": "error",
            "message": "Error processing payment",
            "transaction_id": transaction_id,
            "order_id": order_id
        }
        
        return Response(
            response_data,
            status=status.HTTP_409_CONFLICT
        )


@api_view(["POST"])
def compensate_payment(request):
    """
    Performs compensation (reversal) of a payment in a Saga transaction.
    
    Always returns 200 OK to guarantee transaction reversal.
    Simulates compensation latency (0.2 to 1 second).
    
    This endpoint is called when a later step in the Saga fails
    and it's necessary to revert a previously processed payment.
    """
    # Validate request
    serializer = PaymentRequestSerializer(data=request.data)
    if not serializer.is_valid():
        # Even with invalid data, we compensate successfully
        # to not block the Saga reversal
        return Response(
            {
                "status": "compensated",
                "message": "Payment reversed successfully (without full validation)",
                "warning": "Some input data was invalid"
            },
            status=status.HTTP_200_OK
        )
    
    # Extract validated data
    data = serializer.validated_data
    transaction_id = data.get('transaction_id')
    order_id = data.get('order_id')
    
    # Simulate compensation latency (0.2 to 1 second)
    time.sleep(random.uniform(0.2, 1.0))
    
    # Find the original payment and update it
    if transaction_id:
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            payment.status = Payment.Status.COMPENSATED
            payment.message = "Payment reversed successfully"
            payment.compensated_at = datetime.now()
            payment.metadata["compensated_at"] = datetime.now().isoformat()
            payment.save()
            
            response_data = {
                "status": "compensated",
                "message": "Payment reversed successfully",
                "transaction_id": transaction_id,
                "order_id": order_id
            }
        except Payment.DoesNotExist:
            # Register new compensation entry even if original payment doesn't exist
            Payment.objects.create(
                transaction_id=transaction_id or str(uuid.uuid4()),
                order_id=order_id,
                status=Payment.Status.COMPENSATED,
                message="Payment reversed (original not found)",
                compensated_at=datetime.now(),
                metadata={
                    "compensated_at": datetime.now().isoformat(),
                    "original_not_found": True,
                    "request_data": request.data
                }
            )
            
            response_data = {
                "status": "compensated",
                "message": "Payment reversed successfully",
                "transaction_id": transaction_id,
                "order_id": order_id,
                "note": "Original payment not found, but compensation recorded"
            }
    else:
        # Without transaction_id, create generic compensation record
        new_transaction_id = str(uuid.uuid4())
        Payment.objects.create(
            transaction_id=new_transaction_id,
            order_id=order_id,
            status=Payment.Status.COMPENSATED,
            message="Compensation without original transaction_id",
            compensated_at=datetime.now(),
            metadata={
                "compensated_at": datetime.now().isoformat(),
                "request_data": request.data
            }
        )
        
        response_data = {
            "status": "compensated",
            "message": "Payment reversed successfully",
            "transaction_id": new_transaction_id,
            "order_id": order_id
        }
    
    return Response(
        response_data,
        status=status.HTTP_200_OK
    )
