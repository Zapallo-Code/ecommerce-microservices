import logging
import uuid
from datetime import datetime

from . import (
    CompensationService,
    ServiceClient,
    TransactionRequest,
    TransactionState,
    TransactionStatus,
    transaction_store,
)

logger = logging.getLogger(__name__)


class SagaService:
    def __init__(self) -> None:
        self.client = ServiceClient()
        self.compensation_service = CompensationService()

    def _create_transaction(
        self, purchase_request: TransactionRequest, transaction_id: str
    ) -> TransactionState:
        return TransactionState(
            transaction_id=transaction_id,
            status=TransactionStatus.PENDING,
            user_id=purchase_request.user_id,
            amount=purchase_request.amount,
            created_at=datetime.now(),
        )

    async def _step_get_product(self, transaction: TransactionState) -> None:
        logger.info(
            f"[{transaction.transaction_id}] Step 1: Getting product from the catalog"
        )
        product_response = await self.client.call_service(
            "catalog", "/products/random", method="GET"
        )
        transaction.product_id = (
            str(product_response.get("product_id"))
            if product_response.get("product_id")
            else None
        )
        logger.info(
            f"[{transaction.transaction_id}] Product obtained: {transaction.product_id}"
        )

    async def _step_process_payment(self, transaction: TransactionState) -> None:
        logger.info(f"[{transaction.transaction_id}] Step 2: Processing payment")
        payment_data = {
            "user_id": transaction.user_id,
            "amount": transaction.amount,
            "product_id": transaction.product_id,
        }
        payment_response = await self.client.call_service(
            "payments", "/payments", method="POST", data=payment_data
        )
        transaction.payment_id = (
            str(payment_response.get("payment_id"))
            if payment_response.get("payment_id")
            else None
        )
        logger.info(
            f"[{transaction.transaction_id}] Payment processed: {transaction.payment_id}"
        )

    async def _step_update_inventory(self, transaction: TransactionState) -> None:
        logger.info(f"[{transaction.transaction_id}] Step 3: Updating inventory")
        inventory_data = {"product_id": transaction.product_id, "quantity": 1}
        await self.client.call_service(
            "inventory",
            "/inventory/decrease",
            method="POST",
            data=inventory_data,
        )
        transaction.inventory_updated = True
        logger.info(f"[{transaction.transaction_id}] Inventory updated")

    async def _step_register_purchase(self, transaction: TransactionState) -> None:
        logger.info(f"[{transaction.transaction_id}] Step 4: Registering purchase")
        purchase_data = {
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "product_id": transaction.product_id,
            "payment_id": transaction.payment_id,
            "amount": transaction.amount,
        }
        await self.client.call_service(
            "purchases",
            "/purchases",
            method="POST",
            data=purchase_data,
        )
        transaction.purchase_registered = True
        logger.info(f"[{transaction.transaction_id}] Purchase registered successfully")

    async def execute_saga(
        self, purchase_request: TransactionRequest
    ) -> TransactionState:
        transaction_id = str(uuid.uuid4())
        transaction = self._create_transaction(purchase_request, transaction_id)

        transaction_store.save(transaction)

        try:
            await self._step_get_product(transaction)
            transaction_store.save(transaction)

            await self._step_process_payment(transaction)
            transaction_store.save(transaction)

            await self._step_update_inventory(transaction)
            transaction_store.save(transaction)

            await self._step_register_purchase(transaction)
            transaction_store.save(transaction)

            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            transaction_store.save(transaction)

            logger.info(f"[{transaction_id}] Saga completed successfully")
            return transaction

        except Exception as e:
            logger.error(f"[{transaction_id}] Error in saga: {str(e)}")

            transaction.error_message = str(e)
            transaction_store.save(transaction)

            await self.compensation_service.execute_all_compensations(transaction)

            transaction.status = TransactionStatus.COMPENSATED
            transaction.completed_at = datetime.now()
            transaction_store.save(transaction)

            logger.warning(f"[{transaction_id}] Saga compensated due to error")
            raise
