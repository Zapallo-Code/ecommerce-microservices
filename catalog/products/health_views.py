"""
Health Check Views para el microservicio de Catálogo

Este módulo contiene endpoints de monitoreo y diagnóstico
para verificar el estado del servicio de catálogo.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError

from .models import Product


class CatalogHealthCheckView(APIView):
    """
    Vista de health check para el microservicio de catálogo.
    
    Este endpoint permite verificar que el servicio está funcionando
    correctamente y puede acceder a sus recursos necesarios.
    """
    
    def get(self, request):
        """
        GET /catalog/health/
        
        Retorna el estado de salud del microservicio de catálogo.
        
        Returns:
            200: Servicio saludable
            503: Servicio no disponible
        """
        return Response(
            {
                "status": "ok",
                "service": "catalog",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )


class CatalogDetailedHealthCheckView(APIView):
    """
    Vista de health check detallado para el microservicio de catálogo.
    
    Este endpoint proporciona información más detallada sobre el estado
    del servicio, incluyendo la conectividad con la base de datos y
    estadísticas básicas.
    """
    
    def get(self, request):
        """
        GET /catalog/health/detailed/
        
        Retorna información detallada del estado del servicio.
        
        Returns:
            200: Servicio saludable con detalles
            503: Servicio no disponible
        """
        health_data = {
            "status": "ok",
            "service": "catalog",
            "timestamp": timezone.now().isoformat(),
            "checks": {}
        }
        
        # Verificar conexión a la base de datos
        try:
            connection.ensure_connection()
            health_data["checks"]["database"] = {
                "status": "ok",
                "message": "Database connection successful"
            }
        except OperationalError as e:
            health_data["status"] = "degraded"
            health_data["checks"]["database"] = {
                "status": "error",
                "message": f"Database connection failed: {str(e)}"
            }
        
        # Verificar que se puede consultar productos
        try:
            total_products = Product.objects.count()
            active_products = Product.objects.filter(is_active=True).count()
            products_with_stock = Product.objects.filter(
                is_active=True,
                stock__gt=0
            ).count()
            
            health_data["checks"]["products"] = {
                "status": "ok",
                "total": total_products,
                "active": active_products,
                "available": products_with_stock
            }
        except Exception as e:
            health_data["status"] = "degraded"
            health_data["checks"]["products"] = {
                "status": "error",
                "message": f"Error querying products: {str(e)}"
            }
        
        # Determinar el código de estado HTTP
        if health_data["status"] == "ok":
            http_status = status.HTTP_200_OK
        else:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=http_status)


class CatalogReadinessCheckView(APIView):
    """
    Vista de readiness check para el microservicio de catálogo.
    
    Este endpoint verifica si el servicio está listo para recibir tráfico.
    Útil para orquestadores como Kubernetes.
    """
    
    def get(self, request):
        """
        GET /catalog/health/ready/
        
        Verifica si el servicio está listo para procesar solicitudes.
        
        Returns:
            200: Servicio listo
            503: Servicio no listo
        """
        try:
            # Verificar conexión a la base de datos
            connection.ensure_connection()
            
            # Verificar que se puede hacer una consulta básica
            Product.objects.exists()
            
            return Response(
                {
                    "status": "ready",
                    "service": "catalog",
                    "timestamp": timezone.now().isoformat()
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {
                    "status": "not_ready",
                    "service": "catalog",
                    "timestamp": timezone.now().isoformat(),
                    "error": str(e)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class CatalogLivenessCheckView(APIView):
    """
    Vista de liveness check para el microservicio de catálogo.
    
    Este endpoint verifica si el servicio está vivo y respondiendo.
    Útil para detectar si el servicio necesita ser reiniciado.
    """
    
    def get(self, request):
        """
        GET /catalog/health/live/
        
        Verifica si el servicio está vivo.
        
        Returns:
            200: Servicio vivo
        """
        return Response(
            {
                "status": "alive",
                "service": "catalog",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
