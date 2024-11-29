"""Dashboard consent app."""

from typing import Literal

from django.utils.translation import gettext_lazy as _

AWAITING: str = "AWAITING"
VALIDATED: str = "VALIDATED"
REVOKED: str = "REVOKED"
CONSENT_STATUS_CHOICE = [
    (AWAITING, _("Awaiting")),
    (VALIDATED, _("Validated")),
    (REVOKED, _("Revoked")),
]

# typing
StatusChoices = Literal["AWAITING", "VALIDATED", "REVOKED"]
