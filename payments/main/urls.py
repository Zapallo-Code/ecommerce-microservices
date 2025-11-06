"""
URL configuration for payments project (ms-pagos).
Payments microservice for Saga architecture.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),  # Endpoints at root level: /payment/ and /payment/compensate/
]
