"""Dashboard consent app validators."""

from django.core.exceptions import ValidationError
from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate

from apps.consent.schemas import (
    company_schema,
    control_authority_schema,
    representative_schema,
)


def json_schema_validator(schema):
    """JSON schema validator."""

    def validator(value):
        """Validate a JSON object against a schema."""
        try:
            validate(instance=value, schema=schema)
        except JSONSchemaValidationError as e:
            raise ValidationError(f"Invalid JSON: {e.message}") from e

    return validator


def validate_company_schema(value):
    """Validate a company JSON object against the company schema."""
    validator = json_schema_validator(company_schema)
    return validator(value)


def validate_representative_schema(value):
    """Validate a representative JSON object against the representative schema."""
    validator = json_schema_validator(representative_schema)
    return validator(value)


def validate_control_authority_schema(value):
    """Validate a control authority JSON object against the control authority schema."""
    validator = json_schema_validator(control_authority_schema)
    return validator(value)
