from typing import Protocol

from app.domain.entities import Payment


class WebhookSender(Protocol):
    """Порт отправки результата обработки на webhook клиента."""

    async def send(self, payment: Payment) -> None: ...
