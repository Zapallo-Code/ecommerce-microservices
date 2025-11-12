"""
API views for inventory microservice.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db import transaction
from .services import InventoryService
from .serializers import (
    DecreaseInventorySerializer,
    RestoreInventorySerializer,
    InventorySerializer
)

logger = logging.getLogger(__name__)


class DecreaseInventoryView(APIView):
    """
    POST /inventory/decrease/
    Decrease product stock. Returns 200 or 409 (no stock).
    """
    
    def post(self, request):
        serializer = DecreaseInventorySerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Invalid data for decrease inventory: {serializer.errors}")
            return Response(
                {"error": "Invalid data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        transaction_id = request.data.get('transaction_id')
        
        logger.info(f"Decrease inventory request - product_id: {product_id}, quantity: {quantity}, transaction_id: {transaction_id}")
        
        try:
            with transaction.atomic():
                result = InventoryService.decrease_inventory(
                    product_id=product_id,
                    quantity=quantity,
                    transaction_id=transaction_id
                )
                
                logger.info(f"Inventory decreased successfully - product_id: {product_id}, operation_id: {result.get('operation_id')}")
                return Response(result, status=status.HTTP_200_OK)
                
        except ValueError as e:
            logger.error(f"Insufficient stock - product_id: {product_id}, error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_409_CONFLICT
            )
        except Exception as e:
            logger.error(f"Error decreasing inventory - product_id: {product_id}, error: {str(e)}")
            return Response(
                {"error": "Internal server error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RestoreInventoryView(APIView):
    """
    POST /inventory/{product_id}/restore/
    Restore (compensate) product stock. Always returns 200.
    """
    
    def post(self, request, product_id):
        serializer = RestoreInventorySerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Invalid data for restore inventory: {serializer.errors}")
            return Response(
                {"error": "Invalid data", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quantity = serializer.validated_data['quantity']
        transaction_id = request.data.get('transaction_id')
        
        logger.info(f"Restore inventory request - product_id: {product_id}, quantity: {quantity}, transaction_id: {transaction_id}")
        
        try:
            with transaction.atomic():
                result = InventoryService.restore_inventory(
                    product_id=product_id,
                    quantity=quantity,
                    transaction_id=transaction_id
                )
                
                logger.info(f"Inventory restored successfully - product_id: {product_id}")
                return Response(result, status=status.HTTP_200_OK)
                
        except ValueError as e:
            logger.error(f"Error restoring inventory - product_id: {product_id}, error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error restoring inventory - product_id: {product_id}, error: {str(e)}")
            return Response(
                {"error": "Internal server error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryDetailView(APIView):
    """
    GET /inventory/{product_id}/
    Get inventory details for a product.
    """
    
    def get(self, request, product_id):
        result = InventoryService.get_inventory(product_id)
        
        if result is None:
            return Response(
                {'error': f'Product {product_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = InventorySerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HealthCheckView(APIView):
    """
    GET /inventory/health/
    Health check endpoint for orchestrator/Traefik.
    """
    
    def get(self, request):
        return Response(
            {
                'status': 'healthy',
                'service': 'inventory',
                'version': '1.0.0'
            },
            status=status.HTTP_200_OK
        )
