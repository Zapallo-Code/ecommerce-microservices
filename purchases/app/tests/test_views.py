"""
Integration tests for Purchase API Views (Saga pattern).
"""
import pytest
from unittest.mock import patch
from decimal import Decimal
from rest_framework import status
from app.models import Purchase


@pytest.mark.django_db
@pytest.mark.integration
class TestPurchaseViewSet:
    """Integration tests for Purchase Saga endpoints."""
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_success(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test successful purchase creation (Saga success)."""
        mock_random.return_value = 0.3  # Will succeed (< 0.5)
        
        response = api_client.post(
            '/api/purchases',
            sample_purchase_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'purchase_id' in response.data
        assert response.data['transaction_id'] == 'test-txn-001'
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_failure(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test failed purchase creation (Saga failure - 409 Conflict)."""
        mock_random.return_value = 0.7  # Will fail (>= 0.5)
        
        response = api_client.post(
            '/api/purchases',
            sample_purchase_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data['status'] == 'error'
        assert response.data['message'] == 'Purchase failed'
        assert response.data['error'] == 'CONFLICT'
    
    def test_create_purchase_invalid_amount(self, api_client):
        """Test purchase creation with invalid amount."""
        invalid_data = {
            'transaction_id': 'test-invalid',
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 0  # Invalid: must be > 0
        }
        
        response = api_client.post(
            '/api/purchases',
            invalid_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_purchase_missing_transaction_id(self, api_client):
        """Test purchase creation without transaction_id."""
        data = {
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 100.50
        }
        
        response = api_client.post(
            '/api/purchases',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_purchase_missing_user_id(self, api_client):
        """Test purchase creation without user_id."""
        data = {
            'transaction_id': 'test-missing-user',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 100.50
        }
        
        response = api_client.post(
            '/api/purchases',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_purchase_negative_amount(self, api_client):
        """Test purchase creation with negative amount."""
        data = {
            'transaction_id': 'test-negative',
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': -50.00
        }
        
        response = api_client.post(
            '/api/purchases',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_idempotency(
        self,
        mock_sleep,
        mock_random,
        api_client
    ):
        """Test idempotency - same transaction_id returns same result."""
        mock_random.return_value = 0.3  # Will succeed
        
        data = {
            'transaction_id': 'idempotent-txn',
            'user_id': 'user-123',
            'product_id': 'prod-456',
            'payment_id': 'pay-789',
            'amount': 150.00
        }
        
        # First request
        response1 = api_client.post('/api/purchases', data, format='json')
        assert response1.status_code == status.HTTP_200_OK
        
        # Second request with same transaction_id (idempotent)
        response2 = api_client.post('/api/purchases', data, format='json')
        assert response2.status_code == status.HTTP_200_OK
        assert (response1.data['purchase_id'] ==
                response2.data['purchase_id'])
    
    @patch('app.services.purchase_service.time.sleep')
    def test_cancel_purchase_by_transaction_id(
        self,
        mock_sleep,
        api_client,
        created_purchase
    ):
        """Test cancelling purchase by transaction_id."""
        response = api_client.delete(
            f'/api/purchases/{created_purchase.transaction_id}/cancel'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert 'message' in response.data
        assert (response.data['transaction_id'] ==
                created_purchase.transaction_id)
        
        # Verify purchase was cancelled in DB
        created_purchase.refresh_from_db()
        assert created_purchase.is_cancelled()
    
    @patch('app.services.purchase_service.time.sleep')
    def test_cancel_purchase_not_found(self, mock_sleep, api_client):
        """Test cancelling non-existing purchase."""
        response = api_client.delete(
            '/api/purchases/non-existing-txn/cancel'
        )
        
        # Saga compensation always returns 200 OK
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_latency_simulation(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test that service simulates latency."""
        mock_random.return_value = 0.3  # Will succeed
        
        api_client.post(
            '/api/purchases',
            sample_purchase_data,
            format='json'
        )
        
        # Verify sleep was called (latency simulation)
        assert mock_sleep.called
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_purchase_stores_all_fields(
        self,
        mock_sleep,
        mock_random,
        api_client
    ):
        """Test that all fields are stored correctly."""
        mock_random.return_value = 0.3  # Will succeed
        
        data = {
            'transaction_id': 'test-all-fields',
            'user_id': 'user-999',
            'product_id': 'prod-888',
            'payment_id': 'pay-777',
            'amount': 99.99
        }
        
        response = api_client.post('/api/purchases', data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        purchase = Purchase.objects.get(
            transaction_id='test-all-fields'
        )
        assert purchase.user_id == 'user-999'
        assert purchase.product_id == 'prod-888'
        assert purchase.payment_id == 'pay-777'
        assert purchase.amount == Decimal('99.99')
        assert purchase.is_success()
