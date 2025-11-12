"""
Service layer for Purchase business logic.
Implements Saga pattern with simulated failures and latency.
Follows SOLID principles and clean code practices.
"""
import random
import time
import logging
from typing import Dict, Any
from django.db import transaction
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
    
    @staticmethod
    def _simulate_latency():
        """Simulate network/processing latency."""
        latency_ms = random.randint(
            PurchaseService.MIN_LATENCY_MS,
            PurchaseService.MAX_LATENCY_MS
        )
        time.sleep(latency_ms / 1000.0)
        logger.debug(f"Simulated latency: {latency_ms}ms")
    
    @staticmethod
    def _should_succeed() -> bool:
        """Determine if operation should succeed (50% random)."""
        return random.random() < PurchaseService.SUCCESS_RATE
    
    @transaction.atomic
    def create_purchase(
        self,
        transaction_id: str,
        user_id: str,
        product_id: str,
        payment_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Process a purchase transaction using Saga pattern.
        Returns 200 (success) or 409 (conflict) randomly.
        
        Args:
            transaction_id: Unique transaction ID from orchestrator
            user_id: User/customer identifier
            product_id: Product identifier
            payment_id: Payment transaction identifier
            amount: Purchase amount
            
        Returns:
            Dict with status and purchase data or error info
        """
        logger.info(
            f"Processing purchase transaction: {transaction_id} "
            f"for user {user_id}"
        )
        
        # Simulate network/processing latency
        self._simulate_latency()
        
        try:
            # Check if transaction already exists (idempotency)
            existing = Purchase.objects.filter(
                transaction_id=transaction_id
            ).first()
            
            if existing:
                logger.warning(
                    f"Transaction {transaction_id} already exists"
                )
                if existing.is_success():
                    return {
                        'status': 'success',
                        'purchase_id': existing.id,
                        'transaction_id': existing.transaction_id
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'Purchase failed',
                        'error': 'CONFLICT'
                    }
            
            # Create purchase record
            purchase = Purchase.objects.create(
                transaction_id=transaction_id,
                user_id=user_id,
                product_id=product_id,
                payment_id=payment_id,
                amount=amount,
                status=Purchase.STATUS_PENDING
            )
            
            logger.info(
                f"Purchase {purchase.id} created for "
                f"transaction {transaction_id}"
            )
            
            # Simulate random success/failure (50%)
            if self._should_succeed():
                # Success path
                purchase.mark_success()
                logger.info(
                    f"Purchase {purchase.id} succeeded "
                    f"(transaction {transaction_id})"
                )
                
                return {
                    'status': 'success',
                    'purchase_id': purchase.id,
                    'transaction_id': purchase.transaction_id
                }
            else:
                # Failure path - mark as failed and return conflict
                error_msg = 'Purchase failed'
                purchase.mark_failed(error_msg)
                logger.warning(
                    f"Purchase {purchase.id} failed "
                    f"(transaction {transaction_id})"
                )
                
                return {
                    'status': 'error',
                    'message': error_msg,
                    'error': 'CONFLICT'
                }
                
        except Exception as e:
            logger.error(
                f"Error processing transaction {transaction_id}: {str(e)}",
                exc_info=True
            )
            return {
                'status': 'error',
                'message': f'Internal error: {str(e)}',
                'error': 'INTERNAL_ERROR'
            }
    
    @transaction.atomic
    def cancel_purchase(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Cancel/compensate a purchase transaction.
        Part of the Saga compensation flow.
        Always returns 200 OK.
        
        Args:
            transaction_id: Transaction ID to cancel
            
        Returns:
            Dict with cancellation result (always success)
        """
        logger.info(f"Cancelling purchase transaction: {transaction_id}")
        
        # Simulate network/processing latency
        self._simulate_latency()
        
        try:
            purchase = Purchase.objects.filter(
                transaction_id=transaction_id
            ).first()
            
            if not purchase:
                logger.warning(
                    f"Transaction {transaction_id} not found for "
                    f"cancellation"
                )
                # Still return success for idempotency
                return {
                    'status': 'success',
                    'message': 'Purchase cancelled successfully',
                    'transaction_id': transaction_id
                }
            
            # Cancel the purchase
            purchase.cancel()
            logger.info(
                f"Purchase {purchase.id} cancelled "
                f"(transaction {transaction_id})"
            )
            
            return {
                'status': 'success',
                'message': 'Purchase cancelled successfully',
                'transaction_id': transaction_id
            }
            
        except Exception as e:
            logger.error(
                f"Error cancelling transaction {transaction_id}: {str(e)}",
                exc_info=True
            )
            # Even on error, return success for compensation
            # to not break the Saga flow
            return {
                'status': 'success',
                'message': 'Purchase cancellation completed',
                'transaction_id': transaction_id
            }
