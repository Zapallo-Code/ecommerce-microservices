"""
Service layer for Purchase business logic.
Implements the Saga orchestration pattern with simulated failures.
"""
import random
import time
import uuid
import logging
from typing import Optional, Dict, Any
from app.repositories import PurchaseRepository
from app.models import Purchase

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
    COMPENSATION_MIN_LATENCY_MS = 30
    COMPENSATION_MAX_LATENCY_MS = 100
    
    def __init__(self):
        """Initialize the service."""
        self.repository = PurchaseRepository
    
    def process_purchase(
        self,
        customer_id: int,
        items: list
    ) -> Dict[str, Any]:
        """
        Process a purchase using the Saga pattern.
        Simulates random failures and latency.
        
        Args:
            customer_id: ID of the customer
            items: List of purchase items
            
        Returns:
            Dict with status, purchase data, and error info if any
        """
        saga_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting Saga {saga_id} for customer {customer_id}"
        )
        
        # Simulate network latency
        latency_ms = random.randint(
            self.MIN_LATENCY_MS,
            self.MAX_LATENCY_MS
        )
        time.sleep(latency_ms / 1000.0)
        
        try:
            # Create purchase in pending status
            purchase = self.repository.create_purchase(
                customer_id=customer_id,
                items=items,
                saga_id=saga_id
            )
            
            logger.info(
                f"Purchase {purchase.id} created for Saga {saga_id}"
            )
            
            # Simulate Saga orchestration - random success/failure
            if random.random() < self.SUCCESS_RATE:
                # Success path - confirm purchase
                purchase.confirm()
                logger.info(
                    f"Saga {saga_id} succeeded. "
                    f"Purchase {purchase.id} confirmed"
                )
                
                return {
                    'success': True,
                    'status': 'confirmed',
                    'purchase_id': purchase.id,
                    'saga_id': saga_id,
                    'message': 'Purchase processed successfully'
                }
            else:
                # Failure path - mark as failed
                error_msg = (
                    'Simulated failure: '
                    'External service unavailable'
                )
                purchase.fail(error_msg)
                logger.warning(
                    f"Saga {saga_id} failed. "
                    f"Purchase {purchase.id} marked as failed"
                )
                
                return {
                    'success': False,
                    'status': 'failed',
                    'purchase_id': purchase.id,
                    'saga_id': saga_id,
                    'message': error_msg,
                    'error': 'SAGA_EXECUTION_FAILED'
                }
                
        except Exception as e:
            logger.error(
                f"Error in Saga {saga_id}: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'status': 'error',
                'saga_id': saga_id,
                'message': f'Internal error: {str(e)}',
                'error': 'INTERNAL_ERROR'
            }
    
    def compensate_purchase(
        self,
        purchase_id: Optional[int] = None,
        saga_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compensate (cancel) a purchase.
        Part of the Saga compensation flow.
        
        Args:
            purchase_id: Purchase ID
            saga_id: Saga ID (alternative to purchase_id)
            
        Returns:
            Dict with compensation result
        """
        # Simulate compensation latency
        latency_ms = random.randint(
            self.COMPENSATION_MIN_LATENCY_MS,
            self.COMPENSATION_MAX_LATENCY_MS
        )
        time.sleep(latency_ms / 1000.0)
        
        try:
            # Find purchase
            if saga_id:
                purchase = self.repository.get_by_saga_id(saga_id)
            elif purchase_id:
                purchase = self.repository.get_by_id(purchase_id)
            else:
                return {
                    'success': False,
                    'message': 'Purchase ID or Saga ID required',
                    'error': 'MISSING_IDENTIFIER'
                }
            
            if not purchase:
                return {
                    'success': False,
                    'message': 'Purchase not found',
                    'error': 'NOT_FOUND'
                }
            
            logger.info(
                f"Compensating purchase {purchase.id} "
                f"(Saga {purchase.saga_id})"
            )
            
            # Cancel the purchase
            success = self.repository.cancel_purchase(purchase.id)
            
            if success:
                logger.info(
                    f"Purchase {purchase.id} successfully compensated"
                )
                return {
                    'success': True,
                    'status': 'cancelled',
                    'purchase_id': purchase.id,
                    'saga_id': purchase.saga_id,
                    'message': 'Purchase compensated successfully'
                }
            else:
                logger.warning(
                    f"Failed to compensate purchase {purchase.id}"
                )
                return {
                    'success': False,
                    'status': purchase.status,
                    'purchase_id': purchase.id,
                    'message': 'Cannot compensate purchase in current state',
                    'error': 'INVALID_STATE'
                }
                
        except Exception as e:
            logger.error(
                f"Error compensating purchase: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'message': f'Compensation error: {str(e)}',
                'error': 'COMPENSATION_ERROR'
            }
    
    def get_purchase(self, purchase_id: int) -> Optional[Purchase]:
        """
        Retrieve a purchase by ID.
        
        Args:
            purchase_id: Purchase ID
            
        Returns:
            Purchase instance or None
        """
        return self.repository.get_by_id(purchase_id)
    
    def get_customer_purchases(
        self,
        customer_id: int,
        limit: int = 100
    ) -> list:
        """
        Get all purchases for a customer.
        
        Args:
            customer_id: Customer ID
            limit: Maximum number of results
            
        Returns:
            List of Purchase instances
        """
        return self.repository.get_by_customer(customer_id, limit)
