from typing import Any
from uuid import UUID

from faststream.rabbit import RabbitBroker

from app.application.ports import EventPublisher
from app.infrastructure.messaging.topology import payments_exchange, payments_queue


class RabbitEventPublisher(EventPublisher):
    """Публикует outbox-события в RabbitMQ через FastStream."""

    def __init__(self, broker: RabbitBroker) -> None:
        self._broker = broker

    async def publish(
        self,
        *,
        message_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        await self._broker.publish(
            payload,
            queue=payments_queue,
            exchange=payments_exchange,
            routing_key=event_type,
            message_id=str(message_id),
            message_type=event_type,
            persist=True,
        )
