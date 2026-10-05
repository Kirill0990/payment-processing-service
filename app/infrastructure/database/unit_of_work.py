from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import UnitOfWork


class SQLAlchemyUnitOfWork(UnitOfWork):
    """Управляет транзакцией существующей SQLAlchemy-сессии."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
            return
        await self.commit()

    async def commit(self) -> None:
        """Фиксирует текущую транзакцию."""

        await self._session.commit()

    async def rollback(self) -> None:
        """Откатывает текущую транзакцию."""

        await self._session.rollback()
