from enum import StrEnum

from django.db import models


class PurchaseStatus(StrEnum):
    """Enum for purchase status values in Saga pattern."""

    PENDING = "pending"
    SUCCESS = "success"
    CANCELLED = "cancelled"
    FAILED = "failed"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:  # noqa: D102
        return [(status.value, status.name.title()) for status in cls]


class Purchase(models.Model):  # noqa: D101
    # Backwards compatibility: Status constants as class attributes
    STATUS_PENDING = PurchaseStatus.PENDING
    STATUS_SUCCESS = PurchaseStatus.SUCCESS
    STATUS_CANCELLED = PurchaseStatus.CANCELLED
    STATUS_FAILED = PurchaseStatus.FAILED

    # Core fields required by Saga orchestrator
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique transaction ID from orchestrator",
    )
    user_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="User/customer identifier",
    )
    product_id = models.CharField(
        max_length=255,
        help_text="Product identifier",
    )
    quantity = models.IntegerField(
        default=1,
        help_text="Quantity of products purchased",
    )
    payment_id = models.CharField(
        max_length=255,
        help_text="Payment transaction identifier",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Purchase amount",
    )

    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=PurchaseStatus.choices(),
        default=PurchaseStatus.PENDING,
        db_index=True,
    )
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:  # noqa: D106
        db_table = "purchases"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:  # noqa: D105
        return (
            f"Purchase {self.transaction_id} - "
            f"User {self.user_id} - {self.status}"
        )

    # Status transition methods (DRY pattern)

    def _update_status(
        self,
        new_status: PurchaseStatus,
        error_message: str | None = None,
    ) -> None:
        self.status = new_status
        if error_message:
            self.error_message = error_message

        fields_to_update = ["status"]
        if error_message:
            fields_to_update.append("error_message")

        self.save(update_fields=fields_to_update)

    def mark_success(self) -> None:  # noqa: D102
        self._update_status(PurchaseStatus.SUCCESS)

    def mark_failed(self, error_message: str | None = None) -> None:
        self._update_status(PurchaseStatus.FAILED, error_message)

    def cancel(self) -> None:  # noqa: D102
        self._update_status(PurchaseStatus.CANCELLED)

    # Status checkers as properties (more Pythonic)

    @property
    def is_pending(self) -> bool:  # noqa: D102
        return self.status == PurchaseStatus.PENDING

    @property
    def is_success(self) -> bool:  # noqa: D102
        return self.status == PurchaseStatus.SUCCESS

    @property
    def is_cancelled(self) -> bool:  # noqa: D102
        return self.status == PurchaseStatus.CANCELLED

    @property
    def is_failed(self) -> bool:  # noqa: D102
        return self.status == PurchaseStatus.FAILED
