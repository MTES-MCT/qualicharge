"""Dashboard consent app models."""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.abstract_models import DashboardBase

from . import AWAITING, CONSENT_STATUS_CHOICE, REVOKED, VALIDATED
from .exceptions import ConsentWorkflowError
from .managers import ConsentManager, UpcomingConsentManager
from .utils import consent_end_date
from .validators import (
    validate_company_schema,
    validate_contract_holder_schema,
    validate_control_authority_schema,
    validate_representative_schema,
)

COMPANY_SCHEMA = {
    "type": "object",
    "properties": {
        "company_type": {"type": ["string", "null"], "maxLength": 255},
        "name": {"type": ["string", "null"], "maxLength": 255},
        "legal_form": {"type": ["string", "null"], "maxLength": 50},
        "trade_name": {"type": ["string", "null"], "maxLength": 255},
        "siret": {
            "type": ["string", "null"],
            "maxLength": 14,
            "pattern": r"^\d{14}$",
        },
        "naf": {
            "type": ["string", "null"],
            "maxLength": 5,
            "pattern": r"^\d{4}[A-Z]$",
        },
        "address_1": {"type": ["string", "null"], "maxLength": 255},
        "address_2": {"type": ["string", "null"], "maxLength": 255},
        "zip_code": {
            "type": ["string", "null"],
            "maxLength": 5,
            "pattern": "^[0-9]{1,5}$",
        },
        "city": {"type": ["string", "null"], "maxLength": 255},
    },
    "required": [
        "company_type",
        "name",
        "legal_form",
        "trade_name",
        "siret",
        "naf",
        "address_1",
        "zip_code",
        "city",
    ],
    "additionalProperties": False,
}

REPRESENTATIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "firstname": {"type": ["string", "null"], "maxLength": 150},
        "lastname": {"type": ["string", "null"], "maxLength": 150},
        "email": {"type": ["string", "null"], "format": "email"},
        "phone": {"type": ["string", "null"], "maxLength": 20},
    },
    "required": ["firstname", "lastname", "email", "phone"],
    "additionalProperties": False,
}

CONTROL_AUTHORITY_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": ["string", "null"], "maxLength": 255},
        "represented_by": {"type": ["string", "null"], "maxLength": 255},
        "email": {"type": ["string", "null"], "format": "email"},
        "address_1": {"type": ["string", "null"], "maxLength": 255},
        "address_2": {"type": ["string", "null"], "maxLength": 255},
        "zip_code": {
            "type": ["string", "null"],
            "maxLength": 5,
            "pattern": "^[0-9]{1,5}$",
        },
        "city": {"type": ["string", "null"], "maxLength": 255},
    },
    "required": ["name", "represented_by", "email", "address_1", "zip_code", "city"],
    "additionalProperties": False,
}

CONTRACT_HOLDER_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": ["string", "null"], "maxLength": 150},
        "email": {"type": ["string", "null"], "format": "email"},
        "phone": {"type": ["string", "null"], "maxLength": 20},
    },
    "required": ["name", "email", "phone"],
    "additionalProperties": False,
}


class Consent(DashboardBase):
    """Represents the consent status for a given delivery point and user.

    For contractual reason, a consent cannot be modified after it has the status
    `VALIDATED` or `REVOKED`.

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

    provider_assigned_id = models.CharField(
        _("provider assigned id"), max_length=64, blank=True
    )
    id_station_itinerance = models.CharField(
        _("id station itinerance"), max_length=35, blank=True
    )
    station_name = models.CharField(_("station name"), max_length=255, blank=True)

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

    # Contractual field of the company
    company = models.JSONField(
        _("company informations"),
        blank=True,
        null=True,
        default=None,
        validators=[validate_company_schema],
    )

    # Contractual field of the company representative
    company_representative = models.JSONField(
        _("company representative informations"),
        blank=True,
        null=True,
        default=None,
        validators=[validate_representative_schema],
    )

    # Contractual field of the control authority
    control_authority = models.JSONField(
        _("control authority informations"),
        blank=True,
        null=True,
        default=None,
        validators=[validate_control_authority_schema],
    )

    # contract holder information
    # (Holder of the supply contract for delivery points)
    contract_holder = models.JSONField(
        _("contract holder informations"),
        blank=True,
        null=True,
        default=None,
        validators=[validate_contract_holder_schema],
    )

    # specific authorization fields
    is_authoritative_signatory = models.BooleanField(
        _("the signatory has the authority to sign this consent"), default=False
    )
    allows_measurements = models.BooleanField(
        _("allows historical measurements in kWh"), default=False
    )
    allows_daily_index_readings = models.BooleanField(
        _("allow history of daily index readings in kWh"), default=False
    )
    allows_max_daily_power = models.BooleanField(
        _("allows historical maximum daily power in kVa or kWh "), default=False
    )
    allows_load_curve = models.BooleanField(
        _("allows history of load curve, at steps returned by Enedis"), default=False
    )
    allows_technical_contractual_data = models.BooleanField(
        _("allows the technical and contractual data available"), default=False
    )

    signed_at = models.DateTimeField(_("signature date"), blank=True, null=True)
    signature_location = models.CharField(
        _("signature location"), max_length=255, blank=True, null=True
    )

    # models.Manager() must be in first place to ensure django admin expectations.
    objects = models.Manager()
    active_objects = ConsentManager()
    upcoming_objects = UpcomingConsentManager()

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
        if self._is_update_allowed():
            return

    def save(self, *args, **kwargs):
        """Saves with custom logic.

        - Validates and restricts updates to the consent based on its status and
        modified fields.
        - Updates `revoked_at` with the current date if the consent status is `REVOKED`.
        """
        if not self._is_update_allowed():
            return

        if self.status == REVOKED:
            self.revoked_at = timezone.now()

        return super(Consent, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restrict the deletion of a consent.

        Consents cannot be deleted if status is `VALIDATED` or `REVOKED`.
        """
        if self._is_deletion_allowed():
            super().delete(*args, **kwargs)

    def _is_update_allowed(self) -> bool:
        """Check if consent can be updated.

        Workflow according to consent status:
        - AWAITING:
            - can be updated without restriction.

        - VALIDATED
            - if the status is updated to something other than REVOKED, an exception is
            raised,
            - if the status is updated to REVOKED, we check the updated fields are
             allowed to be updated.

        - REVOKED
            - can be updated without restriction
        """
        ALLOWED_UPDATE_FIELDS = {"status", "revoked_at", "updated_at"}

        if self._state.adding:
            return True

        loaded_status = self._loaded_values.get("status")  # type: ignore[attr-defined]
        updated_status = self.status

        if loaded_status == REVOKED:
            raise ConsentWorkflowError(_("Revoked consent cannot be modified."))

        elif loaded_status == VALIDATED:
            if updated_status != REVOKED:
                raise ConsentWorkflowError(
                    _('Validated consent can only be changed to the status "revoked".')
                )

            # Update the consent status from VALIDATED to REVOKED
            # we check the updated fields are allowed to be updated.
            updated_fields = {
                field
                for field, loaded_value in self._loaded_values.items()  # type: ignore[attr-defined]
                if getattr(self, field) != loaded_value
            }

            if not updated_fields.issubset(ALLOWED_UPDATE_FIELDS):
                raise ConsentWorkflowError(
                    _(
                        f"Only the authorized fields "
                        f"({', '.join(sorted(ALLOWED_UPDATE_FIELDS))}) can be modified."
                    )
                )

        return True

    def _is_deletion_allowed(self) -> bool:
        """Check if a consent can be deleted.

        Consent cannot be deleted if his loaded status is `VALIDATED` or `REVOKED`.
        """
        if self._loaded_values.get("status") == VALIDATED:  # type: ignore[attr-defined]
            raise ConsentWorkflowError(_("Validated consent cannot be deleted."))

        elif self._loaded_values.get("status") == REVOKED:  # type: ignore[attr-defined]
            raise ConsentWorkflowError(_("Revoked consent cannot be deleted."))

        return True
