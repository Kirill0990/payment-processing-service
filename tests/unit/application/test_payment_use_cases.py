import unittest
from decimal import Decimal
from types import TracebackType
from uuid import UUID, uuid4

from app.application.dto import CreatePaymentCommand
from app.application.exceptions import PaymentNotFoundError
from app.application.use_cases import CreatePayment, GetPayment
from app.domain.entities import Payment
from app.domain.enums import Currency, PaymentStatus


class FakePaymentRepository:
    def __init__(self) -> None:
        self.payments: dict[UUID, Payment] = {}

    async def add(self, payment: Payment) -> bool:
        self.payments[payment.id] = payment
        return True

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        return self.payments.get(payment_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        return next(
            (
                payment
                for payment in self.payments.values()
                if payment.idempotency_key == idempotency_key
            ),
            None,
        )


class ConcurrentConflictRepository(FakePaymentRepository):
    def __init__(self, existing_payment: Payment) -> None:
        super().__init__()
        self.existing_payment = existing_payment
        self.lookup_count = 0

    async def add(self, payment: Payment) -> bool:
        return False

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        self.lookup_count += 1
        return None if self.lookup_count == 1 else self.existing_payment


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
        if exc_value is not None:
            await self.rollback()
            return
        await self.commit()

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class PaymentUseCasesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.unit_of_work = FakeUnitOfWork()
        self.payment_repository = FakePaymentRepository()

    async def test_create_payment_and_commit_transaction(self) -> None:
        result = await self._create_payment().execute(self._command())

        self.assertEqual(result.status, PaymentStatus.PENDING)
        self.assertIn(result.id, self.payment_repository.payments)
        self.assertEqual(self.unit_of_work.commit_count, 1)

    async def test_return_existing_payment_for_same_idempotency_key(self) -> None:
        use_case = self._create_payment()

        first = await use_case.execute(self._command())
        second = await use_case.execute(self._command())

        self.assertEqual(second.id, first.id)
        self.assertEqual(len(self.payment_repository.payments), 1)
        self.assertEqual(self.unit_of_work.commit_count, 2)

    async def test_get_payment(self) -> None:
        created = await self._create_payment().execute(self._command())

        result = await GetPayment(self.payment_repository).execute(created.id)

        self.assertEqual(result, created)

    async def test_return_winner_of_concurrent_idempotency_conflict(self) -> None:
        existing_payment = Payment.create(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            idempotency_key="request-1",
            webhook_url="https://example.com/webhook",
        )
        repository = ConcurrentConflictRepository(existing_payment)

        result = await CreatePayment(self.unit_of_work, repository).execute(self._command())

        self.assertEqual(result.id, existing_payment.id)
        self.assertEqual(repository.lookup_count, 2)
        self.assertEqual(self.unit_of_work.commit_count, 1)

    async def test_get_missing_payment(self) -> None:
        payment_id = uuid4()

        with self.assertRaises(PaymentNotFoundError) as error:
            await GetPayment(self.payment_repository).execute(payment_id)

        self.assertEqual(error.exception.payment_id, payment_id)

    def _create_payment(self) -> CreatePayment:
        return CreatePayment(self.unit_of_work, self.payment_repository)

    @staticmethod
    def _command() -> CreatePaymentCommand:
        return CreatePaymentCommand(
            amount=Decimal("100.00"),
            currency=Currency.RUB,
            idempotency_key="request-1",
            webhook_url="https://example.com/webhook",
            description="Test payment",
            metadata={"order_id": "order-1"},
        )
