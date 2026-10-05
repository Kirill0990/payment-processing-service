from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base


class OutboxModel(Base):
    """Событие, ожидающее гарантированной публикации в брокер."""

    __tablename__ = "outbox"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
