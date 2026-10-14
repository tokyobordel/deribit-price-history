
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deribit_base_url: str = "https://www.deribit.com/api/v2/"
    deribit_timeout: float = 10.0

    database_url: str
    test_database_url: str | None = None

    celery_broker_url: str = "redis://localhost:6380/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
