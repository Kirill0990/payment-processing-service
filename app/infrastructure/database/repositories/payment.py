from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import OutboxRepository, PaymentRepository
from app.domain.entities import Payment
from app.domain.enums import Currency, PaymentStatus
from app.infrastructure.database.models import PaymentModel


class SQLAlchemyPaymentRepository(PaymentRepository):
    """Хранилище платежей на основе асинхронной SQLAlchemy-сессии."""

    def __init__(
        self,
        session: AsyncSession,
        outbox_repository: OutboxRepository,
    ) -> None:
        self._session = session
        self._outbox_repository = outbox_repository

    async def add(self, payment: Payment) -> bool:
        """Добавляет платёж и его события в текущую транзакцию."""

        values = self._to_values(payment)
        statement = (
            insert(PaymentModel)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[PaymentModel.idempotency_key])
            .returning(PaymentModel.id)
        )
        inserted_id = await self._session.scalar(statement)
        if inserted_id is None:
            return False

        for event in payment.events:
            await self._outbox_repository.add(event)
        await self._session.flush()
        return True

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        return self._to_entity(model) if model is not None else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        statement = select(PaymentModel).where(
            PaymentModel.idempotency_key == idempotency_key
        )
        model = await self._session.scalar(statement)
        return self._to_entity(model) if model is not None else None

    async def save_processed(self, payment: Payment) -> bool:
        """Сохраняет результат, только если платёж ещё ожидает обработки."""

        statement = (
            update(PaymentModel)
            .where(
                PaymentModel.id == payment.id,
                PaymentModel.status == PaymentStatus.PENDING.value,
            )
            .values(
                status=payment.status.value,
                processed_at=payment.processed_at,
            )
        )
        result = cast(CursorResult[Any], await self._session.execute(statement))
        return result.rowcount == 1

    @staticmethod
    def _to_values(payment: Payment) -> dict[str, object]:
        return {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency.value,
            "description": payment.description,
            "metadata_": dict(payment.metadata),
            "status": payment.status.value,
            "idempotency_key": payment.idempotency_key,
            "webhook_url": payment.webhook_url,
            "created_at": payment.created_at,
            "processed_at": payment.processed_at,
        }

    @staticmethod
    def _to_entity(model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            amount=model.amount,
            currency=Currency(model.currency),
            description=model.description,
            metadata=dict(model.metadata_),
            status=PaymentStatus(model.status),
            idempotency_key=model.idempotency_key,
            webhook_url=model.webhook_url,
            created_at=model.created_at,
            processed_at=model.processed_at,
        )
