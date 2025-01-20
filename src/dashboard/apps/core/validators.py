"""Dashboard core app validators."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_siret(value: str | None) -> None:
    """Validate a SIRET number.

    SIRET must be a string that contains only numbers and have a fixed length of 14
    characters.
    """
    error_message = _(
        "The SIRET must be composed only of numbers and must "
        "contain exactly 14 digits."
    )

    if value is None:
        return

    if not isinstance(value, str):
        raise ValidationError(error_message)

    if not re.match(r"^\d{14}$", value):
        raise ValidationError(error_message)


def validate_naf_code(value: str | None) -> None:
    """Validate a NAF code.

    NAF code must respect the format "####A" (4 digits + 1 letter).
    """
    error_message = _(
        "The NAF code must be in the format of 4 digits "
        "followed by a letter (e.g.: 6820A)."
    )

    if value is None:
        return

    if not isinstance(value, str):
        raise ValidationError(error_message)

    if not re.match(r"^\d{4}[A-Z]$", value):
        raise ValidationError(error_message)


def validate_zip_code(value: str | None) -> None:
    """Validate a zip code.

    Zip code must have only digits and a fixed length of 5 characters.
    """
    error_message = _(
        "Zip code must be composed of number and a fixed length of 5 characters."
    )

    if value is None:
        return

    if not isinstance(value, str):
        raise ValidationError(error_message)

    if not re.match(r"^[0-9]{1,5}$", value):
        raise ValidationError(error_message)
