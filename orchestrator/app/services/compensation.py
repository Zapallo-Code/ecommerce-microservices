import logging

from app.models import TransactionDetail

from .http_client import ServiceClient

logger = logging.getLogger(__name__)


class CompensationService:
    def __init__(self) -> None:
        self.client = ServiceClient()

    async def compensate_payment(self, transaction: TransactionDetail) -> bool:
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

    async def compensate_inventory(self, transaction: TransactionDetail) -> bool:
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

    async def compensate_purchase(self, transaction: TransactionDetail) -> bool:
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

    async def execute_all_compensations(self, transaction: TransactionDetail) -> None:
        logger.warning(
            f"Starting compensations for transaction {transaction.transaction_id}"
        )

        # Define compensations in reverse order to the normal flow
        compensations: list[tuple[str, object]] = []

        if transaction.purchase_registered:
            compensations.append(("purchase", self.compensate_purchase))

        if transaction.inventory_updated:
            compensations.append(("inventory", self.compensate_inventory))

        if transaction.payment_id:
            compensations.append(("payment", self.compensate_payment))

        # Execute compensations SEQUENTIALLY in reverse order
        # This ensures consistency and proper rollback
        for name, compensation_fn in compensations:
            try:
                logger.info(f"Executing compensation for {name}...")
                result = await compensation_fn(transaction)

                if result:
                    logger.info(f"Compensation for {name} succeeded")
                else:
                    logger.error(f"Compensation for {name} failed")
            except Exception as e:
                logger.error(
                    f"Compensation for {name} failed with exception: {str(e)}",
                    exc_info=True,
                )
