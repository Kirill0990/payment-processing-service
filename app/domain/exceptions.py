class DomainError(Exception):
    """Базовая ошибка нарушения доменных правил."""


class InvalidPaymentAmountError(DomainError):
    """Сумма платежа не соответствует доменным ограничениям."""

    def __init__(self) -> None:
        super().__init__("Payment amount must be greater than zero")


class InvalidPaymentStateTransitionError(DomainError):
    """Запрошен недопустимый переход между статусами платежа."""

    def __init__(self, current_status: str, target_status: str) -> None:
        super().__init__(
            f"Payment cannot transition from {current_status!r} to {target_status!r}"
        )
