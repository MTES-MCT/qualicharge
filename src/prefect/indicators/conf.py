"""QualiCharge Prefect indicators: settings."""

import logging
from enum import Enum

from prefect.context import FlowRunContext
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


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


class Staging(Settings):
    """Settings for the API staging environment."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_nested_delimiter="__",
        env_prefix="QUALICHARGE_STAGING_",
    )


class Production(Settings):
    """Settings for the API production environment."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_nested_delimiter="__",
        env_prefix="QUALICHARGE_PRODUCTION_",
    )


class APIEnvironment(Enum):
    """Environments enum."""

    STAGING = Staging
    PRODUCTION = Production


def activate() -> Settings:
    """Activate settings for a particular environment."""
    context = FlowRunContext.get()
    env_name = None
    if context is not None:
        print(f"{context.parameters=}")
    # env_name = context["parameters"].get("environment", None)
    # env_name = FlowRunContext.get("environment")
    logger.info("Will activate settings for the target environment: '%s' …", env_name)

    if env_name is None:
        return Settings()
    try:
        api_env = APIEnvironment.__getitem__(env_name.upper())
    except KeyError as e:
        raise Exception("Target environment '%s' is not defined", env_name) from e
    return api_env.value()
