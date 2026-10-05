from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from payment_service.infrastructure.config import Settings, get_settings
from payment_service.presentation.api.routers import build_api_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Manage resources shared for the entire application lifetime."""

    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the HTTP application."""

    app_settings = settings or get_settings()
    application = FastAPI(
        title=app_settings.name,
        debug=app_settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    application.include_router(
        build_api_router(),
        prefix=app_settings.api_v1_prefix,
    )
    return application
