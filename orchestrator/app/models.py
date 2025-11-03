from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    COMPENSATED = "COMPENSATED"
    FAILED = "FAILED"


class TransactionRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., gt=0, description="Transaction amount")


class TransactionResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    message: str
    details: dict[str, object]
    timestamp: datetime


class TransactionState(BaseModel):
    transaction_id: str
    status: TransactionStatus
    user_id: str
    product_id: str | None = None
    payment_id: str | None = None
    inventory_updated: bool = False
    purchase_registered: bool = False
    amount: float
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
