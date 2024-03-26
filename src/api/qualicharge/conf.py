"""QualiCharge API settings."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic model for QualiCharge's global environment & configuration settings."""

    DEBUG: bool = False

    # Security
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:8010",
    ]

    model_config = SettingsConfigDict(
        case_sensitive=True, env_nested_delimiter="__", env_prefix="QUALICHARGE_"
    )


settings = Settings()
