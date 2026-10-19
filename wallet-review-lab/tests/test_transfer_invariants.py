from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.domain import InsufficientFunds, InvalidTransfer, UnauthorizedTransfer
from app.repository import InMemoryWalletRepository
from app.service import TransferService
from tests.conftest import USER_A, USER_B, WALLET_A, WALLET_B


@given(st.decimals(min_value="0.01", max_value="100.00", places=2, allow_nan=False))
def test_successful_transfer_preserves_total_balance(amount: Decimal) -> None:
    from app.domain import Wallet

    repository = InMemoryWalletRepository(
        [Wallet(WALLET_A, USER_A, Decimal("100.00")), Wallet(WALLET_B, USER_B, Decimal("50"))]
    )
    before = repository.total_balance()
    TransferService(repository).transfer(
        actor_id=USER_A,
        source_wallet_id=WALLET_A,
        destination_wallet_id=WALLET_B,
        amount=amount,
        idempotency_key=f"property-{amount}",
    )
    assert repository.total_balance() == before


def test_balance_never_becomes_negative(
    service: TransferService, repository: InMemoryWalletRepository
) -> None:
    with pytest.raises(InsufficientFunds):
        service.transfer(
            actor_id=USER_A,
            source_wallet_id=WALLET_A,
            destination_wallet_id=WALLET_B,
            amount=Decimal("100.01"),
            idempotency_key="too-expensive",
        )
    assert repository.get_wallet(WALLET_A).balance == Decimal("100.00")


def test_idempotent_retry_only_moves_money_once(
    service: TransferService, repository: InMemoryWalletRepository
) -> None:
    request = dict(
        actor_id=USER_A,
        source_wallet_id=WALLET_A,
        destination_wallet_id=WALLET_B,
        amount=Decimal("10.00"),
        idempotency_key="retry-key-001",
    )
    first = service.transfer(**request)
    second = service.transfer(**request)
    assert first == second
    assert repository.get_wallet(WALLET_A).balance == Decimal("90.00")
    assert repository.get_wallet(WALLET_B).balance == Decimal("60.00")


def test_actor_cannot_spend_another_users_wallet(service: TransferService) -> None:
    with pytest.raises(UnauthorizedTransfer):
        service.transfer(
            actor_id=USER_B,
            source_wallet_id=WALLET_A,
            destination_wallet_id=WALLET_B,
            amount=Decimal("1.00"),
            idempotency_key="unauthorized-001",
        )


@pytest.mark.concurrency
def test_concurrent_transfers_cannot_double_spend(
    service: TransferService, repository: InMemoryWalletRepository
) -> None:
    def transfer(index: int) -> bool:
        try:
            service.transfer(
                actor_id=USER_A,
                source_wallet_id=WALLET_A,
                destination_wallet_id=WALLET_B,
                amount=Decimal("80.00"),
                idempotency_key=f"concurrent-{index}",
            )
        except InsufficientFunds:
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(transfer, range(2)))

    assert outcomes.count(True) == 1
    assert repository.get_wallet(WALLET_A).balance == Decimal("20.00")
    assert repository.get_wallet(WALLET_B).balance == Decimal("130.00")
    assert repository.total_balance() == Decimal("150.00")


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1"), Decimal("NaN")])
def test_invalid_amounts_are_rejected(service: TransferService, amount: Decimal) -> None:
    with pytest.raises(InvalidTransfer):
        service.transfer(
            actor_id=USER_A,
            source_wallet_id=WALLET_A,
            destination_wallet_id=WALLET_B,
            amount=amount,
            idempotency_key="invalid-amount",
        )
