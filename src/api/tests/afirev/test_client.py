"""Tests for QualiCharge Afirev client."""

import httpx
import pytest
from pydantic import HttpUrl

from qualicharge.afirev.client import AfirevClient, AfirevClientException
from qualicharge.afirev.models import AfirevPrefix


def test_client_init():
    """Test the AfirevClient instantiation."""
    base_url = "https://example.org/api/v1/"
    afirev = AfirevClient(api_root_url=HttpUrl(base_url))
    assert isinstance(afirev.client, httpx.Client)
    assert afirev.client.base_url == base_url


def test_client_prefixes_invalid_response(
    httpx_mock, afirev_client, afirev_api_prefixes_url
):
    """Test the AfirevClient `prefixes` method whith an invalid response."""
    httpx_mock.add_response(url=httpx.URL(afirev_api_prefixes_url), json=[])
    with pytest.raises(
        AfirevClientException, match="Invalid AFIREV API response format."
    ):
        afirev_client.prefixes()


def test_client_prefixes_invalid_status(
    httpx_mock, afirev_client, afirev_api_prefixes_url
):
    """Test the AfirevClient `prefixes` method whith an invalid status."""
    httpx_mock.add_response(url=httpx.URL(afirev_api_prefixes_url), status_code=404)
    with pytest.raises(
        AfirevClientException,
        match=r"Invalid AFIREV API response status \(code: 404\).",
    ):
        afirev_client.prefixes()


def test_client_prefixes(httpx_mock, afirev_client, afirev_api_prefixes_url):
    """Test the AfirevClient `prefixes` method."""
    # Empty response
    httpx_mock.add_response(
        url=httpx.URL(afirev_api_prefixes_url), json={"data": [], "total": 0}
    )
    prefixes = afirev_client.prefixes()
    assert prefixes == []

    # Valid example response
    size = 2
    httpx_mock.add_response(
        url=httpx.URL(afirev_api_prefixes_url),
        json={
            "data": [
                {
                    "prefixId": "FRFOO",
                    "name": "Foo",
                    "amenageurName": "Foo Inc.",
                    "exploitantName": "Bar Inc.",
                    "type": "CHARGE",
                    "status": "ACTIVE",
                },
                {
                    "prefixId": "FRBOO",
                    "name": "Boo",
                    "amenageurName": "Boo Inc.",
                    "exploitantName": "Bar Inc.",
                    "type": "MOBILITY",
                    "status": "INACTIVE",
                },
            ],
            "total": size,
        },
    )
    prefixes = afirev_client.prefixes()
    assert len(prefixes) == size
    assert prefixes[0] == AfirevPrefix(
        prefixId="FRFOO",
        name="Foo",
        amenageurName="Foo Inc.",
        exploitantName="Bar Inc.",
        type="CHARGE",
        status="ACTIVE",
    )
    assert prefixes[1] == AfirevPrefix(
        prefixId="FRBOO",
        name="Boo",
        amenageurName="Boo Inc.",
        exploitantName="Bar Inc.",
        type="MOBILITY",
        status="INACTIVE",
    )
