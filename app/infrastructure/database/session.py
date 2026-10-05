from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.infrastructure.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url)
session_factory = async_sessionmaker(engine)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Предоставляет одну SQLAlchemy-сессию на время обработки запроса."""

    async with session_factory() as session:
        yield session
