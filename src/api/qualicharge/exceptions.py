"""QualiCharge exceptions."""


class QualiChargeExceptionMixin:
    """A mixin for QualiCharge exceptions."""

    def __init__(self, name: str):
        """Add name property for our exception handler."""
        self.name = name


class OIDCAuthenticationError(QualiChargeExceptionMixin, Exception):
    """Raised when the OIDC authentication flow fails."""


class OIDCProviderException(QualiChargeExceptionMixin, Exception):
    """Raised when the OIDC provider does not behave as expected."""
