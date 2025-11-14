import logging

from app.models import TransactionDetail

from .http_client import ServiceClient

logger = logging.getLogger(__name__)


class CompensationService:
    def __init__(self) -> None:
        self.client = ServiceClient()

    async def compensate_payment(self, transaction: TransactionDetail) -> bool:
        """
        Compensate payment transaction.
        Always returns success to ensure Saga completion.
        """
        if not transaction.payment_id:
            return True

        try:
            logger.info(f"Compensating payment {transaction.payment_id}")
            await self.client.call_service(
                "payments",
                f"/payments/{transaction.payment_id}/refund/",
                method="POST",
                data={"reason": "Transaction failed"},
            )
            return True
        except Exception as e:
            logger.error(f"Error compensating payment: {str(e)}")
            return False

    async def compensate_purchase(self, transaction: TransactionDetail) -> bool:
        """
        Compensate purchase transaction.
        Always returns success to ensure Saga completion.
        """
        if not transaction.purchase_registered:
            return True

        try:
            logger.info(
                f"Compensating purchase record for transaction {transaction.transaction_id}"
            )
            await self.client.call_service(
                "purchases",
                f"/purchases/{transaction.transaction_id}/cancel/",
                method="DELETE",
            )
            return True
        except Exception as e:
            logger.error(f"Error compensating purchase: {str(e)}")
            return False

    async def execute_all_compensations(self, transaction: TransactionDetail) -> None:
        """
        Execute compensations in reverse order.

        Per requirements:
        - catalog: NO compensation needed
        - payments: HAS compensation (refund)
        - inventory: NO compensation needed (per requirements)
        - purchases: HAS compensation (cancel)

        Order: purchase -> payment (reverse of execution)
        """
        logger.warning(
            f"Starting compensations for transaction {transaction.transaction_id}"
        )

        # Define compensations in reverse order to the normal flow
        compensations: list[tuple[str, object]] = []

        if transaction.purchase_registered:
            compensations.append(("purchase", self.compensate_purchase))

        # Inventory does NOT need compensation per requirements
        # It returns 409 Conflict on failure, triggering compensations
        # of previous steps only

        if transaction.payment_id:
            compensations.append(("payment", self.compensate_payment))

        # Catalog does NOT need compensation per requirements

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
