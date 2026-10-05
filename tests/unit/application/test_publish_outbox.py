import unittest
from datetime import UTC, datetime
from types import TracebackType
from typing import Any
from uuid import UUID, uuid4

from app.application.dto import OutboxMessage
from app.application.use_cases import PublishOutbox
from app.domain.events import DomainEvent


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback_count += 1
            return
        self.commit_count += 1

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class FakeOutboxRepository:
    def __init__(self, messages: list[OutboxMessage]) -> None:
        self.messages = messages
        self.requested_limit: int | None = None
        self.published: list[UUID] = []
        self.failed: dict[UUID, str] = {}

    async def add(self, event: DomainEvent) -> None:
        raise NotImplementedError

    async def get_pending(self, limit: int) -> list[OutboxMessage]:
        self.requested_limit = limit
        return self.messages[:limit]

    async def mark_published(self, message_id: UUID, published_at: datetime) -> None:
        self.published.append(message_id)

    async def mark_failed(self, message_id: UUID, error: str) -> None:
        self.failed[message_id] = error


class FakeEventPublisher:
    def __init__(self, failed_message_ids: set[UUID] | None = None) -> None:
        self.failed_message_ids = failed_message_ids or set()
        self.published: list[UUID] = []

    async def publish(
        self,
        *,
        message_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if message_id in self.failed_message_ids:
            raise RuntimeError("RabbitMQ недоступен")
        self.published.append(message_id)


class PublishOutboxTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_publish_pending_messages(self) -> None:
        messages = [self._message(), self._message()]
        unit_of_work = FakeUnitOfWork()
        repository = FakeOutboxRepository(messages)
        publisher = FakeEventPublisher()

        result = await PublishOutbox(unit_of_work, repository, publisher).execute(limit=10)

        self.assertEqual(result.published, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual(repository.published, [message.id for message in messages])
        self.assertEqual(unit_of_work.commit_count, 1)
        self.assertEqual(repository.requested_limit, 10)

    async def test_record_publication_error_and_continue_batch(self) -> None:
        failed_message = self._message()
        successful_message = self._message()
        unit_of_work = FakeUnitOfWork()
        repository = FakeOutboxRepository([failed_message, successful_message])
        publisher = FakeEventPublisher({failed_message.id})

        result = await PublishOutbox(unit_of_work, repository, publisher).execute()

        self.assertEqual(result.published, 1)
        self.assertEqual(result.failed, 1)
        self.assertEqual(repository.failed[failed_message.id], "RabbitMQ недоступен")
        self.assertEqual(repository.published, [successful_message.id])
        self.assertEqual(unit_of_work.commit_count, 1)

    async def test_empty_outbox_still_closes_transaction(self) -> None:
        unit_of_work = FakeUnitOfWork()
        repository = FakeOutboxRepository([])

        result = await PublishOutbox(
            unit_of_work,
            repository,
            FakeEventPublisher(),
        ).execute()

        self.assertEqual(result.published, 0)
        self.assertEqual(result.failed, 0)
        self.assertEqual(unit_of_work.commit_count, 1)

    @staticmethod
    def _message() -> OutboxMessage:
        message_id = uuid4()
        return OutboxMessage(
            id=message_id,
            event_type="payment.created",
            payload={"payment_id": str(uuid4())},
            created_at=datetime.now(UTC),
            attempts=0,
        )
