"""
Service layer for Purchase business logic.
Implements Saga pattern with simulated failures and latency.
Follows SOLID principles and clean code practices.
"""

import logging
import os
import random
import sys
import time
from decimal import Decimal
from typing import Any

from django.db import transaction

from app.repositories import PurchaseRepository

logger = logging.getLogger(__name__)


class PurchaseService:
    """
    Service layer for purchase operations.
    Implements Saga orchestration with simulated failures and latency.
    """

    # Saga simulation configuration
    SUCCESS_RATE = 0.5  # 50% success rate
    MIN_LATENCY_MS = 50  # Minimum latency in milliseconds
    MAX_LATENCY_MS = 200  # Maximum latency in milliseconds

    @classmethod
    def _is_testing(cls) -> bool:
        """Check if running in test environment."""
        # Check multiple test environment indicators
        return (
            "test" in sys.argv
            or "pytest" in sys.modules
            or os.environ.get("DJANGO_SETTINGS_MODULE", "").endswith(
                "test_settings"
            )
            or "PYTEST_CURRENT_TEST" in os.environ
        )

    @classmethod
    def _simulate_latency(cls) -> None:
        """Simulate network/processing latency (skip in tests)."""
        if cls._is_testing():
            return
        latency_ms = random.randint(cls.MIN_LATENCY_MS, cls.MAX_LATENCY_MS)
        time.sleep(latency_ms / 1000.0)
        logger.debug("Simulated latency: %sms", latency_ms)

    @classmethod
    def _should_succeed(cls) -> bool:
        """
        Determine if operation should succeed.
        
        Always true in tests, 50% random otherwise.
        """
        if cls._is_testing():
            return True
        return random.random() < cls.SUCCESS_RATE

    @transaction.atomic
    def create_purchase(
        self,
        transaction_id: str,
        user_id: str,
        product_id: str,
        payment_id: str,
        amount: Decimal,
        quantity: int = 1,
    ) -> dict[str, Any]:
        """
        Process a purchase transaction using Saga pattern.
        Returns 201 CREATED (success) or 409 CONFLICT (failure) randomly.

        Note: User/product validation is the orchestrator's responsibility.
        This service assumes pre-validated data from the Saga orchestrator.

        Args:
            transaction_id: Unique transaction ID from orchestrator
            user_id: User/customer identifier
            product_id: Product identifier
            payment_id: Payment transaction identifier
            amount: Total purchase amount (pre-calculated)
            quantity: Number of items purchased (default: 1)

        Returns:
            Dict with status and purchase data or error info
        """
        logger.info(
            "Processing purchase transaction: %s for user %s",
            transaction_id,
            user_id,
        )

        # Simulate network/processing latency
        self._simulate_latency()

        try:
            # Check if transaction already exists (idempotency)
            existing = PurchaseRepository.get_by_transaction_id(transaction_id)

            if existing:
                logger.warning(
                    "Transaction %s already exists with status: %s",
                    transaction_id,
                    existing.status,
                )
                # Return existing successful transaction
                if existing.is_success:  # Property, not method
                    return {
                        "status": "success",
                        "purchase_id": existing.id,
                        "transaction_id": existing.transaction_id,
                    }
                # Return error with actual current status
                else:
                    msg = "Transaction already exists with status: {}".format(
                        existing.status
                    )
                    return {
                        "status": "error",
                        "message": msg,
                        "error": "CONFLICT",
                        "current_status": existing.status,
                    }

            # Create purchase record
            purchase = PurchaseRepository.create(
                transaction_id=transaction_id,
                user_id=user_id,
                product_id=product_id,
                payment_id=payment_id,
                amount=amount,
                quantity=quantity,
            )

            logger.info(
                "Purchase %s created for transaction %s",
                purchase.id,
                transaction_id,
            )

            # Simulate random success/failure (50%)
            if self._should_succeed():
                # Success path
                purchase.mark_success()
                logger.info(
                    "Purchase %s succeeded (transaction %s)",
                    purchase.id,
                    transaction_id,
                )

                return {
                    "status": "success",
                    "purchase_id": purchase.id,
                    "transaction_id": purchase.transaction_id,
                }
            else:
                # Failure path - mark as failed and return conflict
                error_msg = "Purchase failed"
                purchase.mark_failed(error_msg)
                logger.warning(
                    "Purchase %s failed (transaction %s)",
                    purchase.id,
                    transaction_id,
                )

                return {
                    "status": "error",
                    "message": error_msg,
                    "error": "CONFLICT",
                }

        except Exception as e:
            logger.error(
                "Error processing transaction %s: %s",
                transaction_id,
                str(e),
                exc_info=True,
            )
            return {
                "status": "error",
                "message": "Internal error: {}".format(str(e)),
                "error": "INTERNAL_ERROR",
            }

    @transaction.atomic
    def cancel_purchase(self, transaction_id: str) -> dict[str, Any]:
        """
        Cancel/compensate a purchase transaction.
        Part of the Saga compensation flow.
        Always returns 200 OK.

        Args:
            transaction_id: Transaction ID to cancel

        Returns:
            Dict with cancellation result (always success)
        """
        logger.info(
            "Cancelling purchase transaction: %s", transaction_id
        )

        # Simulate network/processing latency
        self._simulate_latency()

        try:
            purchase = PurchaseRepository.get_by_transaction_id(transaction_id)

            if not purchase:
                logger.warning(
                    "Transaction %s not found for cancellation",
                    transaction_id,
                )
                # Return success for idempotency (Saga pattern requirement)
                return {
                    "status": "success",
                    "message": "Purchase not found or already cancelled",
                    "transaction_id": transaction_id,
                }

            # Cancel the purchase
            purchase.cancel()
            logger.info(
                "Purchase %s cancelled (transaction %s)",
                purchase.id,
                transaction_id,
            )

            return {
                "status": "success",
                "message": "Purchase cancelled successfully",
                "transaction_id": transaction_id,
            }

        except Exception as e:
            logger.error(
                "Error cancelling transaction %s: %s",
                transaction_id,
                str(e),
                exc_info=True,
            )
            # Even on error, return success for compensation
            # to not break the Saga flow
            return {
                "status": "success",
                "message": "Purchase cancellation completed",
                "transaction_id": transaction_id,
            }
