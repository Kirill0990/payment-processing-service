from datetime import datetime
from typing import Protocol
from uuid import UUID


class DomainEvent(Protocol):
    """Контракт события, возникшего в доменной модели."""

    @property
    def event_id(self) -> UUID: ...

    @property
    def occurred_at(self) -> datetime: ...
