"""
Pytest configuration and fixtures for Purchase tests.
"""
import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from app.models import Purchase, PurchaseDetail


@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()


@pytest.fixture
def sample_purchase_data():
    """Sample data for creating a purchase."""
    return {
        'customer_id': 1,
        'items': [
            {
                'product_id': 1,
                'quantity': 2,
                'unit_price': '29.99'
            },
            {
                'product_id': 2,
                'quantity': 1,
                'unit_price': '49.99'
            }
        ]
    }


@pytest.fixture
def sample_items():
    """Sample items list for purchase creation."""
    return [
        {
            'product_id': 1,
            'quantity': 2,
            'unit_price': Decimal('29.99')
        },
        {
            'product_id': 2,
            'quantity': 1,
            'unit_price': Decimal('49.99')
        }
    ]


@pytest.fixture
def created_purchase(db, sample_items):
    """Fixture that creates a purchase in the database."""
    from app.repositories import PurchaseRepository
    return PurchaseRepository.create_purchase(
        customer_id=1,
        items=sample_items,
        saga_id='test-saga-123'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )
