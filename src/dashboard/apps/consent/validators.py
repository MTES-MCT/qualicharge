"""Dashboard consent app validators."""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate


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
    from .models import COMPANY_SCHEMA

    validator = json_schema_validator(COMPANY_SCHEMA)
    return validator(value)


def validate_representative_schema(value):
    """Validate a representative JSON object against the representative schema."""
    from .models import REPRESENTATIVE_SCHEMA

    validator = json_schema_validator(REPRESENTATIVE_SCHEMA)
    return validator(value)


def validate_control_authority_schema(value):
    """Validate a control authority JSON object against the control authority schema."""
    from .models import CONTROL_AUTHORITY_SCHEMA

    validator = json_schema_validator(CONTROL_AUTHORITY_SCHEMA)
    return validator(value)


def validate_configured_control_authority():
    """Validates the `settings.CONSENT_CONTROL_AUTHORITY`.

    Check if settings.CONSENT_CONTROL_AUTHORITY is valid,
    raise ImproperlyConfigured otherwise.
    """
    try:
        validate_control_authority_schema(settings.CONSENT_CONTROL_AUTHORITY)
    except ValidationError as e:
        raise ImproperlyConfigured(
            f"settings.CONSENT_CONTROL_AUTHORITY validation error: {e.message}"
        ) from e


def validate_contract_holder_schema(value):
    """Validate a contract holder JSON object against the contract holder schema."""
    from .models import CONTRACT_HOLDER_SCHEMA

    validator = json_schema_validator(CONTRACT_HOLDER_SCHEMA)
    return validator(value)
