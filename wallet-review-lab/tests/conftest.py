from decimal import Decimal
from uuid import UUID

import pytest

from app.domain import Wallet
from app.repository import InMemoryWalletRepository
from app.service import TransferService

USER_A = UUID("10000000-0000-0000-0000-000000000001")
USER_B = UUID("10000000-0000-0000-0000-000000000002")
WALLET_A = UUID("20000000-0000-0000-0000-000000000001")
WALLET_B = UUID("20000000-0000-0000-0000-000000000002")


@pytest.fixture
def repository() -> InMemoryWalletRepository:
    return InMemoryWalletRepository(
        [
            Wallet(WALLET_A, USER_A, Decimal("100.00")),
            Wallet(WALLET_B, USER_B, Decimal("50.00")),
        ]
    )


@pytest.fixture
def service(repository: InMemoryWalletRepository) -> TransferService:
    return TransferService(repository)
