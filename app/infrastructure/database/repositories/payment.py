from uuid import UUID

from sqlalchemy import select
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

    async def add(self, payment: Payment) -> None:
        """Добавляет платёж и его события в текущую транзакцию."""

        self._session.add(self._to_model(payment))
        for event in payment.events:
            await self._outbox_repository.add(event)
        await self._session.flush()

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        return self._to_entity(model) if model is not None else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        statement = select(PaymentModel).where(
            PaymentModel.idempotency_key == idempotency_key
        )
        model = await self._session.scalar(statement)
        return self._to_entity(model) if model is not None else None

    @staticmethod
    def _to_model(payment: Payment) -> PaymentModel:
        return PaymentModel(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency.value,
            description=payment.description,
            metadata_=dict(payment.metadata),
            status=payment.status.value,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )

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
