from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class PaymentCreated:
    """Событие создания платежа для последующей публикации через outbox."""

    payment_id: UUID
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    event_type: str = field(default="payment.created", init=False)
