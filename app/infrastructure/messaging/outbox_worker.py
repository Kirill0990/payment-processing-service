import asyncio

from app.application.use_cases import PublishOutbox
from app.infrastructure.config import get_settings
from app.infrastructure.database.repositories import SQLAlchemyOutboxRepository
from app.infrastructure.database.session import session_factory
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.messaging.broker import broker
from app.infrastructure.messaging.publisher import RabbitEventPublisher


async def run_outbox_publisher() -> None:
    """Периодически публикует накопленные outbox-события."""

    settings = get_settings()
    event_publisher = RabbitEventPublisher(broker)

    while True:
        async with session_factory() as session:
            use_case = PublishOutbox(
                SQLAlchemyUnitOfWork(session),
                SQLAlchemyOutboxRepository(session),
                event_publisher,
            )
            await use_case.execute()
        await asyncio.sleep(settings.outbox_poll_interval)
