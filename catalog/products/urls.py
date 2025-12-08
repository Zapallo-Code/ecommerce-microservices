from django.urls import path
from .views import RandomProductView
from .health_views import HealthCheckView

urlpatterns = [
    path("products/random/", RandomProductView.as_view(), name="random-product"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
]
