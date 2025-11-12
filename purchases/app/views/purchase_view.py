"""
API Views for Purchase endpoints.
Implements REST API for purchase operations with Saga pattern.
Uses APIView instead of ViewSet for cleaner endpoint definitions.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging

from app.services.purchase_service import PurchaseService
from app.serializers.purchase_serializer import (
    PurchaseRequestSerializer,
    PurchaseSuccessResponseSerializer,
    PurchaseErrorResponseSerializer,
    CancelResponseSerializer
)

logger = logging.getLogger(__name__)


class PurchaseCreateView(APIView):
    """
    API endpoint for creating a purchase transaction.
    POST /purchases
    
    Implements Saga pattern with random success/failure (50%).
    Returns 200 OK for success or 409 Conflict for failure.
    """
    
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = PurchaseService()
    
    def post(self, request):
        """
        Create a new purchase transaction.
        
        Request body:
        {
            "transaction_id": "uuid",
            "user_id": "string",
            "product_id": "string",
            "payment_id": "string",
            "amount": 100.50
        }
        
        Response 200 OK:
        {
            "status": "success",
            "purchase_id": "generated-id",
            "transaction_id": "uuid"
        }
        
        Response 409 Conflict:
        {
            "status": "error",
            "message": "Purchase failed",
            "error": "CONFLICT"
        }
        """
        # Validate request
        serializer = PurchaseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                f"Invalid purchase request: {serializer.errors}"
            )
            return Response(
                {
                    'status': 'error',
                    'message': 'Invalid request data',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process purchase
        validated_data = serializer.validated_data
        result = self.service.create_purchase(
            transaction_id=validated_data['transaction_id'],
            user_id=validated_data['user_id'],
            product_id=validated_data['product_id'],
            payment_id=validated_data['payment_id'],
            amount=validated_data['amount']
        )
        
        # Return response based on result
        if result['status'] == 'success':
            # Success path - return 200 OK
            response_serializer = PurchaseSuccessResponseSerializer(
                data=result
            )
            response_serializer.is_valid()
            
            logger.info(
                f"Purchase created successfully: "
                f"{result['transaction_id']}"
            )
            
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        else:
            # Failure path - return 409 Conflict
            response_serializer = PurchaseErrorResponseSerializer(
                data=result
            )
            response_serializer.is_valid()
            
            logger.warning(
                f"Purchase failed: {result.get('transaction_id', 'N/A')}"
            )
            
            return Response(
                response_serializer.data,
                status=status.HTTP_409_CONFLICT
            )


class PurchaseCancelView(APIView):
    """
    API endpoint for cancelling a purchase (compensation).
    DELETE /purchases/<transaction_id>/cancel
    
    Part of Saga compensation flow.
    Always returns 200 OK.
    """
    
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = PurchaseService()
    
    def delete(self, request, transaction_id):
        """
        Cancel a purchase transaction (compensation).
        
        Args:
            transaction_id: Transaction ID to cancel
        
        Response 200 OK (always):
        {
            "status": "success",
            "message": "Purchase cancelled successfully",
            "transaction_id": "uuid"
        }
        """
        logger.info(f"Cancellation requested for: {transaction_id}")
        
        # Execute cancellation
        result = self.service.cancel_purchase(transaction_id)
        
        # Serialize response
        response_serializer = CancelResponseSerializer(data=result)
        response_serializer.is_valid()
        
        logger.info(
            f"Cancellation completed for: {transaction_id}"
        )
        
        # Always return 200 OK for compensation
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )
