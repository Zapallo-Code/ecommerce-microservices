"""
App configuration for purchases application.
"""
from django.apps import AppConfig


class PurchasesAppConfig(AppConfig):
    """Configuration for the purchases app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Purchases"
