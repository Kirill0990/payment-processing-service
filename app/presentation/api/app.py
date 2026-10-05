import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from app.infrastructure.config import Settings, get_settings
from app.infrastructure.messaging import broker, payments_exchange, payments_queue
from app.infrastructure.messaging.outbox_worker import run_outbox_publisher
from app.presentation.api.exception_handlers import register_exception_handlers
from app.presentation.api.routers import build_api_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Управляет ресурсами, общими для всего времени жизни приложения."""

    await broker.connect()
    exchange = await broker.declare_exchange(payments_exchange)
    queue = await broker.declare_queue(payments_queue)
    await queue.bind(exchange=exchange, routing_key=payments_queue.routing_key)
    outbox_task = asyncio.create_task(run_outbox_publisher())
    try:
        yield
    finally:
        outbox_task.cancel()
        with suppress(asyncio.CancelledError):
            await outbox_task
        await broker.stop()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Создаёт и настраивает HTTP-приложение."""

    app_settings = settings or get_settings()
    application = FastAPI(
        title=app_settings.name,
        debug=app_settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.settings = app_settings
    register_exception_handlers(application)
    application.include_router(
        build_api_router(),
        prefix=app_settings.api_v1_prefix,
    )
    return application
