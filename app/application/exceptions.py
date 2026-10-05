from uuid import UUID


class ApplicationError(Exception):
    """Базовая ошибка сценариев приложения."""


class PaymentNotFoundError(ApplicationError):
    """Платёж с указанным идентификатором не найден."""

    def __init__(self, payment_id: UUID) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment {payment_id} was not found")
