from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.domain.enums import Currency, PaymentStatus
from app.domain.events import DomainEvent, PaymentCreated
from app.domain.exceptions import (
    InvalidPaymentAmountError,
    InvalidPaymentStateTransitionError,
)


@dataclass(slots=True)
class Payment:
    """Доменная сущность платежа и правила изменения его состояния."""

    id: UUID
    amount: Decimal
    currency: Currency
    idempotency_key: str
    webhook_url: str
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0"):
            raise InvalidPaymentAmountError
        if not self.idempotency_key.strip():
            raise ValueError("Idempotency key must not be empty")
        if not self.webhook_url.strip():
            raise ValueError("Webhook URL must not be empty")

    @classmethod
    def create(
        cls,
        *,
        amount: Decimal,
        currency: Currency,
        idempotency_key: str,
        webhook_url: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
        payment_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> "Payment":
        """Создаёт новый платёж в состоянии ожидания обработки."""

        payment = cls(
            id=payment_id or uuid4(),
            amount=amount,
            currency=currency,
            idempotency_key=idempotency_key,
            webhook_url=webhook_url,
            description=description,
            metadata=dict(metadata or {}),
            created_at=created_at or datetime.now(UTC),
        )
        payment._events.append(PaymentCreated(payment_id=payment.id))
        return payment

    @property
    def events(self) -> tuple[DomainEvent, ...]:
        """Возвращает накопленные события без возможности изменить коллекцию."""

        return tuple(self._events)

    def clear_events(self) -> None:
        """Удаляет события после их успешного сохранения вместе с агрегатом."""

        self._events.clear()

    def mark_succeeded(self, *, processed_at: datetime | None = None) -> None:
        """Помечает ожидающий платёж как успешно обработанный."""

        self._finish(PaymentStatus.SUCCEEDED, processed_at)

    def mark_failed(self, *, processed_at: datetime | None = None) -> None:
        """Помечает ожидающий платёж как завершившийся ошибкой."""

        self._finish(PaymentStatus.FAILED, processed_at)

    def _finish(self, target: PaymentStatus, processed_at: datetime | None) -> None:
        if self.status is not PaymentStatus.PENDING:
            raise InvalidPaymentStateTransitionError(self.status, target)
        self.status = target
        self.processed_at = processed_at or datetime.now(UTC)
