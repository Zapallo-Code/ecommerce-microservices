from django.urls import path

from app.views.health_view import HealthCheckView
from app.views.purchase_view import PurchaseCancelView, PurchaseCreateView

urlpatterns = [
    # Health check
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # POST /purchases/ - Create purchase transaction
    path("purchases/", PurchaseCreateView.as_view(), name="purchase-create"),
    # DELETE /purchases/<transaction_id>/cancel/ - Cancel purchase
    path(
        "purchases/<str:transaction_id>/cancel/",
        PurchaseCancelView.as_view(),
        name="purchase-cancel",
    ),
]
