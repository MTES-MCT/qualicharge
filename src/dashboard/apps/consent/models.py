"""Dashboard consent app models."""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.abstract_models import DashboardBase

from . import AWAITING, CONSENT_STATUS_CHOICE, REVOKED, VALIDATED
from .managers import ConsentManager
from .utils import consent_end_date


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

    VALIDATION_ERROR_MESSAGE = _("Validated consent cannot be modified once defined.")

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
    start = models.DateTimeField(_("start date"), default=timezone.now)
    end = models.DateTimeField(_("end date"), default=consent_end_date)
    revoked_at = models.DateTimeField(_("revoked at"), null=True, blank=True)

    # models.Manager() must be in first place to ensure django admin expectations.
    objects = models.Manager()
    active_objects = ConsentManager()

    class Meta:  # noqa: D106
        ordering = ["delivery_point"]

    def __str__(self):  # noqa: D105
        return f"{self.delivery_point} - {self.updated_at}: {self.status}"

    @classmethod
    def from_db(cls, db, field_names, values):
        """Store the original values when an instance is loaded from the database."""
        instance = super().from_db(db, field_names, values)
        instance._loaded_values = dict(zip(field_names, values, strict=False))
        return instance

    def clean(self):
        """Custom validation logic.

        Validates and restricts updates to the Consent object if its status is set
        to `VALIDATED`. This ensures that validated consents cannot be modified
        after their status are defined to `VALIDATED` (We prevent this update
        for contractual reasons).

        Raises:
        ------
        ValidationError
            If the Consent object's status is `VALIDATED`.
        """
        if self._is_validated_and_modified():
            raise ValidationError(message=self.VALIDATION_ERROR_MESSAGE)

    def save(self, *args, **kwargs):
        """Saves with custom logic.

        If the consent status is `REVOKED`, `revoked_at` is updated to the current time.
        """
        if self._is_validated_and_modified():
            raise ValidationError(message=self.VALIDATION_ERROR_MESSAGE)

        if self.status == REVOKED:
            self.revoked_at = timezone.now()

        return super(Consent, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restrict the deletion of a consent if its status is `VALIDATED`."""
        if self._loaded_values.get("status") == VALIDATED:
            raise ValidationError(message=self.VALIDATION_ERROR_MESSAGE)
        super().delete(*args, **kwargs)

    def _is_validated_and_modified(self):
        """Checks if the validated 'Consent' object is trying to be modified."""
        return not self._state.adding and self._loaded_values.get("status") == VALIDATED
