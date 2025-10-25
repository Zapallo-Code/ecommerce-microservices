from . import TransactionState


class TransactionStore:
    def __init__(self) -> None:
        self._transactions: dict[str, TransactionState] = {}

    def save(self, transaction: TransactionState) -> None:
        self._transactions[transaction.transaction_id] = transaction

    def get(self, transaction_id: str) -> TransactionState | None:
        return self._transactions.get(transaction_id)

    def get_all(self) -> list[TransactionState]:
        return list(self._transactions.values())

    def delete(self, transaction_id: str) -> bool:
        if transaction_id in self._transactions:
            del self._transactions[transaction_id]
            return True
        return False

    def count(self) -> int:
        return len(self._transactions)


transaction_store = TransactionStore()
