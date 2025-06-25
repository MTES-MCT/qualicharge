"""Dashboard renewable app models."""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.abstract_models import DashboardBase
from apps.renewable.managers import RenewableManager


class Renewable(DashboardBase):
    """Renewable model."""

    meter_reading = models.FloatField(
        _("meter reading"),
        validators=[MinValueValidator(0.0, message=_("The value must be positive"))],
    )
    collected_at = models.DateTimeField(_("collection date"))
    delivery_point = models.ForeignKey(
        "qcd_core.DeliveryPoint", on_delete=models.CASCADE, related_name="renewables"
    )
    created_by = models.ForeignKey(
        "qcd_auth.DashboardUser",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("created by"),
    )

    # contractual information
    signed_at = models.DateTimeField(_("signature date"))
    signature_location = models.CharField(_("signature location"), max_length=255)
    has_confirmed_information_accuracy = models.BooleanField(
        _("has confirmed information accuracy"), default=False
    )

    objects = models.Manager()
    active_objects = RenewableManager()

    class Meta:  # noqa: D106
        ordering = ["delivery_point__provider_assigned_id", "collected_at"]

    def __str__(self):  # noqa: D105
        return (
            f"{self.delivery_point.provider_assigned_id} - {self.collected_at}: "
            f"{self.meter_reading}"
        )
