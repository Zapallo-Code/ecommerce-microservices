import asyncio
import logging

from app.models import TransactionState

from .http_client import ServiceClient

logger = logging.getLogger(__name__)


class CompensationService:
    def __init__(self) -> None:
        self.client = ServiceClient()

    async def compensate_payment(self, transaction: TransactionState) -> bool:
        if not transaction.payment_id:
            return True

        try:
            logger.info(f"Offsetting payment {transaction.payment_id}")
            await self.client.call_service(
                "payments",
                f"/payments/{transaction.payment_id}/refund",
                method="POST",
                data={"reason": "Transaction failed"},
            )
            return True
        except Exception as e:
            logger.error(f"Error offsetting payment: {str(e)}")
            return False

    async def compensate_inventory(self, transaction: TransactionState) -> bool:
        if not transaction.inventory_updated or not transaction.product_id:
            return True

        try:
            logger.info(f"Compensando inventario del producto {transaction.product_id}")
            await self.client.call_service(
                "inventory",
                f"/inventory/{transaction.product_id}/restore",
                method="POST",
                data={"quantity": 1},
            )
            return True
        except Exception as e:
            logger.error(f"Error offsetting inventory: {str(e)}")
            return False

    async def compensate_purchase(self, transaction: TransactionState) -> bool:
        if not transaction.purchase_registered:
            return True

        try:
            logger.info(
                f"Offsetting purchase record for transaction {transaction.transaction_id}"
            )
            await self.client.call_service(
                "purchases",
                f"/purchases/{transaction.transaction_id}/cancel",
                method="DELETE",
            )
            return True
        except Exception as e:
            logger.error(f"Error offsetting purchase: {str(e)}")
            return False

    async def execute_all_compensations(self, transaction: TransactionState) -> None:
        logger.warning(
            f"Starting compensations for transaction {transaction.transaction_id}"
        )

        # Define compensations in reverse order to the normal flow
        compensations: list[tuple[str, object]] = []
        compensation_tasks = []

        if transaction.purchase_registered:
            task = self.compensate_purchase(transaction)
            compensations.append(("purchase", task))
            compensation_tasks.append(task)

        if transaction.inventory_updated:
            task = self.compensate_inventory(transaction)
            compensations.append(("inventory", task))
            compensation_tasks.append(task)

        if transaction.payment_id:
            task = self.compensate_payment(transaction)
            compensations.append(("payment", task))
            compensation_tasks.append(task)

        # Execute compensations concurrently
        results = await asyncio.gather(*compensation_tasks, return_exceptions=True)

        # Log results
        for (name, _), result in zip(compensations, results, strict=True):
            if isinstance(result, Exception) or not result:
                logger.error(f"Compensation for {name} failed")
            else:
                logger.info(f"Compensation for {name} succeeded")
