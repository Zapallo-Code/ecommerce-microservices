"""
API Views for Purchase endpoints.
Implements REST API for purchase operations with Saga pattern.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
import logging

from app.services import PurchaseService
from app.serializers import (
    PurchaseRequestSerializer,
    PurchaseResponseSerializer,
    PurchaseListSerializer,
    CompensateRequestSerializer,
    CompensateResponseSerializer
)

logger = logging.getLogger(__name__)


class PurchaseViewSet(viewsets.ViewSet):
    """
    ViewSet for purchase operations.
    Implements Saga orchestration endpoints.
    """
    
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = PurchaseService()
    
    @action(detail=False, methods=['post'], url_path='purchase')
    def create_purchase(self, request):
        """
        Create a new purchase using Saga pattern.
        Returns 200 with confirmed status or 409 with failed status.
        
        POST /api/purchases/purchase/
        {
            "customer_id": 1,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                    "unit_price": "29.99"
                }
            ]
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
                    'success': False,
                    'message': 'Invalid request data',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process purchase
        result = self.service.process_purchase(
            customer_id=serializer.validated_data['customer_id'],
            items=serializer.validated_data['items']
        )
        
        # Return response based on Saga result
        if result['success']:
            # Saga succeeded - return 200
            purchase = self.service.get_purchase(
                result['purchase_id']
            )
            purchase_data = PurchaseResponseSerializer(purchase).data
            
            return Response(
                {
                    'success': True,
                    'status': result['status'],
                    'message': result['message'],
                    'saga_id': result['saga_id'],
                    'purchase': purchase_data
                },
                status=status.HTTP_200_OK
            )
        else:
            # Saga failed - return 409 Conflict
            response_data = {
                'success': False,
                'status': result['status'],
                'message': result['message'],
                'error': result.get('error'),
                'saga_id': result.get('saga_id')
            }
            
            if 'purchase_id' in result:
                purchase = self.service.get_purchase(
                    result['purchase_id']
                )
                if purchase:
                    response_data['purchase'] = (
                        PurchaseResponseSerializer(purchase).data
                    )
            
            return Response(
                response_data,
                status=status.HTTP_409_CONFLICT
            )
    
    @action(detail=False, methods=['post'], url_path='compensate')
    def compensate_purchase(self, request):
        """
        Compensate (cancel) a purchase.
        Part of the Saga compensation flow.
        Always returns 200 OK.
        
        POST /api/purchases/compensate/
        {
            "purchase_id": 1
        }
        or
        {
            "saga_id": "uuid-here"
        }
        """
        # Validate request
        serializer = CompensateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(
                f"Invalid compensation request: {serializer.errors}"
            )
            return Response(
                {
                    'success': False,
                    'message': 'Invalid request data',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute compensation
        result = self.service.compensate_purchase(
            purchase_id=serializer.validated_data.get('purchase_id'),
            saga_id=serializer.validated_data.get('saga_id')
        )
        
        # Always return 200 for compensation endpoint
        response_serializer = CompensateResponseSerializer(data=result)
        response_serializer.is_valid()
        
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='list')
    def list_purchases(self, request):
        """
        List all purchases (for testing/debugging).
        
        GET /api/purchases/list/
        """
        customer_id = request.query_params.get('customer_id')
        
        if customer_id:
            purchases = self.service.get_customer_purchases(
                int(customer_id)
            )
        else:
            # For simplicity, get all purchases (limit 100)
            from app.repositories import PurchaseRepository
            purchases = PurchaseRepository.get_all(limit=100)
        
        serializer = PurchaseListSerializer(purchases, many=True)
        return Response(
            {
                'count': len(purchases),
                'purchases': serializer.data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def retrieve_purchase(self, request, pk=None):
        """
        Retrieve a specific purchase by ID.
        
        GET /api/purchases/{id}/
        """
        purchase = self.service.get_purchase(int(pk))
        
        if not purchase:
            return Response(
                {
                    'success': False,
                    'message': 'Purchase not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PurchaseResponseSerializer(purchase)
        return Response(
            {
                'success': True,
                'purchase': serializer.data
            },
            status=status.HTTP_200_OK
        )
