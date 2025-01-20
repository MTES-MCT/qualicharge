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


def test_validate_company_schema_valid():
    """Test the json schema validator with a valid company data."""
    validate_company_schema(VALID_COMPANY_DATA)


def test_validate_company_schema_invalid():
    """Test the json schema validator with a valid company data."""
    # test without properties
    invalid_value = {}
    with pytest.raises(ValidationError):
        validate_company_schema(invalid_value)

    # test with invalid value (invalid siret)
    invalid_value = VALID_COMPANY_DATA
    invalid_value["siret"] = "1234"
    with pytest.raises(ValidationError):
        validate_company_schema(invalid_value)

    # test with additional properties
    invalid_value = VALID_COMPANY_DATA
    invalid_value["additional_property"] = ""
    with pytest.raises(ValidationError):
        validate_company_schema(invalid_value)


def test_validate_representative_schema_valid():
    """Test the json schema validator with a valid representative company data."""
    validate_representative_schema(VALID_REPRESENTATIVE_DATA)


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
    validate_control_authority_schema(VALID_CONTROL_AUTHORITY_DATA)


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
