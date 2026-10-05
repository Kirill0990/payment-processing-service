from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    """Настройки, загружаемые из переменных окружения и локального файла `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

    name: str = Field(default="Payment Processing Service")
    environment: Literal["local", "test", "production"] = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "payment"
    db_user: str = "payment"
    db_password: SecretStr = SecretStr("payment")

    @property
    def database_url(self) -> URL:
        """Собирает URL PostgreSQL из отдельных настроек подключения."""

        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
