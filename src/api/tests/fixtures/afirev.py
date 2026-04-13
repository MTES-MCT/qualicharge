"""Afirev related fixtures."""

import pytest
from pydantic import HttpUrl
from sqlmodel import select

from qualicharge.afirev.client import AfirevClient
from qualicharge.afirev.models import AfirevPrefix, AfirevPrefixStatusEnum
from qualicharge.schemas.core import OperationalUnit


@pytest.fixture
def afirev_api_root_url():
    """Fake AFIREV API root URL."""
    yield "https://example.org/api/v1/"


@pytest.fixture
def afirev_api_prefixes_url(afirev_api_root_url):
    """Fake AFIREV API prefixes URL."""
    yield f"{afirev_api_root_url}prefixes"


@pytest.fixture
def afirev_client(afirev_api_root_url):
    """An Afirev client fixture."""
    yield AfirevClient(api_root_url=HttpUrl(afirev_api_root_url))


@pytest.fixture
def afirev_prefixes(db_session):
    """Generate Afirev prefixes API payload from database operational units."""
    prefixes = [
        AfirevPrefix.from_operational_unit(operational_unit)
        for operational_unit in db_session.exec(
            select(OperationalUnit).distinct()
        ).all()
    ]
    # Force prefixes to be active
    for prefix in prefixes:
        prefix.status = AfirevPrefixStatusEnum.ACTIVE
    yield prefixes
