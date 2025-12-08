from django.urls import path

from app.views.health_view import HealthCheckView
from app.views.purchase_view import PurchaseCancelView, PurchaseCreateView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("purchases/", PurchaseCreateView.as_view(), name="purchase-create"),
    path(
        "purchases/<str:transaction_id>/cancel/",
        PurchaseCancelView.as_view(),
        name="purchase-cancel",
    ),
]
