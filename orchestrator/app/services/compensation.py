import logging
import uuid

from app.models import TransactionDetail

from .http_client import ServiceClient

logger = logging.getLogger(__name__)


class CompensationService:
    def __init__(self) -> None:
        self.client = ServiceClient()

    async def _execute_compensation(
        self,
        name: str,
        should_compensate: bool,
        compensation_fn,
    ) -> bool:
        """Execute a compensation action with consistent error handling."""
        if not should_compensate:
            return True

        try:
            logger.info(f"Compensating {name}")
            await compensation_fn()
            return True
        except Exception as e:
            logger.error(f"Error compensating {name}: {str(e)}")
            return False

    async def compensate_payment(self, transaction: TransactionDetail) -> bool:
        """Compensate payment transaction."""
        return await self._execute_compensation(
            name=f"payment {transaction.payment_id}",
            should_compensate=bool(transaction.payment_id),
            compensation_fn=lambda: self.client.call_service(
                "payments",
                f"/payments/{transaction.payment_id}/refund/",
                method="POST",
                data={"reason": "Transaction failed"},
            ),
        )

    async def compensate_inventory(self, transaction: TransactionDetail) -> bool:
        """Compensate inventory transaction - restore the stock."""
        return await self._execute_compensation(
            name=f"inventory for product {transaction.product_id}",
            should_compensate=transaction.inventory_updated and bool(transaction.product_id),
            compensation_fn=lambda: self.client.call_service(
                "inventory",
                "/inventory/compensate/",
                method="POST",
                data={
                    "operation_id": str(uuid.uuid4()),  # New operation for compensation
                    "product_id": int(transaction.product_id),
                    "quantity": 1,
                    "metadata": {
                        "reason": "Transaction compensation",
                        "original_transaction": transaction.transaction_id,
                        "original_operation_id": transaction.inventory_operation_id,
                    }
                },
            ),
        )

    async def compensate_purchase(self, transaction: TransactionDetail) -> bool:
        """Compensate purchase transaction."""
        return await self._execute_compensation(
            name=f"purchase {transaction.transaction_id}",
            should_compensate=transaction.purchase_registered,
            compensation_fn=lambda: self.client.call_service(
                "purchases",
                f"/purchases/{transaction.transaction_id}/cancel/",
                method="DELETE",
            ),
        )

    async def execute_all_compensations(self, transaction: TransactionDetail) -> None:
        """
        Execute compensations in reverse order.
        Order: purchase -> inventory -> payment (reverse of execution)
        """
        logger.warning(f"Starting compensations for {transaction.transaction_id}")

        # Compensations in reverse order of execution
        compensations = [
            ("purchase", self.compensate_purchase),
            ("inventory", self.compensate_inventory),
            ("payment", self.compensate_payment),
        ]

        for name, compensation_fn in compensations:
            result = await compensation_fn(transaction)
            log_fn = logger.info if result else logger.error
            status = "succeeded" if result else "failed"
            log_fn(f"Compensation for {name} {status}")
