from uuid import UUID

from app.application.dto import PaymentDTO
from app.application.exceptions import PaymentNotFoundError
from app.application.ports import PaymentRepository


class GetPayment:
    """Возвращает платёж по его идентификатору."""

    def __init__(self, payment_repository: PaymentRepository) -> None:
        self._payment_repository = payment_repository

    async def execute(self, payment_id: UUID) -> PaymentDTO:
        """Выполняет поиск платежа или сообщает, что платёж не найден."""

        payment = await self._payment_repository.get_by_id(payment_id)

        if payment is None:
            raise PaymentNotFoundError(payment_id)
        return PaymentDTO.from_entity(payment)
