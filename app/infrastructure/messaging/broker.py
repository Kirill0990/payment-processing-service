from faststream.rabbit import RabbitBroker

from app.infrastructure.config import get_settings

broker = RabbitBroker(get_settings().rabbitmq_url)
