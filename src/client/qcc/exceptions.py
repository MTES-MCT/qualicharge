"""QualiCharge API client exceptions."""


class ConfigurationError(Exception):
    """Raised when the client is not properly configured."""


class AuthenticationError(Exception):
    """Raised when the API client cannot authenticate user."""


class APIRequestError(Exception):
    """Raised when an API request failed."""
