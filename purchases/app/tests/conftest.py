"""
Pytest configuration and fixtures for Purchase tests (Saga pattern).
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from app.models import Purchase


@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()


@pytest.fixture
def sample_purchase_data():
    """Sample data for creating a purchase (Saga format)."""
    return {
        'transaction_id': 'test-txn-001',
        'user_id': 'user-123',
        'product_id': 'prod-456',
        'payment_id': 'pay-789',
        'amount': 100.50
    }


@pytest.fixture
def created_purchase(db):
    """Fixture that creates a purchase in the database."""
    return Purchase.objects.create(
        transaction_id='test-txn-fixture',
        user_id='user-123',
        product_id='prod-456',
        payment_id='pay-789',
        amount=Decimal('100.00'),
        status=Purchase.STATUS_PENDING
    )


@pytest.fixture
def another_purchase(db):
    """Fixture for a second purchase."""
    return Purchase.objects.create(
        transaction_id='test-txn-002',
        user_id='user-456',
        product_id='prod-789',
        payment_id='pay-012',
        amount=Decimal('50.00'),
        status=Purchase.STATUS_PENDING
    )
