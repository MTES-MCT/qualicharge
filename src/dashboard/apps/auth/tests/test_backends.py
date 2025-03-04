"""Dashboard auth backends tests."""

from apps.auth.backends import OIDCAuthenticationBackend


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
