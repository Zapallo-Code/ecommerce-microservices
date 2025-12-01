from django.urls import path
from .views import process_payment, refund_payment, health_check

urlpatterns = [
    path("payments/health/", health_check, name="health_check"),
    path("payments/", process_payment, name="process_payment"),
    path("payments/<int:payment_id>/refund/", refund_payment, name="refund_payment"),
]
