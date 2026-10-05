from typing import Protocol

from app.domain.events import DomainEvent


class OutboxRepository(Protocol):
    """Порт хранилища событий transactional outbox."""

    async def add(self, event: DomainEvent) -> None: ...
