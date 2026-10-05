"""Зависимости FastAPI."""

from app.presentation.api.dependencies.auth import require_api_key
from app.presentation.api.dependencies.payment import get_create_payment, get_payment

__all__ = ["get_create_payment", "get_payment", "require_api_key"]
