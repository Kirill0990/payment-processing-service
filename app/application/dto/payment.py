from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.entities import Payment
from app.domain.enums import Currency, PaymentStatus


@dataclass(frozen=True, slots=True)
class CreatePaymentCommand:
    """Входные данные сценария создания платежа."""

    amount: Decimal
    currency: Currency
    idempotency_key: str
    webhook_url: str
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PaymentDTO:
    """Снимок платежа, возвращаемый сценарием приложения."""

    id: UUID
    amount: Decimal
    currency: Currency
    description: str | None
    metadata: dict[str, Any]
    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def from_entity(cls, payment: Payment) -> "PaymentDTO":
        """Создаёт DTO из доменной сущности без передачи изменяемых данных по ссылке."""

        return cls(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=dict(payment.metadata),
            status=payment.status,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
