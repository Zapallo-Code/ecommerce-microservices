"""
URL configuration for the app.
Defines endpoints for Saga pattern operations.
"""
from django.urls import path
from app.views.purchase_view import (
    PurchaseCreateView,
    PurchaseCancelView
)

urlpatterns = [
    # POST /purchases - Create purchase transaction
    path('purchases', PurchaseCreateView.as_view(), name='purchase-create'),
    
    # DELETE /purchases/<transaction_id>/cancel - Cancel purchase
    path(
        'purchases/<str:transaction_id>/cancel',
        PurchaseCancelView.as_view(),
        name='purchase-cancel'
    ),
]
