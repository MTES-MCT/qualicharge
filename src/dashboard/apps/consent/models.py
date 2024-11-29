"""Dashboard consent app models."""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.abstract_models import DashboardBase

from . import AWAITING, CONSENT_STATUS_CHOICE, REVOKED
from .managers import ConsentManager


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

    delivery_point = models.ForeignKey(
        "qcd_core.DeliveryPoint", on_delete=models.CASCADE, related_name="consents"
    )
    created_by = models.ForeignKey(
        "qcd_auth.DashboardUser",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("created by"),
    )
    status = models.CharField(
        _("status"), max_length=20, choices=CONSENT_STATUS_CHOICE, default=AWAITING
    )

    # Validity period
    start = models.DateTimeField(_("start date"))
    end = models.DateTimeField(_("end date"))
    revoked_at = models.DateTimeField(_("revoked at"), null=True, blank=True)

    active_objects = ConsentManager()
    objects = models.Manager()

    class Meta:  # noqa: D106
        ordering = ["delivery_point"]

    def __str__(self):  # noqa: D105
        return f"{self.delivery_point} - {self.updated_at}: {self.status}"

    def save(self, *args, **kwargs):
        """Update the revoked_at timestamps if the consent is revoked."""
        if self.status == REVOKED:
            self.revoked_at = timezone.now()
        return super(Consent, self).save(*args, **kwargs)
