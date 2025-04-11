"""Dashboard renewable app models."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.abstract_models import DashboardBase


class Renewable(DashboardBase):
    """Renewable model."""

    provider_assigned_id = models.CharField(
        _("provider assigned id"), max_length=64, blank=True
    )
    delivery_point = models.ForeignKey(
        "qcd_core.DeliveryPoint", on_delete=models.CASCADE, related_name="renewables"
    )
    created_by = models.ForeignKey(
        "qcd_auth.DashboardUser",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("created by"),
    )
    meter_reading = models.PositiveIntegerField(
        _("meter reading"), blank=True, null=True
    )

    # Meter reading period
    # todo : add default start / end
    start = models.DateTimeField(_("start date"), blank=True, null=True)
    end = models.DateTimeField(_("end date"), blank=True, null=True)

    signed_at = models.DateTimeField(_("signature date"), blank=True, null=True)
    signature_location = models.CharField(
        _("signature location"), max_length=255, blank=True, null=True
    )

    class Meta:  # noqa: D106
        ordering = ["provider_assigned_id", "start"]

    def __str__(self):  # noqa: D105
        return f"{self.provider_assigned_id} - {self.updated_at}: {self.meter_reading}"
