"""QualiCharge API settings."""

import logging
from pathlib import Path
from typing import List, Optional

from passlib.context import CryptContext
from pydantic import AnyHttpUrl, HttpUrl, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configuration logger
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Pydantic model for QualiCharge's global environment & configuration settings."""

    DEBUG: bool = False

    # Security
    ALLOWED_HOSTS: List[str]

    # Middlewares
    GZIP_MIDDLEWARE_MINIMUM_SIZE: int = 1000
    GZIP_MIDDLEWARE_COMPRESSION_LEVEL: int = 5

    # API Core Root path
    # (used at least by everything that is alembic-configuration-related)
    ROOT_PATH: Path = Path(__file__).parent

    # Alembic
    ALEMBIC_CFG_PATH: Path = ROOT_PATH / "alembic.ini"

    # Database
    DB_ENGINE: str = "postgresql+psycopg"
    DB_ASYNC_ENGINE: str = "postgresql+asyncpg"
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: int = 5432
    DB_CONNECTION_POOL_SIZE: int = 5
    DB_CONNECTION_MAX_OVERFLOW: int = 10
    TEST_DB_NAME: str = "test-qualicharge-api"

    def _build_db_url(self, async_: bool = False) -> PostgresDsn:
        """A private method that build the database URL."""
        return PostgresDsn.build(
            scheme=self.DB_ASYNC_ENGINE if async_ else self.DB_ENGINE,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """Get the database URL as required by SQLAlchemy."""
        return self._build_db_url(async_=False)

    @computed_field  # type: ignore[misc]
    @property
    def ASYNC_DATABASE_URL(self) -> PostgresDsn:
        """Get the asynchronous database URL as required by SQLAlchemy."""
        return self._build_db_url(async_=True)

    @computed_field  # type: ignore[misc]
    @property
    def TEST_DATABASE_URL(self) -> PostgresDsn:
        """Get the database URL as required by SQLAlchemy."""
        return PostgresDsn.build(
            scheme=self.DB_ASYNC_ENGINE,
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.TEST_DB_NAME,
        )

    # OIDC
    OIDC_IS_ENABLED: bool = True  # If false, fallback to (local) OAuth2 scheme
    OIDC_PROVIDER_BASE_URL: AnyHttpUrl
    OIDC_PROVIDER_DISCOVER_TIMEOUT: int = 5
    OIDC_CONFIGURATION_PATH: Path = Path("/.well-known/openid-configuration")
    # FIXME: we should be more specific
    OIDC_EXPECTED_AUDIENCE: str = "account"

    # OAuth2 (local provider)
    OAUTH2_TOKEN_ALGORITHMS: list[str] = [
        "HS256",
    ]
    OAUTH2_TOKEN_ENCODING_KEY: str
    OAUTH2_TOKEN_ISSUER: AnyHttpUrl
    OAUTH2_TOKEN_LIFETIME: int = 30 * 60  # in seconds
    OAUTH2_TOKEN_URL: str = "/api/v1/auth/token"  # noqa: S105

    @computed_field  # type: ignore[misc]
    @property
    def OIDC_CONFIGURATION_URL(self) -> AnyHttpUrl:
        """Get the OIDC provider configuration URL."""
        if self.OIDC_PROVIDER_BASE_URL.host is None:
            logger.warning(
                "OIDC_PROVIDER_BASE_URL host is not defined. Defaulting to localhost."
            )
        host = self.OIDC_PROVIDER_BASE_URL.host or "localhost"

        return AnyHttpUrl.build(
            scheme=self.OIDC_PROVIDER_BASE_URL.scheme,
            host=host,
            port=self.OIDC_PROVIDER_BASE_URL.port,
            path=(self.OIDC_PROVIDER_BASE_URL.path or "")
            + f"/{self.OIDC_CONFIGURATION_PATH}",
        )

    # Security
    PASSWORD_HASHERS: list[str] = [
        "bcrypt",
    ]

    @computed_field  # type: ignore[misc]
    @property
    def PASSWORD_CONTEXT(self) -> CryptContext:
        """Get passlib CryptContext."""
        return CryptContext(schemes=self.PASSWORD_HASHERS, deprecated="auto")

    # Third-party integrations
    SENTRY_DSN: Optional[HttpUrl] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_PROFILES_SAMPLE_RATE: float = 1.0

    # Misc
    EXECUTION_ENVIRONMENT: str

    # API
    API_SESSION_BULK_CREATE_MAX_SIZE: int = 10
    API_STATIQUE_BULK_CREATE_MAX_SIZE: int = 10
    API_STATIQUE_PAGE_MAX_SIZE: int = 100
    API_STATIQUE_PAGE_SIZE: int = 10
    API_STATUS_BULK_CREATE_MAX_SIZE: int = 10
    API_GET_USER_CACHE_MAXSIZE: int = 256
    API_GET_USER_CACHE_TTL: int = 1800
    API_GET_USER_CACHE_INFO: bool = False
    API_GET_PDC_ID_CACHE_MAXSIZE: int = 5000
    API_GET_PDC_ID_CACHE_INFO: bool = False

    model_config = SettingsConfigDict(
        case_sensitive=True, env_nested_delimiter="__", env_prefix="QUALICHARGE_"
    )

    PROFILING: bool = False
    PROFILING_INTERVAL: float = 0.001


settings = Settings()
