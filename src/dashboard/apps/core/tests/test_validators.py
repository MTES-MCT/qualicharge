"""Dashboard core validators tests."""

import pytest
from django.core.exceptions import ValidationError

from apps.core.validators import (
    validate_naf_code,
    validate_siren,
    validate_siret,
    validate_zip_code,
)


@pytest.mark.parametrize("value", ["12345678901234", "00000000000000", None])
def test_validate_siret_valid(value):
    """Tests that a valid SIRET does not raise an exception."""
    assert validate_siret(value) is None


@pytest.mark.parametrize(
    "value",
    [
        "1234567890123",  # Too short
        "123456789012345",  # Too long
        "1234ABC8901234",  # Contains non-numeric characters
        1234,  # Number
        "",  # Empty string
        " " * 14,  # Only spaces
    ],
)
def test_validate_siret_invalid(value):
    """Tests that an invalid SIRET raises a ValidationError."""
    with pytest.raises(ValidationError):
        validate_siret(value)


@pytest.mark.parametrize("value", ["1234A", "0001Z", "9876B", "0000Z", None])
def test_validate_naf_code_valid(value):
    """Test that valid NAF codes does not raise an exception."""
    assert validate_naf_code(value) is None


@pytest.mark.parametrize(
    "value",
    [
        "12345",
        "12345Z",
        "123A",
        "12A45",
        "ABC1Z",
        "1234!",
        "abcdA",
        "1234a",
        "1234",
        "",
        12345,
    ],
)
def test_validate_naf_code_invalid(value):
    """Test that invalid NAF codes raise a ValidationError."""
    with pytest.raises(ValidationError):
        validate_naf_code(value)


@pytest.mark.parametrize("value", ["12345", "98765", "00000", "978", None])
def test_validate_zip_code_valid(value):
    """Tests validation of valid zip codes  does not raise an exception."""
    assert validate_zip_code(value) is None


@pytest.mark.parametrize("value", ["123456", "12a45", "abcde", "", " ", 12345])
def test_validate_zip_code_invalid(value):
    """Tests validation of invalid zip codes raise a ValidationError."""
    with pytest.raises(ValidationError):
        validate_zip_code(value)


@pytest.mark.parametrize("value", ["123456789", "000000000", None])
def test_validate_siren_valid(value):
    """Tests that a valid SIREN does not raise an exception."""
    assert validate_siren(value) is None


@pytest.mark.parametrize(
    "value",
    [
        "1234",  # Too short
        "123456789012345",  # Too long
        "1234ABC89",  # Contains non-numeric characters
        1234,  # Number
        "",  # Empty string
        " " * 9,  # Only spaces
    ],
)
def test_validate_siren_invalid(value):
    """Tests that an invalid SIREN raises a ValidationError."""
    with pytest.raises(ValidationError):
        validate_siren(value)
