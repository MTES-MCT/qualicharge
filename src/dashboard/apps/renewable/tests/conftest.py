"""Dashboard renewable configuration tests."""

import pytest


@pytest.fixture(autouse=True)
def set_language_code(settings):
    """Fixture to set LANGUAGE_CODE to 'en-us' by default for tests."""
    settings.LANGUAGE_CODE = "en-us"


@pytest.fixture()
def disable_session_expiration(settings):
    """Disable session lifetime during testing.

    Since we often mock now() in tests, using it together with SESSION_COOKIE_AGE causes
    the session to expire prematurely. Therefore, we assign it a long lifetime.
    """
    settings.SESSION_COOKIE_AGE = 999999999  # very very long lifespan
