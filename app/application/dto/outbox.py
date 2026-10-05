from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    """Событие, ожидающее публикации в брокер сообщений."""

    id: UUID
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
    attempts: int
