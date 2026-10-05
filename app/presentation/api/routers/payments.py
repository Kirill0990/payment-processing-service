from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.application.dto import CreatePaymentCommand
from app.application.use_cases import CreatePayment, GetPayment
from app.presentation.api.dependencies import get_create_payment, get_payment
from app.presentation.api.schemas import (
    CreatePaymentRequest,
    ErrorResponse,
    PaymentAcceptedResponse,
    PaymentDetailsResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])


async def get_idempotency_key(
    value: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
) -> str:
    """Извлекает и нормализует обязательный ключ идемпотентности."""

    idempotency_key = value.strip()
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Заголовок Idempotency-Key не может быть пустым",
        )
    return idempotency_key


@router.post(
    "",
    response_model=PaymentAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment(
    request: CreatePaymentRequest,
    idempotency_key: Annotated[str, Depends(get_idempotency_key)],
    use_case: Annotated[CreatePayment, Depends(get_create_payment)],
) -> PaymentAcceptedResponse:
    """Принимает новый платёж в асинхронную обработку."""

    payment = await use_case.execute(
        CreatePaymentCommand(
            amount=request.amount,
            currency=request.currency,
            idempotency_key=idempotency_key,
            webhook_url=str(request.webhook_url),
            description=request.description,
            metadata=request.metadata,
        )
    )
    return PaymentAcceptedResponse.from_dto(payment)


@router.get(
    "/{payment_id}",
    response_model=PaymentDetailsResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def get_payment_details(
    payment_id: UUID,
    use_case: Annotated[GetPayment, Depends(get_payment)],
) -> PaymentDetailsResponse:
    """Возвращает актуальное состояние платежа."""

    payment = await use_case.execute(payment_id)
    return PaymentDetailsResponse.from_dto(payment)
