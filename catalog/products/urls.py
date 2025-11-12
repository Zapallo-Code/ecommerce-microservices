from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet
from .health_views import (
    CatalogHealthCheckView,
    CatalogDetailedHealthCheckView,
    CatalogReadinessCheckView,
    CatalogLivenessCheckView,
)

# Create a router and register our viewset
router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    
    # Saga-specific endpoints
    path('saga/products/', include('products.saga_urls')),
    
    # Health check endpoints
    path('catalog/health/', CatalogHealthCheckView.as_view(), name='catalog-health'),
    path('catalog/health/detailed/', CatalogDetailedHealthCheckView.as_view(), name='catalog-health-detailed'),
    path('catalog/health/ready/', CatalogReadinessCheckView.as_view(), name='catalog-readiness'),
    path('catalog/health/live/', CatalogLivenessCheckView.as_view(), name='catalog-liveness'),
]

