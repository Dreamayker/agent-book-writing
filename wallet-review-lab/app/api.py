from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app.domain import UnauthorizedTransfer, Wallet, WalletError, WalletNotFound
from app.repository import InMemoryWalletRepository, WalletRepository
from app.service import TransferService

DEMO_USER_A = UUID("10000000-0000-0000-0000-000000000001")
DEMO_USER_B = UUID("10000000-0000-0000-0000-000000000002")
DEMO_WALLET_A = UUID("20000000-0000-0000-0000-000000000001")
DEMO_WALLET_B = UUID("20000000-0000-0000-0000-000000000002")

class TransferRequest(BaseModel):
    source_wallet_id: UUID
    destination_wallet_id: UUID
    amount: Decimal = Field(gt=0, decimal_places=2)
    idempotency_key: str = Field(min_length=8, max_length=128)


class TransferResponse(BaseModel):
    transfer_id: UUID
    amount: Decimal


def create_app(repository: WalletRepository) -> FastAPI:
    application = FastAPI(title="Wallet Review Lab", version="0.1.0")
    service = TransferService(repository)

    def get_service() -> TransferService:
        return service

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/transfers", response_model=TransferResponse)
    def create_transfer(
        request: TransferRequest,
        x_user_id: Annotated[UUID, Header(description="Teaching-only identity header")],
        transfer_service: Annotated[TransferService, Depends(get_service)],
    ) -> TransferResponse:
        try:
            transfer = transfer_service.transfer(
                actor_id=x_user_id,
                source_wallet_id=request.source_wallet_id,
                destination_wallet_id=request.destination_wallet_id,
                amount=request.amount,
                idempotency_key=request.idempotency_key,
            )
        except UnauthorizedTransfer as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except WalletNotFound as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except WalletError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return TransferResponse(transfer_id=transfer.id, amount=transfer.amount)

    return application


repository = InMemoryWalletRepository(
    [
        Wallet(DEMO_WALLET_A, DEMO_USER_A, Decimal("100.00")),
        Wallet(DEMO_WALLET_B, DEMO_USER_B, Decimal("50.00")),
    ]
)
app = create_app(repository)
