"""
Конфигурация приложения.

Загружает настройки из переменных окружения.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения."""

    # Telegram Bot
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_mini_app_url: str = Field("", env="TELEGRAM_MINI_APP_URL")

    # Database
    postgres_host: str = Field("localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_db: str = Field("ozon_bot", env="POSTGRES_DB")
    postgres_user: str = Field("postgres", env="POSTGRES_USER")
    postgres_password: str = Field("", env="POSTGRES_PASSWORD")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    encryption_key: str = Field(..., env="ENCRYPTION_KEY")

    # API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")

    # Environment
    env: str = Field("development", env="ENV")
    debug: bool = Field(True, env="DEBUG")

    # Sentry
    sentry_dsn: str = Field("", env="SENTRY_DSN")

    @property
    def database_url(self) -> str:
        """Получить URL для подключения к PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Получить URL для подключения к Redis."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = Settings()
