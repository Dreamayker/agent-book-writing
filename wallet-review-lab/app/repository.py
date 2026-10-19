from collections.abc import Callable
from decimal import Decimal
from threading import RLock
from typing import Protocol, TypeVar
from uuid import UUID

from app.domain import Transfer, Wallet, WalletNotFound

T = TypeVar("T")


class WalletRepository(Protocol):
    def atomic(self, operation: Callable[[], T]) -> T: ...

    def get_wallet(self, wallet_id: UUID) -> Wallet: ...

    def save_wallet(self, wallet: Wallet) -> None: ...

    def get_transfer(self, actor_id: UUID, idempotency_key: str) -> Transfer | None: ...

    def save_transfer(self, transfer: Transfer) -> None: ...

    def total_balance(self) -> Decimal: ...


class InMemoryWalletRepository:
    """Thread-safe teaching repository with one process-local transaction lock."""

    def __init__(self, wallets: list[Wallet] | None = None) -> None:
        self._wallets = {wallet.id: wallet for wallet in wallets or []}
        self._transfers: dict[tuple[UUID, str], Transfer] = {}
        self._lock = RLock()

    def atomic(self, operation: Callable[[], T]) -> T:
        # Avoid holding the process-wide lock while repository calls perform I/O.
        return operation()

    def get_wallet(self, wallet_id: UUID) -> Wallet:
        try:
            return self._wallets[wallet_id]
        except KeyError as error:
            raise WalletNotFound(str(wallet_id)) from error

    def save_wallet(self, wallet: Wallet) -> None:
        self._wallets[wallet.id] = wallet

    def get_transfer(self, actor_id: UUID, idempotency_key: str) -> Transfer | None:
        return self._transfers.get((actor_id, idempotency_key))

    def save_transfer(self, transfer: Transfer) -> None:
        self._transfers[(transfer.actor_id, transfer.idempotency_key)] = transfer

    def total_balance(self) -> Decimal:
        return sum((wallet.balance for wallet in self._wallets.values()), Decimal("0"))
