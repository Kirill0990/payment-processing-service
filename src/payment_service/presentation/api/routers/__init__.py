from fastapi import APIRouter

from payment_service.presentation.api.routers.health import router as health_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    return router


__all__ = ["build_api_router"]
