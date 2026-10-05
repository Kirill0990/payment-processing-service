from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import OutboxRepository
from app.domain.events import DomainEvent, PaymentCreated
from app.infrastructure.database.models import OutboxModel


class SQLAlchemyOutboxRepository(OutboxRepository):
    """Сохраняет доменные события в transactional outbox."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: DomainEvent) -> None:
        aggregate_id, payload = self._serialize(event)
        self._session.add(
            OutboxModel(
                id=event.event_id,
                event_type=event.event_type,
                aggregate_id=aggregate_id,
                payload=payload,
                created_at=event.occurred_at,
            )
        )

    @staticmethod
    def _serialize(event: DomainEvent) -> tuple[UUID, dict[str, Any]]:
        if isinstance(event, PaymentCreated):
            return event.payment_id, {
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "payment_id": str(event.payment_id),
            }
        raise TypeError(f"Неподдерживаемый тип доменного события: {type(event).__name__}")
