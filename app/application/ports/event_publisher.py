from typing import Any, Protocol
from uuid import UUID


class EventPublisher(Protocol):
    """Порт публикации событий во внешний брокер сообщений."""

    async def publish(
        self,
        *,
        message_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None: ...
