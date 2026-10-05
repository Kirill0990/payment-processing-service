from dataclasses import dataclass
from datetime import UTC, datetime

from app.application.ports import EventPublisher, OutboxRepository, UnitOfWork


@dataclass(frozen=True, slots=True)
class PublishOutboxResult:
    """Результат одного прохода издателя outbox-событий."""

    published: int
    failed: int


class PublishOutbox:
    """Публикует ожидающие outbox-события и сохраняет результат попытки."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        outbox_repository: OutboxRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._outbox_repository = outbox_repository
        self._event_publisher = event_publisher

    async def execute(self, *, limit: int = 100) -> PublishOutboxResult:
        """Обрабатывает одну заблокированную пачку неопубликованных событий."""

        published = 0
        failed = 0

        async with self._unit_of_work:
            messages = await self._outbox_repository.get_pending(limit)
            for message in messages:
                try:
                    await self._event_publisher.publish(
                        message_id=message.id,
                        event_type=message.event_type,
                        payload=message.payload,
                    )
                except Exception as error:
                    await self._outbox_repository.mark_failed(message.id, str(error))
                    failed += 1
                else:
                    await self._outbox_repository.mark_published(
                        message.id,
                        datetime.now(UTC),
                    )
                    published += 1

        return PublishOutboxResult(published=published, failed=failed)
