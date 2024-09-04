"""QualiCharge API client settings."""

from typing import Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Client's global environment & configuration settings."""

    DEBUG: bool = False

    # Qualicharge server
    API_ROOT_URL: Optional[AnyHttpUrl] = None

    # API Credentials
    API_LOGIN_USERNAME: Optional[str] = None
    API_LOGIN_PASSWORD: Optional[str] = None

    # API usage
    API_BULK_CREATE_MAX_SIZE: int = 10
    GZIP_COMPRESSION_LEVEL: int = 9

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_nested_delimiter="__",
        env_prefix="QCC_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
