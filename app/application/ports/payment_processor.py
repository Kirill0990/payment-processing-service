from typing import Protocol

from app.domain.entities import Payment


class PaymentProcessor(Protocol):
    """Порт внешнего платёжного шлюза."""

    async def process(self, payment: Payment) -> bool: ...
