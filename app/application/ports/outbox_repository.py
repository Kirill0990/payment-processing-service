from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.dto import OutboxMessage
from app.domain.events import DomainEvent


class OutboxRepository(Protocol):
    """Порт хранилища событий transactional outbox."""

    async def add(self, event: DomainEvent) -> None: ...

    async def get_pending(self, limit: int) -> list[OutboxMessage]: ...

    async def mark_published(self, message_id: UUID, published_at: datetime) -> None: ...

    async def mark_failed(self, message_id: UUID, error: str) -> None: ...
