from typing import Annotated

from fastapi import Depends

from app.application.ports import PaymentRepository, UnitOfWork
from app.application.use_cases import CreatePayment, GetPayment
from app.presentation.api.dependencies.database import (
    get_payment_repository,
    get_unit_of_work,
)


def get_create_payment(
    unit_of_work: Annotated[UnitOfWork, Depends(get_unit_of_work)],
    payment_repository: Annotated[
        PaymentRepository,
        Depends(get_payment_repository),
    ],
) -> CreatePayment:
    """Собирает сценарий создания платежа."""

    return CreatePayment(unit_of_work, payment_repository)


def get_payment(
    payment_repository: Annotated[
        PaymentRepository,
        Depends(get_payment_repository),
    ],
) -> GetPayment:
    """Собирает сценарий получения платежа."""

    return GetPayment(payment_repository)
