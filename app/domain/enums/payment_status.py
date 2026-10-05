from enum import StrEnum


class PaymentStatus(StrEnum):
    """Состояние обработки платежа."""

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
