"""ASGI-точка входа для локального запуска и production-окружения."""

from app.presentation.api.app import create_app

app = create_app()
