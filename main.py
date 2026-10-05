"""ASGI entry point for local development and production."""

from payment_service.presentation.api.app import create_app

app = create_app()
