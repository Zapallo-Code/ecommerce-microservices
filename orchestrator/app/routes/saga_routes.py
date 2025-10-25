from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from . import (
    SagaService,
    TransactionRequest,
    TransactionResponse,
    TransactionState,
    TransactionStatus,
    transaction_store,
)

router = APIRouter(prefix="/saga", tags=["Saga Orchestrator"])
saga_service = SagaService()


@router.post(
    "/transaction", response_model=TransactionResponse, status_code=status.HTTP_200_OK
)
async def initiate_transaction(request: TransactionRequest) -> TransactionResponse:
    try:
        transaction = await saga_service.execute_saga(request)

        return TransactionResponse(
            transaction_id=transaction.transaction_id,
            status=transaction.status,
            message="Transaction completed successfully",
            details={
                "user_id": transaction.user_id,
                "product_id": transaction.product_id,
                "payment_id": transaction.payment_id,
                "amount": transaction.amount,
            },
            timestamp=transaction.completed_at or datetime.now(),
        )

    except Exception as e:
        transactions = transaction_store.get_all()
        last_transaction = transactions[-1] if transactions else None

        transaction_id = (
            last_transaction.transaction_id if last_transaction else "unknown"
        )
        error_message = last_transaction.error_message if last_transaction else str(e)

        return TransactionResponse(
            transaction_id=transaction_id,
            status=TransactionStatus.COMPENSATED,
            message="Transaction was reverted",
            details={
                "user_id": request.user_id,
                "product_id": last_transaction.product_id if last_transaction else None,
                "payment_id": last_transaction.payment_id if last_transaction else None,
                "error": error_message,
            },
            timestamp=datetime.now(),
        )


@router.get("/status/{transaction_id}", response_model=TransactionState)
async def get_transaction_status(transaction_id: str) -> TransactionState:
    transaction = transaction_store.get(transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    return transaction


@router.get("/transactions")
async def list_transactions() -> dict[str, object]:
    return {
        "total": transaction_store.count(),
        "transactions": transaction_store.get_all(),
    }
