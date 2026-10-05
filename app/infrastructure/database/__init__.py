"""Адаптеры для работы с базой данных."""

from app.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

__all__ = ["SQLAlchemyUnitOfWork"]
