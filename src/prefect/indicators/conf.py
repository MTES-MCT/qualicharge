"""QualiCharge Prefect indicators: settings."""

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic model for QualiCharge's global environment & configuration settings."""

    # Databases
    API_DATABASE_URL: PostgresDsn
    INDICATORS_DATABASE_URL: PostgresDsn
    DB_CONNECTION_POOL_SIZE: int = 5
    DB_CONNECTION_MAX_OVERFLOW: int = 10

    # Workers
    THREAD_POOL_MAX_WORKERS: int = 5
    WORK_POOL_NAME: str = "indicators"

    # Tasks
    DEFAULT_CHUNK_SIZE: int = 100

    # Misc
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        case_sensitive=True, env_nested_delimiter="__", env_prefix="QUALICHARGE_"
    )


settings = Settings()
