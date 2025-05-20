"""Dashboard renewable configuration tests."""

import pytest


@pytest.fixture(autouse=True)
def set_language_code(settings):
    """Fixture to set LANGUAGE_CODE to 'en-us' by default for tests."""
    settings.LANGUAGE_CODE = "en-us"
