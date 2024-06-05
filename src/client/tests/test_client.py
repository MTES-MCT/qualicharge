"""Tests for the qcc.client module."""

import pytest

from qcc.client import QCC
from qcc.endpoints.auth import Auth
from qcc.endpoints.static import Static
from qcc.exceptions import ConfigurationError
from qcc.http import HTTPClient


def test_client_initialization():
    """Test QCC client initialization."""
    with pytest.raises(
        ConfigurationError, match="API credentials are not set in client nor settings"
    ):
        QCC(username=None, password=None, api_root_url=None)
    with pytest.raises(
        ConfigurationError, match="API credentials are not set in client nor settings"
    ):
        QCC(username="", password="", api_root_url="")
    with pytest.raises(
        ConfigurationError, match="API credentials are not set in client nor settings"
    ):
        QCC(username="foo", password="foo", api_root_url="")  # noqa: S106
    with pytest.raises(
        ConfigurationError, match="API credentials are not set in client nor settings"
    ):
        QCC(username="foo", password=None, api_root_url=None)

    qcc = QCC(username="foo", password="pass", api_root_url="http://fake")  # noqa: S106
    assert isinstance(qcc.client, HTTPClient)
    assert isinstance(qcc.auth, Auth)
    assert qcc.auth.client == qcc.client
    assert isinstance(qcc.static, Static)
    assert qcc.static.client == qcc.client
