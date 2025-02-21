"""QualiCharge prefect indicators: types."""

from enum import StrEnum


class Environment(StrEnum):
    """Exhaustive list of supported environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
