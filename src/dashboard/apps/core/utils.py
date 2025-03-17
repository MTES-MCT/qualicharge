"""Dashboard core utils."""

from apps.core.validators import validate_siret


def siret2siren(siret: str) -> str:
    """Convert a SIRET to a SIREN."""
    validate_siret(siret)
    return siret[:9]
