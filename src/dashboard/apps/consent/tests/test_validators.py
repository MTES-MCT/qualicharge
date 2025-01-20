"""Dashboard consent validators tests."""

import pytest
from django.core.exceptions import ValidationError

from apps.consent.validators import (
    validate_company_schema,
    validate_control_authority_schema,
    validate_representative_schema,
)

VALID_COMPANY_DATA = {
    "company_type": "SARL",
    "name": "My Company",
    "legal_form": "SARL",
    "trade_name": "The test company",
    "siret": "12345678901234",
    "naf": "1234A",
    "address": {
        "line_1": "1 rue Exemple",
        "line_2": None,
        "zip_code": "75000",
        "city": "Paris",
    },
}

VALID_REPRESENTATIVE_DATA = {
    "firstname": "Alice",
    "lastname": "Brown",
    "email": "alice.brown@example.com",
    "phone": "9876543210",
}

VALID_CONTROL_AUTHORITY_DATA = {
    "name": "QualiCharge",
    "represented_by": "John Doe",
    "email": "mail@test.com",
    "address": {
        "line_1": "1 Rue Exemple",
        "line_2": None,
        "zip_code": "75000",
        "city": "Paris",
    },
}


@pytest.mark.parametrize("value", ["12345678901234", "00000000000000", None])
def test_validate_company_siret_valid(value):
    """Tests that a valid SIRET does not raise an exception."""
    valid_data = VALID_COMPANY_DATA
    valid_data["siret"] = value
    assert validate_company_schema(valid_data) is None


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
def test_validate_company_siret_invalid(value):
    """Tests that an invalid SIRET raises a ValidationError."""
    invalid_data = VALID_COMPANY_DATA
    invalid_data["siret"] = value
    with pytest.raises(ValidationError):
        assert validate_company_schema(invalid_data) is None
    # reset with valid siret
    VALID_COMPANY_DATA["siret"] = "12345678901234"


@pytest.mark.parametrize("value", ["1234A", "0001Z", "9876B", "0000Z", None])
def test_validate_company_naf_code_valid(value):
    """Test that valid NAF codes does not raise an exception."""
    valid_data = VALID_COMPANY_DATA
    valid_data["naf"] = value
    assert validate_company_schema(valid_data) is None


@pytest.mark.parametrize(
    "value",
    [
        "12345",
        "12345Z",
        "123A",
        "12A45",
        "1245a",
        "ABC1Z",
        "1234!",
        "abcdA",
        "1234",
        "",
        12345,
    ],
)
def test_validate_compnay_naf_code_invalid(value):
    """Test that invalid NAF codes raise a ValidationError."""
    invalid_data = VALID_COMPANY_DATA
    invalid_data["naf"] = value
    with pytest.raises(ValidationError):
        validate_company_schema(invalid_data)
    # reset with valid naf
    VALID_COMPANY_DATA["naf"] = "1234A"


@pytest.mark.parametrize("value", ["12345", "98765", "00000", "978", None])
def test_validate_zip_code_valid(value):
    """Tests validation of valid zip codes  does not raise an exception."""
    valid_company_data = VALID_COMPANY_DATA
    valid_company_data["address"]["zip_code"] = value
    assert validate_company_schema(valid_company_data) is None

    valid_authority_data = VALID_CONTROL_AUTHORITY_DATA
    valid_authority_data["address"]["zip_code"] = value
    assert validate_control_authority_schema(valid_authority_data) is None


@pytest.mark.parametrize("value", ["123456", "12a45", "abcde", "", " ", 12345])
def test_validate_zip_code_invalid(value):
    """Tests validation of invalid zip codes raise a ValidationError."""
    valid_company_data = VALID_COMPANY_DATA
    valid_company_data["address"]["zip_code"] = value
    with pytest.raises(ValidationError):
        validate_company_schema(valid_company_data)
    # reset with valid zip
    VALID_COMPANY_DATA["address"]["zip_code"] = "12345"

    valid_authority_data = VALID_CONTROL_AUTHORITY_DATA
    valid_authority_data["address"]["zip_code"] = value
    with pytest.raises(ValidationError):
        validate_control_authority_schema(valid_authority_data)
    # reset with valid zip
    VALID_CONTROL_AUTHORITY_DATA["address"]["zip_code"] = "12345"


def test_validate_company_schema_valid():
    """Test the json schema validator with a valid company data."""
    assert validate_company_schema(VALID_COMPANY_DATA) is None

    # valid with specific zip code
    VALID_COMPANY_DATA["address"]["zip_code"] = "978"
    assert validate_company_schema(VALID_COMPANY_DATA) is None

    # test with null values
    valid_company_data = {
        "company_type": None,
        "name": None,
        "legal_form": None,
        "trade_name": None,
        "siret": None,
        "naf": None,
        "address": {
            "line_1": None,
            "zip_code": None,
            "city": None,
        },
    }
    assert validate_company_schema(valid_company_data) is None


def test_validate_company_schema_invalid():
    """Test the json schema validator with a valid company data."""
    # test without properties
    invalid_value = {}
    with pytest.raises(ValidationError):
        validate_company_schema(invalid_value)

    # test with additional properties
    invalid_value = VALID_COMPANY_DATA
    invalid_value["additional_property"] = ""
    with pytest.raises(ValidationError):
        validate_company_schema(invalid_value)


def test_validate_representative_schema_valid():
    """Test the json schema validator with a valid representative company data."""
    assert validate_representative_schema(VALID_REPRESENTATIVE_DATA) is None

    # test with null values
    validate_representative_data = {
        "firstname": None,
        "lastname": None,
        "email": None,
        "phone": None,
    }
    assert validate_representative_schema(validate_representative_data) is None


def test_validate_representative_schema_invalid():
    """Test the json schema validator with a valid representative company data."""
    # test without properties
    invalid_value = {}
    with pytest.raises(ValidationError):
        validate_representative_schema(invalid_value)

    # test with invalid value
    invalid_value = VALID_REPRESENTATIVE_DATA
    invalid_value["firstname"] = 1234
    with pytest.raises(ValidationError):
        validate_representative_schema(invalid_value)

    # test with additional properties
    invalid_value = VALID_REPRESENTATIVE_DATA
    invalid_value["additional_property"] = ""
    with pytest.raises(ValidationError):
        validate_representative_schema(invalid_value)


def test_validate_control_authority_schema_valid():
    """Test the json schema validator with a valid control authority data."""
    assert validate_control_authority_schema(VALID_CONTROL_AUTHORITY_DATA) is None

    validate_control_authority_data = {
        "name": None,
        "represented_by": None,
        "email": None,
        "address": {
            "line_1": None,
            "zip_code": None,
            "city": None,
        },
    }
    assert validate_control_authority_schema(validate_control_authority_data) is None


def test_validate_control_authority_schema_invalid():
    """Test the json schema validator with a valid control authority data."""
    # test without properties
    invalid_value = {}
    with pytest.raises(ValidationError):
        validate_control_authority_schema(invalid_value)

    # test with invalid value
    invalid_value = VALID_CONTROL_AUTHORITY_DATA
    invalid_value["represented_by"] = 1234
    with pytest.raises(ValidationError):
        validate_control_authority_schema(invalid_value)

    # test with additional properties
    invalid_value = VALID_CONTROL_AUTHORITY_DATA
    invalid_value["additional_property"] = ""
    with pytest.raises(ValidationError):
        validate_control_authority_schema(invalid_value)
