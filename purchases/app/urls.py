"""
URL configuration for the app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import PurchaseViewSet

router = DefaultRouter()
router.register(r'purchases', PurchaseViewSet, basename='purchase')

urlpatterns = [
    path('', include(router.urls)),
]
