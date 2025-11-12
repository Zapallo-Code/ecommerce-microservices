"""
Saga Views para el microservicio de Catálogo

Este módulo contiene views especializados para manejar operaciones
relacionadas con el patrón Saga en transacciones distribuidas.

Los endpoints aquí definidos son utilizados por el orquestador del Saga
para coordinar operaciones de reserva, confirmación y compensación de productos.
"""

import random
import time
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from .models import Product
from .serializers import ProductSerializer, ProductRandomSerializer

logger = logging.getLogger(__name__)


class SagaRandomProductView(APIView):
    """
    Vista para obtener un producto aleatorio (usado por el Saga).
    
    Este endpoint es llamado por el orquestador del Saga para seleccionar
    un producto aleatorio que será usado en el flujo de la transacción distribuida.
    
    Incluye simulación de latencia y posibles errores para testing realista.
    """
    
    def get(self, request):
        """
        GET /api/saga/products/random/
        
        Retorna un producto aleatorio activo con stock disponible.
        
        Returns:
            200: Producto aleatorio encontrado
            404: No hay productos disponibles
            500: Error interno simulado (10% probabilidad)
        """
        # Simular latencia de procesamiento entre 0.1 y 0.5 segundos
        time.sleep(random.uniform(0.1, 0.5))
        
        # Simular error aleatorio con 10% de probabilidad
        if random.random() < 0.1:
            logger.error("Saga: Simulated internal server error in random product selection")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Obtener productos activos con stock disponible
        products = Product.objects.filter(
            is_active=True,
            stock__gt=0
        )
        
        if not products.exists():
            logger.warning("Saga: No products available for random selection")
            return Response(
                {"error": "No products available"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Seleccionar un producto aleatorio
        product = random.choice(list(products))
        serializer = ProductRandomSerializer(product)
        
        logger.info(f"Saga: Random product selected - ID: {product.id}, Name: {product.name}")
        return Response(serializer.data, status=status.HTTP_200_OK)


class SagaReserveProductView(APIView):
    """
    Vista para reservar stock de un producto (Fase de preparación del Saga).
    
    Este endpoint reserva temporalmente el stock de un producto durante
    la transacción distribuida. El stock se resta pero el producto se marca
    como "reservado" hasta que se confirme o compense la transacción.
    """
    
    def post(self, request):
        """
        POST /api/saga/products/reserve/
        
        Body:
        {
            "product_id": 123,
            "quantity": 2,
            "saga_transaction_id": "uuid-string"
        }
        
        Returns:
            200: Reserva exitosa
            400: Datos inválidos
            404: Producto no encontrado
            409: Stock insuficiente
            500: Error interno
        """
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        saga_transaction_id = request.data.get('saga_transaction_id')
        
        # Validar datos de entrada
        if not product_id or not saga_transaction_id:
            return Response(
                {"error": "product_id and saga_transaction_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(quantity, int) or quantity <= 0:
            return Response(
                {"error": "quantity must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Obtener el producto con lock para evitar race conditions
                product = Product.objects.select_for_update().get(
                    id=product_id,
                    is_active=True
                )
                
                # Verificar stock disponible
                if product.stock < quantity:
                    logger.warning(
                        f"Saga: Insufficient stock for product {product_id}. "
                        f"Requested: {quantity}, Available: {product.stock}"
                    )
                    return Response(
                        {
                            "error": "Insufficient stock",
                            "available": product.stock,
                            "requested": quantity
                        },
                        status=status.HTTP_409_CONFLICT
                    )
                
                # Reservar el stock (restar del inventario)
                product.stock -= quantity
                product.updated_at = timezone.now()
                product.save()
                
                logger.info(
                    f"Saga: Stock reserved - Transaction: {saga_transaction_id}, "
                    f"Product: {product_id}, Quantity: {quantity}, Remaining: {product.stock}"
                )
                
                return Response(
                    {
                        "message": "Stock reserved successfully",
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity_reserved": quantity,
                        "remaining_stock": product.stock,
                        "saga_transaction_id": saga_transaction_id
                    },
                    status=status.HTTP_200_OK
                )
                
        except Product.DoesNotExist:
            logger.error(f"Saga: Product not found - ID: {product_id}")
            return Response(
                {"error": f"Product with id {product_id} not found or inactive"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Saga: Error reserving stock - {str(e)}")
            return Response(
                {"error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SagaConfirmProductView(APIView):
    """
    Vista para confirmar la reserva de un producto (Fase de confirmación del Saga).
    
    Este endpoint confirma que la transacción fue exitosa y que el stock
    reservado se mantiene. En esta implementación, como el stock ya fue
    restado en la fase de reserva, simplemente registramos la confirmación.
    """
    
    def post(self, request):
        """
        POST /api/saga/products/confirm/
        
        Body:
        {
            "product_id": 123,
            "quantity": 2,
            "saga_transaction_id": "uuid-string"
        }
        
        Returns:
            200: Confirmación exitosa
            400: Datos inválidos
            404: Producto no encontrado
        """
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        saga_transaction_id = request.data.get('saga_transaction_id')
        
        # Validar datos de entrada
        if not product_id or not saga_transaction_id:
            return Response(
                {"error": "product_id and saga_transaction_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
            
            logger.info(
                f"Saga: Reservation confirmed - Transaction: {saga_transaction_id}, "
                f"Product: {product_id}, Quantity: {quantity}"
            )
            
            return Response(
                {
                    "message": "Reservation confirmed successfully",
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity_confirmed": quantity,
                    "current_stock": product.stock,
                    "saga_transaction_id": saga_transaction_id
                },
                status=status.HTTP_200_OK
            )
            
        except Product.DoesNotExist:
            logger.error(f"Saga: Product not found for confirmation - ID: {product_id}")
            return Response(
                {"error": f"Product with id {product_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class SagaCompensateProductView(APIView):
    """
    Vista para compensar (revertir) la reserva de un producto (Fase de compensación del Saga).
    
    Este endpoint restaura el stock del producto cuando la transacción distribuida
    falla y necesita ser revertida. Es la acción de compensación del patrón Saga.
    """
    
    def post(self, request):
        """
        POST /api/saga/products/compensate/
        
        Body:
        {
            "product_id": 123,
            "quantity": 2,
            "saga_transaction_id": "uuid-string"
        }
        
        Returns:
            200: Compensación exitosa
            400: Datos inválidos
            404: Producto no encontrado
            500: Error interno
        """
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        saga_transaction_id = request.data.get('saga_transaction_id')
        
        # Validar datos de entrada
        if not product_id or not saga_transaction_id:
            return Response(
                {"error": "product_id and saga_transaction_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(quantity, int) or quantity <= 0:
            return Response(
                {"error": "quantity must be a positive integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Obtener el producto con lock
                product = Product.objects.select_for_update().get(id=product_id)
                
                # Restaurar el stock (devolver el inventario)
                product.stock += quantity
                product.updated_at = timezone.now()
                product.save()
                
                logger.info(
                    f"Saga: Compensation executed - Transaction: {saga_transaction_id}, "
                    f"Product: {product_id}, Quantity restored: {quantity}, "
                    f"New stock: {product.stock}"
                )
                
                return Response(
                    {
                        "message": "Compensation executed successfully",
                        "product_id": product.id,
                        "product_name": product.name,
                        "quantity_restored": quantity,
                        "current_stock": product.stock,
                        "saga_transaction_id": saga_transaction_id
                    },
                    status=status.HTTP_200_OK
                )
                
        except Product.DoesNotExist:
            logger.error(f"Saga: Product not found for compensation - ID: {product_id}")
            return Response(
                {"error": f"Product with id {product_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Saga: Error during compensation - {str(e)}")
            return Response(
                {"error": "Internal server error during compensation"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SagaProductStatusView(APIView):
    """
    Vista para consultar el estado de un producto en el contexto del Saga.
    
    Endpoint auxiliar que permite al orquestador verificar el estado actual
    de un producto, incluyendo su disponibilidad y stock.
    """
    
    def get(self, request, product_id):
        """
        GET /api/saga/products/{product_id}/status/
        
        Returns:
            200: Estado del producto
            404: Producto no encontrado
        """
        try:
            product = Product.objects.get(id=product_id)
            
            return Response(
                {
                    "product_id": product.id,
                    "name": product.name,
                    "price": str(product.price),
                    "stock": product.stock,
                    "is_active": product.is_active,
                    "is_available": product.stock > 0 and product.is_active,
                    "category": product.category,
                    "last_updated": product.updated_at.isoformat()
                },
                status=status.HTTP_200_OK
            )
            
        except Product.DoesNotExist:
            return Response(
                {"error": f"Product with id {product_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
