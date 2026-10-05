from enum import StrEnum


class Currency(StrEnum):
    """Поддерживаемые валюты платежа."""

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
