from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PaymentMessageCatalog:
    """Стабильные имена событий платежей."""

    created: str = "payment.created"


PAYMENT_MESSAGES = PaymentMessageCatalog()
