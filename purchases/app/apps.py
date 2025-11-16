"""
App configuration for purchases application.
"""
from django.apps import AppConfig


class AppConfig(AppConfig):
    """Configuration for the app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    verbose_name = 'Purchases'
