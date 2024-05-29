"""Fixtures for QualiCharge CLI."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    """CLI runner."""
    yield CliRunner()
