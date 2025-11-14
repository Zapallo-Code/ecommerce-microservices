"""
Business logic for inventory operations.
Handles decrease operation with random failures (50% like payments and purchases).
Per requirements, inventory does NOT need compensation/restore.
"""

import random
import time
import logging
import uuid
from .models import Inventory

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for managing inventory operations in a saga pattern."""

    @staticmethod
    def decrease_inventory(
        product_id: str, quantity: int = 1, transaction_id: str = None
    ):
        """
        Decreases product inventory.
        Returns 200 OK or 409 Conflict randomly (50% each).

        Args:
            product_id: Product ID (string)
            quantity: Quantity to decrease
            transaction_id: Saga transaction ID (optional)

        Returns:
            dict with operation result

        Raises:
            ValueError: If random failure occurs (50% chance)
        """
        # Simulate latency (0.1 to 0.5 seconds)
        latency = random.uniform(0.1, 0.5)
        time.sleep(latency)

        # Simulate random error at 50% (consistent with payments and purchases)
        # This ensures Saga pattern triggers compensations properly
        if random.random() < 0.5:
            logger.warning(f"Random failure (50%) - product_id: {product_id}")
            raise ValueError(
                f"Insufficient stock for product {product_id} (random failure)"
            )

        # Generate internal operation_id
        operation_id = str(uuid.uuid4())

        # Find or create inventory
        inventory, created = Inventory.objects.get_or_create(
            product_id=product_id, defaults={"stock": 100}
        )

        if created:
            logger.info(
                f"Created new inventory entry - product_id: {product_id}, initial stock: 100"
            )

        # Verify actual stock (second validation)
        if inventory.stock < quantity:
            logger.warning(
                f"Insufficient stock - product_id: {product_id}, available: {inventory.stock}, requested: {quantity}"
            )
            raise ValueError(
                f"Insufficient stock for product {product_id}. Available: {inventory.stock}, Requested: {quantity}"
            )

        # Decrease stock
        old_stock = inventory.stock
        inventory.stock -= quantity
        inventory.save()

        logger.info(
            f"Stock decreased - product_id: {product_id}, old: {old_stock}, new: {inventory.stock}, operation_id: {operation_id}"
        )

        return {
            "message": "Inventory decreased successfully",
            "product_id": product_id,
            "quantity": quantity,
            "previous_stock": old_stock,
            "current_stock": inventory.stock,
            "operation_id": operation_id,
            "transaction_id": transaction_id,
            "latency_seconds": round(latency, 3),
        }
