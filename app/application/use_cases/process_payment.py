from uuid import UUID

from app.application.dto import PaymentDTO
from app.application.exceptions import PaymentNotFoundError
from app.application.ports import (
    PaymentProcessor,
    PaymentRepository,
    UnitOfWork,
    WebhookSender,
)
from app.domain.enums import PaymentStatus


class ProcessPayment:
    """Обрабатывает платёж и уведомляет клиента о результате."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        payment_repository: PaymentRepository,
        payment_processor: PaymentProcessor,
        webhook_sender: WebhookSender,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._payment_repository = payment_repository
        self._payment_processor = payment_processor
        self._webhook_sender = webhook_sender

    async def execute(self, payment_id: UUID) -> PaymentDTO:
        """Выполняет процессинг не более одного раза и отправляет webhook."""

        payment = await self._payment_repository.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(payment_id)

        if payment.status is PaymentStatus.PENDING:
            succeeded = await self._payment_processor.process(payment)
            if succeeded:
                payment.mark_succeeded()
            else:
                payment.mark_failed()

            async with self._unit_of_work:
                saved = await self._payment_repository.save_processed(payment)
            if not saved:
                current_payment = await self._payment_repository.get_by_id(payment_id)
                if current_payment is None:
                    raise PaymentNotFoundError(payment_id)
                payment = current_payment

        await self._webhook_sender.send(payment)
        return PaymentDTO.from_entity(payment)
