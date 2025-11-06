"""
URLs for the payments microservice (Saga pattern).
"""
from django.urls import path
from .views import process_payment, compensate_payment

urlpatterns = [
    path('payment/', process_payment, name='process_payment'),
    path('payment/compensate/', compensate_payment, name='compensate_payment'),
]
