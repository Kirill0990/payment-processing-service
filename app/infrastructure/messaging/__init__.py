"""Адаптеры RabbitMQ, обработчики сообщений и издатель outbox-событий."""

from app.infrastructure.messaging.broker import broker
from app.infrastructure.messaging.publisher import RabbitEventPublisher
from app.infrastructure.messaging.topology import (
    dead_letter_exchange,
    dead_letter_queue,
    payments_exchange,
    payments_queue,
)

__all__ = [
    "RabbitEventPublisher",
    "broker",
    "dead_letter_exchange",
    "dead_letter_queue",
    "payments_exchange",
    "payments_queue",
]
