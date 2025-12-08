from . import TransactionDetail


class TransactionStore:
    def __init__(self) -> None:
        self._transactions: dict[str, TransactionDetail] = {}

    def save(self, transaction: TransactionDetail) -> None:
        self._transactions[transaction.transaction_id] = transaction

    def get(self, transaction_id: str) -> TransactionDetail | None:
        return self._transactions.get(transaction_id)

    def get_all(self) -> list[TransactionDetail]:
        return list(self._transactions.values())

    def count(self) -> int:
        return len(self._transactions)


transaction_store = TransactionStore()
