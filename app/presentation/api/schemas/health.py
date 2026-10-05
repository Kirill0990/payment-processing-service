from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Ответ проверки доступности HTTP-приложения."""

    status: Literal["ok"]
