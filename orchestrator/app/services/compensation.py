import logging

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
        Order: purchase -> payment (reverse of execution)
        Note: catalog and inventory do not need compensation.
        """
        logger.warning(f"Starting compensations for {transaction.transaction_id}")

        # Compensations in reverse order
        compensations = [
            ("purchase", self.compensate_purchase),
            ("payment", self.compensate_payment),
        ]

        for name, compensation_fn in compensations:
            result = await compensation_fn(transaction)
            log_fn = logger.info if result else logger.error
            status = "succeeded" if result else "failed"
            log_fn(f"Compensation for {name} {status}")
