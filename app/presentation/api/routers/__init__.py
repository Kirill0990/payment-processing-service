from fastapi import APIRouter, Depends

from app.presentation.api.dependencies import require_api_key
from app.presentation.api.routers.health import router as health_router
from app.presentation.api.routers.payments import router as payments_router


def build_api_router() -> APIRouter:
    """Собирает маршруты первой версии HTTP API."""

    router = APIRouter(dependencies=[Depends(require_api_key)])
    router.include_router(health_router)
    router.include_router(payments_router)
    return router


__all__ = ["build_api_router"]
