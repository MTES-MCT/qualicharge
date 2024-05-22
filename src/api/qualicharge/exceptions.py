"""QualiCharge exceptions."""


class QualiChargeExceptionMixin:
    """A mixin for QualiCharge exceptions."""

    def __init__(self, name: str):
        """Add name property for our exception handler."""
        self.name = name


class AuthenticationError(QualiChargeExceptionMixin, Exception):
    """Raised when the authentication flow fails."""


class PermissionDenied(QualiChargeExceptionMixin, Exception):
    """Raised when authenticated user does not have required permissions."""


class OIDCAuthenticationError(QualiChargeExceptionMixin, Exception):
    """Raised when the OIDC authentication flow fails."""


class OIDCProviderException(QualiChargeExceptionMixin, Exception):
    """Raised when the OIDC provider does not behave as expected."""


class ModelSerializerException(QualiChargeExceptionMixin, Exception):
    """Raised when a custom model serialization occurs."""


class DatabaseQueryException(QualiChargeExceptionMixin, Exception):
    """Raised when a database query does not provide expected results."""


class DuplicateEntriesSubmitted(QualiChargeExceptionMixin, Exception):
    """Raised when submitted batch contains duplicated entries."""


class IntegrityError(QualiChargeExceptionMixin, Exception):
    """Raised when operation affects database integrity."""


class ObjectDoesNotExist(QualiChargeExceptionMixin, Exception):
    """Raised when queried object does not exist."""
