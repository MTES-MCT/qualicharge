"""Dashboard consent exceptions."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ConsentWorkflowError(ValidationError):
    """Exception for consent workflow validation errors."""

    DEFAULT_MESSAGE = _("Consent workflow error.")

    def __init__(self, custom_message=None):
        """Initialize the exception with an optional custom message."""
        super().__init__(custom_message or self.DEFAULT_MESSAGE)
