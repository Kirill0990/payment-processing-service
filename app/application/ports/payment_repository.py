from typing import Protocol
from uuid import UUID

from app.domain.entities import Payment


class PaymentRepository(Protocol):
    """Порт хранилища платежей."""

    async def add(self, payment: Payment) -> None: ...

    async def get_by_id(self, payment_id: UUID) -> Payment | None: ...

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None: ...
