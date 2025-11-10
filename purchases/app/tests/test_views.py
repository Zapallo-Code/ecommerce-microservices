"""
Integration tests for Purchase API Views.
"""
import pytest
from unittest.mock import patch
from decimal import Decimal
from rest_framework import status
from app.models import Purchase


@pytest.mark.django_db
@pytest.mark.integration
class TestPurchaseViewSet:
    """Integration tests for PurchaseViewSet."""
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_success(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test successful purchase creation."""
        mock_random.return_value = 0.3  # Will succeed
        
        response = api_client.post(
            '/api/purchases/purchase/',
            sample_purchase_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['status'] == 'confirmed'
        assert 'purchase' in response.data
        assert 'saga_id' in response.data
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_create_purchase_failure(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test failed purchase creation (Saga failure)."""
        mock_random.return_value = 0.7  # Will fail
        
        response = api_client.post(
            '/api/purchases/purchase/',
            sample_purchase_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data['success'] is False
        assert response.data['status'] == 'failed'
        assert 'error' in response.data
    
    def test_create_purchase_invalid_data(self, api_client):
        """Test purchase creation with invalid data."""
        invalid_data = {
            'customer_id': 0,  # Invalid
            'items': []
        }
        
        response = api_client.post(
            '/api/purchases/purchase/',
            invalid_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'errors' in response.data
    
    def test_create_purchase_missing_customer_id(self, api_client):
        """Test purchase creation without customer_id."""
        data = {
            'items': [
                {
                    'product_id': 1,
                    'quantity': 1,
                    'unit_price': '10.00'
                }
            ]
        }
        
        response = api_client.post(
            '/api/purchases/purchase/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_purchase_missing_items(self, api_client):
        """Test purchase creation without items."""
        data = {
            'customer_id': 1
        }
        
        response = api_client.post(
            '/api/purchases/purchase/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_purchase_empty_items(self, api_client):
        """Test purchase creation with empty items list."""
        data = {
            'customer_id': 1,
            'items': []
        }
        
        response = api_client.post(
            '/api/purchases/purchase/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_by_id(
        self,
        mock_sleep,
        api_client,
        created_purchase
    ):
        """Test compensating purchase by ID."""
        response = api_client.post(
            '/api/purchases/compensate/',
            {'purchase_id': created_purchase.id},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['status'] == 'cancelled'
        assert response.data['purchase_id'] == created_purchase.id
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_by_saga_id(
        self,
        mock_sleep,
        api_client,
        created_purchase
    ):
        """Test compensating purchase by saga_id."""
        response = api_client.post(
            '/api/purchases/compensate/',
            {'saga_id': 'test-saga-123'},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['saga_id'] == 'test-saga-123'
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_purchase_not_found(self, mock_sleep, api_client):
        """Test compensating non-existing purchase."""
        response = api_client.post(
            '/api/purchases/compensate/',
            {'purchase_id': 99999},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is False
        assert 'error' in response.data
    
    def test_compensate_purchase_missing_identifier(self, api_client):
        """Test compensation without purchase_id or saga_id."""
        response = api_client.post(
            '/api/purchases/compensate/',
            {},
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_list_purchases(self, api_client, created_purchase):
        """Test listing all purchases."""
        response = api_client.get('/api/purchases/list/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'purchases' in response.data
        assert response.data['count'] >= 1
    
    def test_list_purchases_by_customer(
        self,
        api_client,
        sample_items
    ):
        """Test listing purchases filtered by customer."""
        from app.repositories import PurchaseRepository
        
        # Create purchases for specific customer
        PurchaseRepository.create_purchase(
            customer_id=99,
            items=sample_items
        )
        
        response = api_client.get(
            '/api/purchases/list/',
            {'customer_id': 99}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
        purchases = response.data['purchases']
        assert all(p['customer_id'] == 99 for p in purchases)
    
    def test_retrieve_purchase(self, api_client, created_purchase):
        """Test retrieving specific purchase."""
        response = api_client.get(
            f'/api/purchases/{created_purchase.id}/retrieve_purchase/'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'purchase' in response.data
        assert response.data['purchase']['id'] == created_purchase.id
    
    def test_retrieve_purchase_not_found(self, api_client):
        """Test retrieving non-existing purchase."""
        response = api_client.get('/api/purchases/99999/retrieve_purchase/')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['success'] is False
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_purchase_creates_correct_details(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test that purchase details are created correctly."""
        mock_random.return_value = 0.3  # Will succeed
        
        response = api_client.post(
            '/api/purchases/purchase/',
            sample_purchase_data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        purchase_data = response.data['purchase']
        assert len(purchase_data['details']) == 2
        
        # Check first detail
        detail1 = purchase_data['details'][0]
        assert detail1['product_id'] == 1
        assert detail1['quantity'] == 2
        assert Decimal(detail1['unit_price']) == Decimal('29.99')
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_purchase_calculates_total(
        self,
        mock_sleep,
        mock_random,
        api_client,
        sample_purchase_data
    ):
        """Test that total is calculated correctly."""
        mock_random.return_value = 0.3  # Will succeed
        
        response = api_client.post(
            '/api/purchases/purchase/',
            sample_purchase_data,
            format='json'
        )
        
        purchase_data = response.data['purchase']
        expected_total = Decimal('29.99') * 2 + Decimal('49.99')
        assert Decimal(purchase_data['total_amount']) == expected_total
    
    @patch('app.services.purchase_service.time.sleep')
    def test_compensate_verified_in_database(
        self,
        mock_sleep,
        api_client,
        created_purchase
    ):
        """Test that compensation is persisted in database."""
        response = api_client.post(
            '/api/purchases/compensate/',
            {'purchase_id': created_purchase.id},
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify in database
        purchase = Purchase.objects.get(id=created_purchase.id)
        assert purchase.status == Purchase.STATUS_CANCELLED
    
    def test_invalid_json_format(self, api_client):
        """Test handling of invalid JSON."""
        response = api_client.post(
            '/api/purchases/purchase/',
            'invalid-json',
            content_type='application/json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @patch('app.services.purchase_service.random.random')
    @patch('app.services.purchase_service.time.sleep')
    def test_purchase_with_multiple_items(
        self,
        mock_sleep,
        mock_random,
        api_client
    ):
        """Test purchase with multiple different items."""
        mock_random.return_value = 0.3  # Will succeed
        
        data = {
            'customer_id': 1,
            'items': [
                {
                    'product_id': 1,
                    'quantity': 1,
                    'unit_price': '10.00'
                },
                {
                    'product_id': 2,
                    'quantity': 2,
                    'unit_price': '20.00'
                },
                {
                    'product_id': 3,
                    'quantity': 3,
                    'unit_price': '30.00'
                }
            ]
        }
        
        response = api_client.post(
            '/api/purchases/purchase/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        purchase_data = response.data['purchase']
        assert len(purchase_data['details']) == 3
        assert Decimal(purchase_data['total_amount']) == Decimal('140.00')
