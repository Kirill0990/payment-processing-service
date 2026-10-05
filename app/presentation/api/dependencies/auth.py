from secrets import compare_digest
from typing import Annotated

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.infrastructure.config import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    request: Request,
    provided_api_key: Annotated[str | None, Security(api_key_header)],
) -> None:
    """Проверяет статический API-ключ из HTTP-заголовка."""

    settings: Settings = request.app.state.settings
    expected_api_key = settings.api_key.get_secret_value()
    if provided_api_key is None or not compare_digest(provided_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный API-ключ",
        )
