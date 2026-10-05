from app.application.dto import CreatePaymentCommand, PaymentDTO
from app.application.ports import PaymentRepository, UnitOfWork
from app.domain.entities import Payment


class CreatePayment:
    """Создаёт платёж и фиксирует изменения.

    Репозиторий и Unit of Work работают с одной транзакционной сессией.
    """

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        payment_repository: PaymentRepository,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._payment_repository = payment_repository

    async def execute(self, command: CreatePaymentCommand) -> PaymentDTO:
        """Выполняет сценарий с защитой от повторного ключа идемпотентности."""

        async with self._unit_of_work:
            existing_payment = await self._payment_repository.get_by_idempotency_key(
                command.idempotency_key
            )
            if existing_payment is not None:
                return PaymentDTO.from_entity(existing_payment)

            payment = Payment.create(
                amount=command.amount,
                currency=command.currency,
                idempotency_key=command.idempotency_key,
                webhook_url=command.webhook_url,
                description=command.description,
                metadata=command.metadata,
            )
            created = await self._payment_repository.add(payment)
            if not created:
                existing_payment = await self._payment_repository.get_by_idempotency_key(
                    command.idempotency_key
                )
                if existing_payment is None:
                    raise RuntimeError("Не удалось получить платёж после конфликта ключа")
                return PaymentDTO.from_entity(existing_payment)

        return PaymentDTO.from_entity(payment)
