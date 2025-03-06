"""Dashboard auth backends tests."""

from unittest.mock import patch

import pytest

from apps.auth.backends import OIDCAuthenticationBackend
from apps.auth.factories import UserFactory
from apps.core.factories import EntityFactory


def test_clean_siret_valid():
    """Test clean_siret with a valid SIRET."""
    backend = OIDCAuthenticationBackend()

    # Valid SIRET with correct format
    siret = backend.clean_siret("12345678901234")
    assert siret == "12345678901234"

    # Valid SIRET with an incorrect format that we can reformat
    siret = backend.clean_siret("1234 5678 901 234")
    assert siret == "12345678901234"


def test_clean_siret_invalid():
    """Test clean_siret with an invalid SIRET."""
    backend = OIDCAuthenticationBackend()

    # SIRET with wrong format
    siret = backend.clean_siret("invalid_siret")
    assert siret is None

    # Test with missing SIRET in claims.
    siret = backend.clean_siret(None)
    assert siret is None


@pytest.mark.django_db
@patch("apps.auth.backends.sync_entity_from_siret")
def test_create_entity_with_valid_siret(mocked):
    """Test create_entity with a valid SIRET and no user to attach."""
    backend = OIDCAuthenticationBackend()

    # create user
    user = UserFactory(siret="12345678901234")

    # mock sync_entity_from_siret()
    mocked.return_value = EntityFactory()

    # and finally test create_entity()
    backend.create_entity("12345678901234", user)

    # by default settings.PROCONNECT_ATTACH_USER_ON_CREATION = True,
    # so user must not be not attached to entity and so user=None
    mocked.assert_called_once_with("12345678901234", None)


@pytest.mark.django_db
@patch("apps.auth.backends.sync_entity_from_siret")
def test_create_entity_with_valid_siretand_attach_user(mocked, settings):
    """Test create_entity with a valid SIRET and user to attach."""
    backend = OIDCAuthenticationBackend()

    # user must be attached to entity
    settings.PROCONNECT_ATTACH_USER_ON_CREATION = True

    # create user
    user = UserFactory(siret="12345678901234")

    # mock sync_entity_from_siret()
    mocked.return_value = EntityFactory()

    # and finally test create_entity()
    backend.create_entity("12345678901234", user)
    mocked.assert_called_once_with("12345678901234", user)


@pytest.mark.django_db
@patch("apps.auth.backends.sync_entity_from_siret")
def test_create_entity_with_siret_exception(mocked):
    """Test create_entity when sync_entity_from_siret raises an exception."""
    backend = OIDCAuthenticationBackend()

    # create user
    user = UserFactory(siret="12345678901234")

    # sync_entity_from_siret raise an exception
    mocked.side_effect = Exception("Sync error")

    # and finally test create_entity()
    with patch("sentry_sdk.capture_exception") as mock_capture_exception:
        backend.create_entity("12345678901234", user)
        mocked.assert_called_once_with("12345678901234", None)
        mock_capture_exception.assert_called_once()
