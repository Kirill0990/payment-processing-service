from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.config import Settings, get_settings
from app.presentation.api.exception_handlers import register_exception_handlers
from app.presentation.api.routers import build_api_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Управляет ресурсами, общими для всего времени жизни приложения."""

    yield


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
