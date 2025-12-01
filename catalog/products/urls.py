from django.urls import path
from .views import RandomProductView
from .health_views import CatalogHealthCheckView

urlpatterns = [
    path("products/random/", RandomProductView.as_view(), name="random-product"),
    path("health/", CatalogHealthCheckView.as_view(), name="catalog-health"),
]
