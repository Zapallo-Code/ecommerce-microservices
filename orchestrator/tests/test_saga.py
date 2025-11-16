"""
Tests for the orchestrator microservice.
Tests the SAGA pattern, distributed transactions, and compensations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport, Response

from app.main import app
from app.models import TransactionStatus
from app.storage.transaction_store import transaction_store


@pytest.fixture(autouse=True)
def clear_transactions():
    """Clear transaction store before each test."""
    transaction_store._transactions.clear()
    yield
    transaction_store._transactions.clear()


@pytest_asyncio.fixture
async def client():
    """Provide async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as ac:
        yield ac


class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test that health check endpoint returns OK."""
        response = await client.get("/health/")
        assert response.status_code == 200


class TestTransactionCreation:
    """Test cases for SAGA transaction creation."""

    @pytest.mark.asyncio
    async def test_successful_transaction(self, client):
        """Test successful end-to-end transaction."""
        with patch("app.services.http_client.httpx.AsyncClient") as mock_client:
            # Mock all service responses
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock product selection
            product_response = MagicMock(spec=Response)
            product_response.status_code = 200
            product_response.json.return_value = {
                "product_id": "1",
                "name": "Test Product",
                "price": "99.99",
            }

            # Mock inventory decrease
            inventory_response = MagicMock(spec=Response)
            inventory_response.status_code = 200
            inventory_response.json.return_value = {
                "message": "Inventory decreased successfully",
                "current_stock": 95,
            }

            # Mock payment processing
            payment_response = MagicMock(spec=Response)
            payment_response.status_code = 200
            payment_response.json.return_value = {
                "status": "success",
                "payment_id": "123",
            }

            # Mock purchase creation
            purchase_response = MagicMock(spec=Response)
            purchase_response.status_code = 201
            purchase_response.json.return_value = {
                "status": "success",
                "purchase_id": "456",
            }

            mock_instance.get.return_value = product_response
            mock_instance.post.side_effect = [
                inventory_response,
                payment_response,
                purchase_response,
            ]

            # Execute transaction
            response = await client.post(
                "/saga/transaction",
                json={"user_id": "user-001", "amount": 99.99},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "COMPLETED"
            assert "transaction_id" in data

    @pytest.mark.asyncio
    async def test_transaction_with_payment_failure(self, client):
        """Test transaction that fails at payment step and compensates."""
        with patch("app.services.http_client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock product selection
            product_response = MagicMock(spec=Response)
            product_response.status_code = 200
            product_response.json.return_value = {
                "product_id": "1",
                "name": "Test Product",
                "price": "99.99",
            }

            # Mock inventory decrease (succeeds)
            inventory_response = MagicMock(spec=Response)
            inventory_response.status_code = 200
            inventory_response.json.return_value = {
                "message": "Inventory decreased successfully",
                "current_stock": 95,
            }

            # Mock payment processing (fails)
            payment_response = MagicMock(spec=Response)
            payment_response.status_code = 409
            payment_response.json.return_value = {
                "status": "error",
                "message": "Payment failed",
            }

            mock_instance.get.return_value = product_response
            mock_instance.post.side_effect = [inventory_response, payment_response]

            # Execute transaction
            response = await client.post(
                "/saga/transaction",
                json={"user_id": "user-002", "amount": 99.99},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["status"] == "COMPENSATED"
            assert "error" in data["details"]

    @pytest.mark.asyncio
    async def test_transaction_missing_user_id(self, client):
        """Test transaction with missing user_id."""
        response = await client.post(
            "/saga/transaction",
            json={"amount": 99.99},  # Missing user_id
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_transaction_missing_amount(self, client):
        """Test transaction with missing amount."""
        response = await client.post(
            "/saga/transaction",
            json={"user_id": "user-001"},  # Missing amount
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_transaction_invalid_amount(self, client):
        """Test transaction with invalid amount."""
        response = await client.post(
            "/saga/transaction",
            json={"user_id": "user-001", "amount": -50.00},  # Negative amount
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_transaction_with_inventory_failure(self, client):
        """Test transaction that fails at inventory step."""
        with patch("app.services.http_client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock product selection
            product_response = MagicMock(spec=Response)
            product_response.status_code = 200
            product_response.json.return_value = {
                "product_id": "1",
                "name": "Test Product",
                "price": "99.99",
            }

            # Mock inventory decrease (fails - insufficient stock)
            inventory_response = MagicMock(spec=Response)
            inventory_response.status_code = 409
            inventory_response.json.return_value = {
                "status": "error",
                "message": "Insufficient stock",
            }

            mock_instance.get.return_value = product_response
            mock_instance.post.return_value = inventory_response

            # Execute transaction
            response = await client.post(
                "/saga/transaction",
                json={"user_id": "user-003", "amount": 99.99},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["status"] == "COMPENSATED"


class TestTransactionStatus:
    """Test cases for retrieving transaction status."""

    @pytest.mark.asyncio
    async def test_get_transaction_status_not_found(self, client):
        """Test getting status of non-existent transaction."""
        response = await client.get("/saga/status/nonexistent-txn-123")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    @pytest.mark.asyncio
    async def test_get_transaction_status_success(self, client):
        """Test getting status of existing transaction."""
        # First create a transaction
        from app.storage.transaction_store import TransactionDetail
        from datetime import datetime

        txn = TransactionDetail(
            transaction_id="test-txn-123",
            status=TransactionStatus.COMPLETED,
            user_id="user-001",
            product_id="1",
            payment_id="pay-123",
            inventory_updated=True,
            purchase_registered=True,
            amount=99.99,
            created_at=datetime.now(),
            completed_at=datetime.now(),
        )
        transaction_store.save(txn)

        # Now get its status
        response = await client.get("/saga/status/test-txn-123")

        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "test-txn-123"
        assert data["status"] == "COMPLETED"
        assert data["user_id"] == "user-001"


class TestTransactionListing:
    """Test cases for listing all transactions."""

    @pytest.mark.asyncio
    async def test_list_transactions_empty(self, client):
        """Test listing transactions when none exist."""
        response = await client.get("/saga/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["transactions"] == []

    @pytest.mark.asyncio
    async def test_list_transactions_with_data(self, client):
        """Test listing multiple transactions."""
        from app.storage.transaction_store import TransactionDetail
        from datetime import datetime

        # Create multiple transactions
        for i in range(3):
            txn = TransactionDetail(
                transaction_id=f"txn-{i}",
                status=TransactionStatus.COMPLETED
                if i % 2 == 0
                else TransactionStatus.COMPENSATED,
                user_id=f"user-{i}",
                product_id="1",
                payment_id=f"pay-{i}",
                inventory_updated=True,
                purchase_registered=i % 2 == 0,
                amount=100.00 * (i + 1),
                created_at=datetime.now(),
                completed_at=datetime.now(),
            )
            transaction_store.save(txn)

        response = await client.get("/saga/transactions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["transactions"]) == 3


class TestCompensationLogic:
    """Test cases for compensation/rollback logic."""

    @pytest.mark.asyncio
    async def test_compensation_after_purchase_failure(self, client):
        """Test that payment and inventory are compensated when purchase fails."""
        with patch("app.services.http_client.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock successful product, inventory, and payment
            product_response = MagicMock(spec=Response)
            product_response.status_code = 200
            product_response.json.return_value = {"product_id": "1", "price": "99.99"}

            inventory_response = MagicMock(spec=Response)
            inventory_response.status_code = 200
            inventory_response.json.return_value = {"message": "Success"}

            payment_response = MagicMock(spec=Response)
            payment_response.status_code = 200
            payment_response.json.return_value = {
                "status": "success",
                "payment_id": "123",
            }

            # Mock purchase failure
            purchase_response = MagicMock(spec=Response)
            purchase_response.status_code = 409
            purchase_response.json.return_value = {"status": "error"}

            # Mock compensation responses
            payment_refund = MagicMock(spec=Response)
            payment_refund.status_code = 200
            payment_refund.json.return_value = {"status": "compensated"}

            mock_instance.get.return_value = product_response
            mock_instance.post.side_effect = [
                inventory_response,
                payment_response,
                purchase_response,
                payment_refund,
            ]

            # Execute transaction
            response = await client.post(
                "/saga/transaction",
                json={"user_id": "user-004", "amount": 99.99},
            )

            assert response.status_code == 409
            data = response.json()
            assert data["status"] == "COMPENSATED"


class TestTransactionStore:
    """Test cases for the transaction store."""

    def test_store_and_retrieve_transaction(self):
        """Test storing and retrieving a transaction."""
        from app.storage.transaction_store import TransactionDetail
        from datetime import datetime

        txn = TransactionDetail(
            transaction_id="store-test-001",
            status=TransactionStatus.COMPLETED,
            user_id="user-store",
            product_id="1",
            payment_id="pay-store",
            inventory_updated=True,
            purchase_registered=True,
            amount=150.00,
            created_at=datetime.now(),
        )

        transaction_store.save(txn)
        retrieved = transaction_store.get("store-test-001")

        assert retrieved is not None
        assert retrieved.transaction_id == "store-test-001"
        assert retrieved.user_id == "user-store"
        assert retrieved.amount == 150.00

    def test_get_nonexistent_transaction(self):
        """Test retrieving a transaction that doesn't exist."""
        result = transaction_store.get("nonexistent-999")
        assert result is None

    def test_count_transactions(self):
        """Test counting stored transactions."""
        from app.storage.transaction_store import TransactionDetail
        from datetime import datetime

        initial_count = transaction_store.count()

        # Add transactions
        for i in range(5):
            txn = TransactionDetail(
                transaction_id=f"count-test-{i}",
                status=TransactionStatus.COMPLETED,
                user_id=f"user-{i}",
                amount=100.00,
                created_at=datetime.now(),
            )
            transaction_store.save(txn)

        assert transaction_store.count() == initial_count + 5

    def test_get_all_transactions(self):
        """Test retrieving all transactions."""
        from app.storage.transaction_store import TransactionDetail
        from datetime import datetime

        # Clear and add specific transactions
        transaction_store._transactions.clear()

        for i in range(3):
            txn = TransactionDetail(
                transaction_id=f"all-test-{i}",
                status=TransactionStatus.COMPLETED,
                user_id=f"user-{i}",
                amount=50.00 * (i + 1),
                created_at=datetime.now(),
            )
            transaction_store.save(txn)

        all_txns = transaction_store.get_all()
        assert len(all_txns) == 3
        assert all(txn.transaction_id.startswith("all-test-") for txn in all_txns)
