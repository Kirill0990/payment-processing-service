"""Адаптеры для доставки webhook-уведомлений."""

from app.infrastructure.webhook.http_sender import HttpWebhookSender

__all__ = ["HttpWebhookSender"]
