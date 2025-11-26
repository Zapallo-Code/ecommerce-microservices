import logging
import uuid
from datetime import datetime

from app.models import TransactionDetail, TransactionRequest, TransactionStatus
from app.storage.transaction_store import transaction_store

from .compensation import CompensationService
from .http_client import ServiceClient

logger = logging.getLogger(__name__)


class SagaService:
    def __init__(self) -> None:
        self.client = ServiceClient()
        self.compensation_service = CompensationService()

    def _create_transaction(
        self, purchase_request: TransactionRequest, transaction_id: str
    ) -> TransactionDetail:
        return TransactionDetail(
            transaction_id=transaction_id,
            status=TransactionStatus.PENDING,
            user_id=purchase_request.user_id,
            amount=purchase_request.amount,
            created_at=datetime.now(),
        )

    async def _execute_step(
        self,
        transaction: TransactionDetail,
        step_name: str,
        step_fn,
    ) -> None:
        """Execute a saga step with logging and state persistence."""
        logger.info(f"[{transaction.transaction_id}] {step_name}")
        await step_fn(transaction)
        transaction_store.save(transaction)
        logger.info(f"[{transaction.transaction_id}] {step_name} completed")

    async def _step_get_product(self, transaction: TransactionDetail) -> None:
        """Get product from catalog."""
        product_response = await self.client.call_service(
            "catalog", "/catalog/", method="GET"
        )
        transaction.product_id = (
            str(product_response["product_id"])
            if product_response.get("product_id")
            else None
        )

    async def _step_process_payment(self, transaction: TransactionDetail) -> None:
        """Process payment for the transaction."""
        payment_data: dict[str, object] = {
            "user_id": transaction.user_id,
            "amount": transaction.amount,
            "product_id": transaction.product_id,
        }
        payment_response = await self.client.call_service(
            "payments", "/payments/", method="POST", data=payment_data
        )
        transaction.payment_id = (
            str(payment_response["payment_id"])
            if payment_response.get("payment_id")
            else None
        )

    async def _step_update_inventory(self, transaction: TransactionDetail) -> None:
        """Update inventory for the product."""
        inventory_data: dict[str, object] = {
            "product_id": transaction.product_id,
            "quantity": 1,
        }
        await self.client.call_service(
            "inventory",
            "/inventory/decrease/",
            method="POST",
            data=inventory_data,
        )
        transaction.inventory_updated = True

    async def _step_register_purchase(self, transaction: TransactionDetail) -> None:
        """Register the purchase."""
        purchase_data: dict[str, object] = {
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "product_id": transaction.product_id,
            "payment_id": transaction.payment_id,
            "amount": transaction.amount,
        }
        await self.client.call_service(
            "purchases",
            "/purchases/",
            method="POST",
            data=purchase_data,
        )
        transaction.purchase_registered = True

    async def execute_saga(
        self, purchase_request: TransactionRequest
    ) -> TransactionDetail:
        """Execute the complete saga orchestration."""
        transaction_id = str(uuid.uuid4())
        transaction = self._create_transaction(purchase_request, transaction_id)
        transaction_store.save(transaction)

        try:
            # Execute saga steps
            await self._execute_step(
                transaction, "Step 1: Get product", self._step_get_product
            )
            await self._execute_step(
                transaction, "Step 2: Process payment", self._step_process_payment
            )
            await self._execute_step(
                transaction, "Step 3: Update inventory", self._step_update_inventory
            )
            await self._execute_step(
                transaction, "Step 4: Register purchase", self._step_register_purchase
            )

            # Mark as completed
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            transaction_store.save(transaction)

            logger.info(f"[{transaction_id}] Saga completed successfully")
            return transaction

        except Exception as e:
            logger.error(f"[{transaction_id}] Saga failed: {str(e)}")

            transaction.error_message = str(e)
            transaction_store.save(transaction)

            await self.compensation_service.execute_all_compensations(transaction)

            transaction.status = TransactionStatus.COMPENSATED
            transaction.completed_at = datetime.now()
            transaction_store.save(transaction)

            logger.warning(f"[{transaction_id}] Saga compensated")
            raise
