"""Точка входа consumer платежей."""

import asyncio
from uuid import UUID

from faststream import FastStream
from faststream.exceptions import RejectMessage
from pydantic import BaseModel

from app.application.use_cases import ProcessPayment
from app.infrastructure.database.repositories import (
    SQLAlchemyOutboxRepository,
    SQLAlchemyPaymentRepository,
)
from app.infrastructure.database.session import session_factory
from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.messaging import (
    broker,
    dead_letter_exchange,
    dead_letter_queue,
    payments_exchange,
    payments_queue,
)
from app.infrastructure.payment_gateway import SimulatedPaymentProcessor
from app.infrastructure.webhook import HttpWebhookSender

app = FastStream(broker)


class PaymentCreatedMessage(BaseModel):
    """Сообщение о созданном платеже."""

    payment_id: UUID


@app.after_startup
async def declare_dead_letter_queue() -> None:
    """Создаёт и связывает exchange и очередь для окончательно упавших сообщений."""

    exchange = await broker.declare_exchange(dead_letter_exchange)
    queue = await broker.declare_queue(dead_letter_queue)
    await queue.bind(
        exchange=exchange,
        routing_key=dead_letter_queue.routing_key,
    )


@broker.subscriber(payments_queue, payments_exchange)
async def process_payment(message: PaymentCreatedMessage) -> None:
    """Обрабатывает сообщение с тремя попытками и экспоненциальной задержкой."""

    for attempt in range(3):
        try:
            async with session_factory() as session:
                outbox_repository = SQLAlchemyOutboxRepository(session)
                payment_repository = SQLAlchemyPaymentRepository(
                    session,
                    outbox_repository,
                )
                use_case = ProcessPayment(
                    SQLAlchemyUnitOfWork(session),
                    payment_repository,
                    SimulatedPaymentProcessor(),
                    HttpWebhookSender(),
                )
                await use_case.execute(message.payment_id)
            return
        except Exception as error:
            if attempt == 2:
                raise RejectMessage from error
            await asyncio.sleep(2**attempt)
