import asyncio
import random

from app.application.ports import PaymentProcessor
from app.domain.entities import Payment


class SimulatedPaymentProcessor(PaymentProcessor):
    """Эмулирует внешний платёжный шлюз."""

    async def process(self, payment: Payment) -> bool:
        await asyncio.sleep(random.randint(2, 5))
        return random.random() < 0.9
