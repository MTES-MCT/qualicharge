"""QualiCharge Prefect indicators: settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic model for QualiCharge's global environment & configuration settings."""

    DATABASE_URL: PostgresDsn
    THREAD_POOL_MAX_WORKERS: int = 5
    WORK_POOL_NAME: str = "indicators"
    DEFAULT_CHUNK_SIZE: int = 100

    model_config = SettingsConfigDict(
        case_sensitive=True, env_nested_delimiter="__", env_prefix="QUALICHARGE_"
    )


settings = Settings()
