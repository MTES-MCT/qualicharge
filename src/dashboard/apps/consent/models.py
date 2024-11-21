"""Dashboard consent app models."""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.auth.models import DashboardUser as User
from apps.core.models import DashboardBase, DeliveryPoint


class Consent(DashboardBase):
    """Represents the consent status for a given delivery point and user.

    Attributes:
    - AWAITING: Status indicating that the consent is awaiting validation.
    - VALIDATED: Status indicating that the consent has been validated.
    - REVOKED: Status indicating that the consent has been revoked.

    - delivery_point (ForeignKey): relation to the delivery point associated with the
        consent.
    - created_by (ForeignKey): relation to the user giving the consent.
    - status (CharField): storing the status of the consent, with choices constrained
        by CONSENT_STATUS_CHOICE.
    - start (DateTimeField): representing the start date of the consent validity.
    - end (DateTimeField): representing the end date of the consent validity.
    - revoked_at (DateTimeField): recording the revoked date of the consent, if any.
    """

    AWAITING = "AWAITING"
    VALIDATED = "VALIDATED"
    REVOKED = "REVOKED"
    CONSENT_STATUS_CHOICE = [
        (AWAITING, _("Awaiting")),
        (VALIDATED, _("Validated")),
        (REVOKED, _("Revoked")),
    ]

    delivery_point = models.ForeignKey(DeliveryPoint, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name=_("created by")
    )
    status = models.CharField(
        _("status"), max_length=20, choices=CONSENT_STATUS_CHOICE, default=AWAITING
    )

    # Validity period
    start = models.DateTimeField(_("start date"))
    end = models.DateTimeField(_("end date"))
    revoked_at = models.DateTimeField(_("revoked at"), null=True, blank=True)

    class Meta:  # noqa: D106
        ordering = ["delivery_point"]

    def __str__(self):  # noqa: D105
        return f"{self.delivery_point} - {self.updated_at}: {self.status}"

    def save(self, *args, **kwargs):
        """Update the revoked_at timestamps if the consent is revoked."""
        if self.status == self.REVOKED:
            self.revoked_at = timezone.now()
        return super(Consent, self).save(*args, **kwargs)
