from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import PaymentRepository, UnitOfWork
from app.infrastructure.database.repositories import (
    SQLAlchemyOutboxRepository,
    SQLAlchemyPaymentRepository,
)
from app.infrastructure.database.session import get_session
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


def get_payment_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PaymentRepository:
    """Создаёт репозиторий платежей в текущей SQLAlchemy-сессии."""

    outbox_repository = SQLAlchemyOutboxRepository(session)
    return SQLAlchemyPaymentRepository(session, outbox_repository)


def get_unit_of_work(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UnitOfWork:
    """Создаёт Unit of Work в текущей SQLAlchemy-сессии."""

    return SQLAlchemyUnitOfWork(session)
