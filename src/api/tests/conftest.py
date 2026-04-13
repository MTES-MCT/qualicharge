"""Fixtures for pytest."""

# ruff: noqa: F401

from qualicharge.auth.factories import IDTokenFactory

from .fixtures.afirev import (
    afirev_api_prefixes_url,
    afirev_api_root_url,
    afirev_client,
    afirev_prefixes,
)
from .fixtures.app import clear_lru_cache, client, client_auth
from .fixtures.cli import runner
from .fixtures.db import (
    db_engine,
    db_session,
    load_operational_units,
    override_db_test_session,
    versioning_manager,
)
