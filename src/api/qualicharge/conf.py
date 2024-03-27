"""QualiCharge API settings."""

from pathlib import Path
from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic model for QualiCharge's global environment & configuration settings."""

    DEBUG: bool = False

    # Security
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:8010",
    ]

    # API Core Root path
    # (used at least by everything that is alembic-configuration-related)
    ROOT_PATH: Path = Path(__file__).parent

    # Alembic
    ALEMBIC_CFG_PATH: Path = ROOT_PATH / "alembic.ini"

    # Database
    DB_ENGINE: str = "postgresql"
    DB_HOST: str = "postgresql"
    DB_NAME: str = "qualicharge-api"
    DB_USER: str = "qualicharge"
    DB_PASSWORD: str = "pass"
    DB_PORT: int = 5432
    TEST_DB_NAME: str = "test-qualicharge-api"

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL as required by SQLAlchemy."""
        return (
            f"{self.DB_ENGINE}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}/{self.DB_NAME}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def TEST_DATABASE_URL(self) -> str:
        """Get the database URL as required by SQLAlchemy."""
        return (
            f"{self.DB_ENGINE}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}/{self.TEST_DB_NAME}"
        )

    model_config = SettingsConfigDict(
        case_sensitive=True, env_nested_delimiter="__", env_prefix="QUALICHARGE_"
    )


settings = Settings()
