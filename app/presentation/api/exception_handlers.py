from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.exceptions import PaymentNotFoundError
from app.domain.exceptions import DomainError


def register_exception_handlers(application: FastAPI) -> None:
    """Регистрирует преобразование ошибок приложения в HTTP-ответы."""

    @application.exception_handler(PaymentNotFoundError)
    async def payment_not_found(
        _: Request,
        error: PaymentNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(error)},
        )

    @application.exception_handler(DomainError)
    async def domain_error(_: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(error)},
        )
