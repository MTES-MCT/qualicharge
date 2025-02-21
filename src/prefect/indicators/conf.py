"""QualiCharge Prefect indicators: settings."""

import logging
from typing import Dict, List

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from .types import Environment

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Pydantic model for QualiCharge's global environment & configuration settings."""

    # Databases
    API_DATABASE_URLS: Dict[Environment, PostgresDsn]
    API_ACTIVE_ENVIRONMENTS: List[Environment] = [
        Environment.STAGING,
        Environment.PRODUCTION,
    ]
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
