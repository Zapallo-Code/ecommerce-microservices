"""
Business logic for inventory operations.
Handles decrease and compensate operations with idempotency and atomicity.
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
        Decrementa el inventario de un producto.

        Args:
            product_id: ID del producto (string)
            quantity: Cantidad a decrementar
            transaction_id: ID de transacción saga (opcional)

        Returns:
            dict con resultado de la operación

        Raises:
            ValueError: Si no hay stock suficiente o fallo aleatorio
        """
        # Simular latencia
        latency = random.uniform(0.1, 0.5)
        time.sleep(latency)

        # Simular error aleatorio al 50% (igual que pagos y compras)
        # Esto garantiza consistencia en el patrón Saga
        if random.random() < 0.5:
            logger.warning(f"Simulated random failure (50%) - product_id: {product_id}")
            raise ValueError(
                f"Insufficient stock for product {product_id} (random failure)"
            )

        # Generar operation_id interno
        operation_id = str(uuid.uuid4())

        # Buscar o crear inventario
        inventory, created = Inventory.objects.get_or_create(
            product_id=product_id, defaults={"stock": 100}
        )

        if created:
            logger.info(
                f"Created new inventory entry - product_id: {product_id}, initial stock: 100"
            )

        # Verificar stock real (segunda validación)
        if inventory.stock < quantity:
            logger.warning(
                f"Insufficient stock - product_id: {product_id}, available: {inventory.stock}, requested: {quantity}"
            )
            raise ValueError(
                f"Insufficient stock for product {product_id}. Available: {inventory.stock}, Requested: {quantity}"
            )

        # Decrementar stock
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

    @staticmethod
    def restore_inventory(
        product_id: str, quantity: int = 1, transaction_id: str = None
    ):
        """
        Restaura el inventario de un producto (compensación).

        Args:
            product_id: ID del producto (string)
            quantity: Cantidad a restaurar
            transaction_id: ID de transacción saga (opcional)

        Returns:
            dict con resultado de la operación

        Raises:
            ValueError: Si el producto no existe
        """
        # Simular latencia
        latency = random.uniform(0.1, 0.3)
        time.sleep(latency)

        try:
            inventory = Inventory.objects.get(product_id=product_id)
        except Inventory.DoesNotExist:
            logger.error(f"Product not found for restore - product_id: {product_id}")
            raise ValueError(f"Product {product_id} not found in inventory")

        # Restaurar stock
        old_stock = inventory.stock
        inventory.stock += quantity
        inventory.save()

        logger.info(
            f"Stock restored - product_id: {product_id}, old: {old_stock}, new: {inventory.stock}, transaction_id: {transaction_id}"
        )

        return {
            "message": "Inventory restored successfully",
            "product_id": product_id,
            "quantity": quantity,
            "previous_stock": old_stock,
            "current_stock": inventory.stock,
            "transaction_id": transaction_id,
            "latency_seconds": round(latency, 3),
        }

    @staticmethod
    def get_inventory(product_id):
        """Get inventory for a product."""
        try:
            inventory = Inventory.objects.get(product_id=product_id)
            return {
                "product_id": inventory.product_id,
                "stock": inventory.stock,
                "reserved": inventory.reserved,
                "available": inventory.available,
            }
        except Inventory.DoesNotExist:
            return None
