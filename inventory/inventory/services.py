"""
Business logic for inventory operations.
Handles decrease and compensate operations with idempotency and atomicity.
"""
import random
import time
import logging
from django.db import transaction
from django.conf import settings
from .models import Inventory, InventoryOperation

logger = logging.getLogger(__name__)


class InsufficientStockError(Exception):
    """Raised when there's not enough stock for an operation."""
    pass


class InventoryService:
    """Service for managing inventory operations in a saga pattern."""

    @staticmethod
    def _simulate_latency():
        """Simulate network/processing latency if enabled."""
        if settings.SIMULATE_LATENCY:
            latency = random.uniform(
                settings.MIN_LATENCY_MS / 1000,
                settings.MAX_LATENCY_MS / 1000
            )
            time.sleep(latency)

    @staticmethod
    def _should_simulate_no_stock():
        """Randomly decide if we should simulate no stock."""
        return random.random() < settings.NO_STOCK_RATE

    @staticmethod
    @transaction.atomic
    def decrease_stock(operation_id, product_id, quantity, metadata=None):
        """
        Decrease stock for a product with idempotency support.
        
        Args:
            operation_id: UUID for idempotency
            product_id: ID of the product
            quantity: Amount to decrease
            metadata: Optional metadata dict
            
        Returns:
            dict with status and remaining stock
            
        Raises:
            InsufficientStockError: When stock is insufficient
        """
        logger.info(f"Decrease stock request: operation_id={operation_id}, product_id={product_id}, quantity={quantity}")
        
        # Simulate latency
        InventoryService._simulate_latency()
        
        # Check if operation already exists (idempotency)
        existing_op = InventoryOperation.objects.filter(
            operation_id=operation_id
        ).first()
        
        if existing_op:
            if existing_op.status == 'applied':
                logger.info(f"Operation {operation_id} already applied (idempotent)")
                inventory = Inventory.objects.get(product_id=product_id)
                return {
                    'status': 'updated',
                    'product_id': product_id,
                    'remaining': inventory.stock,
                    'idempotent': True
                }
            elif existing_op.status == 'failed':
                logger.info(f"Operation {operation_id} previously failed")
                raise InsufficientStockError(f"Operation {operation_id} previously failed")
        
        # Simulate random no stock scenario
        if InventoryService._should_simulate_no_stock():
            logger.warning(f"Simulating no stock for product_id={product_id}")
            InventoryOperation.objects.create(
                operation_id=operation_id,
                product_id=product_id,
                quantity=-quantity,
                status='failed',
                metadata=metadata or {}
            )
            raise InsufficientStockError(f"Simulated: No stock for product {product_id}")
        
        # Get inventory with lock
        try:
            inventory = Inventory.objects.select_for_update().get(product_id=product_id)
        except Inventory.DoesNotExist:
            logger.error(f"Product {product_id} not found in inventory")
            InventoryOperation.objects.create(
                operation_id=operation_id,
                product_id=product_id,
                quantity=-quantity,
                status='failed',
                metadata=metadata or {}
            )
            raise InsufficientStockError(f"Product {product_id} not found")
        
        # Check if there's enough stock
        if inventory.stock < quantity:
            logger.warning(f"Insufficient stock: product_id={product_id}, available={inventory.stock}, requested={quantity}")
            InventoryOperation.objects.create(
                operation_id=operation_id,
                product_id=product_id,
                quantity=-quantity,
                status='failed',
                metadata=metadata or {}
            )
            raise InsufficientStockError(f"Insufficient stock for product {product_id}")
        
        # Decrease stock
        inventory.stock -= quantity
        inventory.save()
        
        # Record operation
        InventoryOperation.objects.create(
            operation_id=operation_id,
            product_id=product_id,
            quantity=-quantity,
            status='applied',
            metadata=metadata or {}
        )
        
        logger.info(f"Stock decreased successfully: product_id={product_id}, new_stock={inventory.stock}")
        
        return {
            'status': 'updated',
            'product_id': product_id,
            'remaining': inventory.stock
        }

    @staticmethod
    @transaction.atomic
    def compensate(operation_id, product_id, quantity, metadata=None):
        """
        Compensate (restore) stock with idempotency support.
        Always returns success (200).
        
        Args:
            operation_id: UUID for the compensation operation
            product_id: ID of the product
            quantity: Amount to restore
            metadata: Optional metadata dict
            
        Returns:
            dict with status and new stock
        """
        logger.info(f"Compensate request: operation_id={operation_id}, product_id={product_id}, quantity={quantity}")
        
        # Simulate latency
        InventoryService._simulate_latency()
        
        # Check if compensation already applied (idempotency)
        existing_comp = InventoryOperation.objects.filter(
            operation_id=operation_id,
            status='reverted'
        ).first()
        
        if existing_comp:
            logger.info(f"Compensation {operation_id} already applied (idempotent)")
            inventory = Inventory.objects.get(product_id=product_id)
            return {
                'status': 'compensated',
                'product_id': product_id,
                'new_stock': inventory.stock,
                'idempotent': True
            }
        
        # Get or create inventory
        inventory, created = Inventory.objects.select_for_update().get_or_create(
            product_id=product_id,
            defaults={'stock': 0}
        )
        
        # Restore stock
        inventory.stock += quantity
        inventory.save()
        
        # Record compensation
        InventoryOperation.objects.create(
            operation_id=operation_id,
            product_id=product_id,
            quantity=quantity,
            status='reverted',
            metadata=metadata or {}
        )
        
        logger.info(f"Stock compensated successfully: product_id={product_id}, new_stock={inventory.stock}")
        
        return {
            'status': 'compensated',
            'product_id': product_id,
            'new_stock': inventory.stock
        }

    @staticmethod
    def get_inventory(product_id):
        """Get inventory for a product."""
        try:
            inventory = Inventory.objects.get(product_id=product_id)
            return {
                'product_id': inventory.product_id,
                'stock': inventory.stock,
                'reserved': inventory.reserved,
                'available': inventory.available
            }
        except Inventory.DoesNotExist:
            return None
