import unittest
from decimal import Decimal
from types import TracebackType
from uuid import UUID, uuid4

from app.application.exceptions import PaymentNotFoundError
from app.application.use_cases import ProcessPayment
from app.domain.entities import Payment
from app.domain.enums import Currency, PaymentStatus


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commit_count = 0

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit_count += 1

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        pass


class FakePaymentRepository:
    def __init__(self, payment: Payment | None, *, save_result: bool = True) -> None:
        self.payment = payment
        self.save_result = save_result
        self.saved: list[Payment] = []

    async def add(self, payment: Payment) -> bool:
        self.payment = payment
        return True

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        return self.payment if self.payment is not None and self.payment.id == payment_id else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        return None

    async def save_processed(self, payment: Payment) -> bool:
        self.saved.append(payment)
        return self.save_result


class FakePaymentProcessor:
    def __init__(self, result: bool) -> None:
        self.result = result
        self.calls = 0

    async def process(self, payment: Payment) -> bool:
        self.calls += 1
        return self.result


class FakeWebhookSender:
    def __init__(self) -> None:
        self.payments: list[Payment] = []

    async def send(self, payment: Payment) -> None:
        self.payments.append(payment)


class ProcessPaymentTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_process_pending_payment_and_send_webhook(self) -> None:
        payment = self._payment()
        repository = FakePaymentRepository(payment)
        processor = FakePaymentProcessor(result=True)
        webhook = FakeWebhookSender()
        unit_of_work = FakeUnitOfWork()

        result = await ProcessPayment(
            unit_of_work,
            repository,
            processor,
            webhook,
        ).execute(payment.id)

        self.assertEqual(result.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(processor.calls, 1)
        self.assertEqual(repository.saved, [payment])
        self.assertEqual(webhook.payments, [payment])
        self.assertEqual(unit_of_work.commit_count, 1)

    async def test_do_not_process_terminal_payment_twice(self) -> None:
        payment = self._payment()
        payment.mark_failed()
        repository = FakePaymentRepository(payment)
        processor = FakePaymentProcessor(result=True)
        webhook = FakeWebhookSender()

        result = await ProcessPayment(
            FakeUnitOfWork(),
            repository,
            processor,
            webhook,
        ).execute(payment.id)

        self.assertEqual(result.status, PaymentStatus.FAILED)
        self.assertEqual(processor.calls, 0)
        self.assertEqual(repository.saved, [])
        self.assertEqual(webhook.payments, [payment])

    async def test_raise_when_payment_does_not_exist(self) -> None:
        payment_id = uuid4()

        with self.assertRaises(PaymentNotFoundError):
            await ProcessPayment(
                FakeUnitOfWork(),
                FakePaymentRepository(None),
                FakePaymentProcessor(result=True),
                FakeWebhookSender(),
            ).execute(payment_id)

    @staticmethod
    def _payment() -> Payment:
        return Payment.create(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            idempotency_key="request-1",
            webhook_url="https://example.com/webhook",
        )
