from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dto import OutboxMessage
from app.application.messaging import PAYMENT_MESSAGES
from app.application.ports import OutboxRepository
from app.domain.events import DomainEvent, PaymentCreated
from app.infrastructure.database.models import OutboxModel


class SQLAlchemyOutboxRepository(OutboxRepository):
    """Сохраняет доменные события в transactional outbox."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: DomainEvent) -> None:
        event_type, aggregate_id, payload = self._serialize(event)
        self._session.add(
            OutboxModel(
                id=event.event_id,
                event_type=event_type,
                aggregate_id=aggregate_id,
                payload=payload,
                created_at=event.occurred_at,
            )
        )

    async def get_pending(self, limit: int) -> list[OutboxMessage]:
        """Блокирует и возвращает очередную пачку неопубликованных событий."""

        statement = (
            select(OutboxModel)
            .where(OutboxModel.published_at.is_(None))
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        models = (await self._session.scalars(statement)).all()
        return [self._to_message(model) for model in models]

    async def mark_published(self, message_id: UUID, published_at: datetime) -> None:
        statement = (
            update(OutboxModel)
            .where(OutboxModel.id == message_id)
            .values(published_at=published_at, last_error=None)
        )
        await self._session.execute(statement)

    async def mark_failed(self, message_id: UUID, error: str) -> None:
        statement = (
            update(OutboxModel)
            .where(OutboxModel.id == message_id)
            .values(
                attempts=OutboxModel.attempts + 1,
                last_error=error,
            )
        )
        await self._session.execute(statement)

    @staticmethod
    def _to_message(model: OutboxModel) -> OutboxMessage:
        return OutboxMessage(
            id=model.id,
            event_type=model.event_type,
            payload=dict(model.payload),
            created_at=model.created_at,
            attempts=model.attempts,
        )

    @staticmethod
    def _serialize(event: DomainEvent) -> tuple[str, UUID, dict[str, Any]]:
        if isinstance(event, PaymentCreated):
            return PAYMENT_MESSAGES.created, event.payment_id, {
                "event_id": str(event.event_id),
                "event_type": PAYMENT_MESSAGES.created,
                "occurred_at": event.occurred_at.isoformat(),
                "payment_id": str(event.payment_id),
            }
        raise TypeError(f"Неподдерживаемый тип доменного события: {type(event).__name__}")
