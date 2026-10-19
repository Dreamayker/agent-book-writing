from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.domain import Wallet
from app.repository import InMemoryWalletRepository
from tests.conftest import USER_A, USER_B, WALLET_A, WALLET_B


@pytest.fixture
def api_repository() -> InMemoryWalletRepository:
    return InMemoryWalletRepository(
        [
            Wallet(WALLET_A, USER_A, Decimal("100.00")),
            Wallet(WALLET_B, USER_B, Decimal("50.00")),
        ]
    )


@pytest.fixture
def client(api_repository: InMemoryWalletRepository) -> TestClient:
    return TestClient(create_app(api_repository))


def transfer_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_wallet_id": str(WALLET_A),
        "destination_wallet_id": str(WALLET_B),
        "amount": "10.00",
        "idempotency_key": "api-request-001",
    }
    payload.update(overrides)
    return payload


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_successful_transfer_updates_balances(
    client: TestClient, api_repository: InMemoryWalletRepository
) -> None:
    response = client.post(
        "/transfers", json=transfer_payload(), headers={"X-User-Id": str(USER_A)}
    )
    assert response.status_code == 200
    assert response.json()["amount"] == "10.00"
    assert api_repository.get_wallet(WALLET_A).balance == Decimal("90.00")
    assert api_repository.get_wallet(WALLET_B).balance == Decimal("60.00")


def test_idempotent_api_retry_returns_same_transfer(client: TestClient) -> None:
    request = transfer_payload()
    headers = {"X-User-Id": str(USER_A)}
    first = client.post("/transfers", json=request, headers=headers)
    second = client.post("/transfers", json=request, headers=headers)
    assert first.status_code == second.status_code == 200
    assert first.json()["transfer_id"] == second.json()["transfer_id"]


def test_missing_identity_header_is_rejected(client: TestClient) -> None:
    response = client.post("/transfers", json=transfer_payload())
    assert response.status_code == 422


def test_malformed_identity_header_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/transfers", json=transfer_payload(), headers={"X-User-Id": "not-a-uuid"}
    )
    assert response.status_code == 422


def test_actor_cannot_spend_another_users_wallet(client: TestClient) -> None:
    response = client.post(
        "/transfers", json=transfer_payload(), headers={"X-User-Id": str(USER_B)}
    )
    assert response.status_code == 403


@pytest.mark.parametrize("amount", ["0", "-1", "0.001"])
def test_invalid_amount_is_rejected_by_request_schema(client: TestClient, amount: str) -> None:
    response = client.post(
        "/transfers",
        json=transfer_payload(amount=amount),
        headers={"X-User-Id": str(USER_A)},
    )
    assert response.status_code == 422


def test_unknown_wallet_returns_not_found(client: TestClient) -> None:
    response = client.post(
        "/transfers",
        json=transfer_payload(source_wallet_id=str(uuid4())),
        headers={"X-User-Id": str(USER_A)},
    )
    assert response.status_code == 404


def test_insufficient_balance_returns_bad_request(client: TestClient) -> None:
    response = client.post(
        "/transfers",
        json=transfer_payload(amount="100.01"),
        headers={"X-User-Id": str(USER_A)},
    )
    assert response.status_code == 400
