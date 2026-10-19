from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID


class WalletError(Exception):
    """Base class for expected domain errors."""


class WalletNotFound(WalletError):
    pass


class UnauthorizedTransfer(WalletError):
    pass


class InvalidTransfer(WalletError):
    pass


class InsufficientFunds(WalletError):
    pass


@dataclass(frozen=True, slots=True)
class Wallet:
    id: UUID
    owner_id: UUID
    balance: Decimal


@dataclass(frozen=True, slots=True)
class Transfer:
    id: UUID
    actor_id: UUID
    source_wallet_id: UUID
    destination_wallet_id: UUID
    amount: Decimal
    idempotency_key: str
    created_at: datetime

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)
