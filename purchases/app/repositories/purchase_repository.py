from decimal import Decimal

from django.db.models import QuerySet

from app.models import Purchase


class PurchaseRepository:
    @classmethod
    def get_by_transaction_id(cls, transaction_id: str) -> Purchase | None:
        try:
            return Purchase.objects.get(transaction_id=transaction_id)
        except Purchase.DoesNotExist:
            return None

    @classmethod
    def get_by_user(
        cls,
        user_id: str,
        limit: int = 100,
    ) -> QuerySet[Purchase]:
        return Purchase.objects.filter(user_id=user_id)[:limit]

    @classmethod
    def create(
        cls,
        transaction_id: str,
        user_id: str,
        product_id: str,
        payment_id: str,
        amount: Decimal,
        quantity: int = 1,
        status: str | None = None,
    ) -> Purchase:
        kwargs = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "product_id": product_id,
            "payment_id": payment_id,
            "amount": amount,
            "quantity": quantity,
        }
        if status is not None:
            kwargs["status"] = status
        return Purchase.objects.create(**kwargs)
