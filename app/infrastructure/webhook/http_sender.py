import httpx

from app.application.ports import WebhookSender
from app.domain.entities import Payment


class HttpWebhookSender(WebhookSender):
    """Отправляет результат обработки платежа на HTTP webhook клиента."""

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout

    async def send(self, payment: Payment) -> None:
        payload = {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "processed_at": (
                payment.processed_at.isoformat() if payment.processed_at is not None else None
            ),
        }
        headers = {"Idempotency-Key": f"payment-result:{payment.id}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                payment.webhook_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
