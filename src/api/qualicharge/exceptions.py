"""QualiCharge exceptions."""


class OIDCAuthenticationError(Exception):
    """Raised when the OIDC authentication flow fails."""


class OIDCProviderException(Exception):
    """Raised when the OIDC provider does not behave as expected."""
