from dataclasses import dataclass

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

from app.application.messaging import PAYMENT_MESSAGES


@dataclass(frozen=True, slots=True)
class RabbitTopology:
    """Имена объектов RabbitMQ платежного сервиса."""

    events_exchange: str = "payments.events"
    payments_queue: str = "payments.new"
    dead_letter_exchange: str = "payments.dlx"
    dead_letter_queue: str = "payments.dlq"
    dead_letter_routing_key: str = "payments.failed"


RABBIT_TOPOLOGY = RabbitTopology()

payments_exchange = RabbitExchange(
    RABBIT_TOPOLOGY.events_exchange,
    type=ExchangeType.DIRECT,
)
dead_letter_exchange = RabbitExchange(
    RABBIT_TOPOLOGY.dead_letter_exchange,
    type=ExchangeType.DIRECT,
)
dead_letter_queue = RabbitQueue(
    RABBIT_TOPOLOGY.dead_letter_queue,
    routing_key=RABBIT_TOPOLOGY.dead_letter_routing_key,
)
payments_queue = RabbitQueue(
    RABBIT_TOPOLOGY.payments_queue,
    routing_key=PAYMENT_MESSAGES.created,
    arguments={
        "x-dead-letter-exchange": RABBIT_TOPOLOGY.dead_letter_exchange,
        "x-dead-letter-routing-key": RABBIT_TOPOLOGY.dead_letter_routing_key,
    },
)
