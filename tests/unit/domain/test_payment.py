import unittest
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.entities import Payment
from app.domain.enums import Currency, PaymentStatus
from app.domain.exceptions import (
    InvalidPaymentAmountError,
    InvalidPaymentStateTransitionError,
)
from app.domain.events import PaymentCreated


class PaymentTestCase(unittest.TestCase):
    def test_create_pending_payment(self) -> None:
        metadata = {"order_id": "order-1"}

        payment = Payment.create(
            amount=Decimal("125.50"),
            currency=Currency.RUB,
            idempotency_key="request-1",
            webhook_url="https://example.com/webhooks/payments",
            metadata=metadata,
        )

        metadata["order_id"] = "changed"
        self.assertEqual(payment.status, PaymentStatus.PENDING)
        self.assertEqual(payment.metadata, {"order_id": "order-1"})
        self.assertIsNone(payment.processed_at)
        self.assertEqual(len(payment.events), 1)
        self.assertIsInstance(payment.events[0], PaymentCreated)

    def test_reject_non_positive_amount(self) -> None:
        with self.assertRaises(InvalidPaymentAmountError):
            Payment.create(
                amount=Decimal("0"),
                currency=Currency.USD,
                idempotency_key="request-1",
                webhook_url="https://example.com/webhook",
            )

    def test_mark_payment_succeeded(self) -> None:
        payment = self._payment()
        processed_at = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)

        payment.mark_succeeded(processed_at=processed_at)

        self.assertEqual(payment.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(payment.processed_at, processed_at)

    def test_terminal_payment_cannot_be_processed_twice(self) -> None:
        payment = self._payment()
        payment.mark_failed()

        with self.assertRaises(InvalidPaymentStateTransitionError):
            payment.mark_succeeded()

    @staticmethod
    def _payment() -> Payment:
        return Payment.create(
            amount=Decimal("10.00"),
            currency=Currency.EUR,
            idempotency_key="request-1",
            webhook_url="https://example.com/webhook",
        )
