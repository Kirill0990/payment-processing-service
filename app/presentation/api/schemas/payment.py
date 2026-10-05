from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.application.dto import PaymentDTO
from app.domain.enums import Currency, PaymentStatus


class CreatePaymentRequest(BaseModel):
    """Тело запроса на создание платежа."""

    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: Currency
    description: str | None = Field(default=None, max_length=2_000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class PaymentAcceptedResponse(BaseModel):
    """Ответ о принятом в асинхронную обработку платеже."""

    payment_id: UUID
    status: PaymentStatus
    created_at: datetime

    @classmethod
    def from_dto(cls, payment: PaymentDTO) -> "PaymentAcceptedResponse":
        return cls(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )


class PaymentDetailsResponse(BaseModel):
    """Подробная информация о платеже."""

    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str | None
    metadata: dict[str, Any]
    status: PaymentStatus
    webhook_url: HttpUrl
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def from_dto(cls, payment: PaymentDTO) -> "PaymentDetailsResponse":
        return cls(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            status=payment.status,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )


class ErrorResponse(BaseModel):
    """Стандартное описание ошибки HTTP API."""

    detail: str
