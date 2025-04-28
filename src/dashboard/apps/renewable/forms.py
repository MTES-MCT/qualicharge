"""Dashboard renewable app forms."""

import datetime
import uuid

from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from apps.consent.forms import ConsentCheckboxInput
from apps.renewable.models import Renewable


class RenewableReadingForm(ModelForm):
    """Form for managing renewable energy readings.

    Custom ModelForm designed to handle renewal energy readings input.
    It dynamically creates fields (collected_at_<uuid> and meter_reading_<uuid>) for
    submitting meter readings for each delivery point provided during initialization.

    Attributes:
        has_confirmed_information_accuracy (BooleanField): Global checkbox requiring the
        user's agreement to confirm information accuracy and consent for data
        processing.

        delivery_points (Optional): List of delivery points dynamically added as
        form fields for collecting readings and timestamps if provided during
        form initialization.
    """

    # Global authorization checkbox
    # todo: add real content to the label
    has_confirmed_information_accuracy = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _(
                    "je certifie production à l’aval du PDL et compteur homologué "
                    "dédié, possibilité de contrôle sur site"
                ),
            },
        ),
    )

    class Meta:  # noqa: D106
        model = Renewable
        fields = ["has_confirmed_information_accuracy"]

    def __init__(self, *args, renewable_delivery_points=None, **kwargs):
        """Initializes a form with dynamic fields based on the provided delivery points.

        This constructor dynamically generates additional form fields
        (collected_at_<uuid> and meter_reading_<uuid>) for each delivery point provided.
        Each generated field is associated with the respective delivery point's unique
        identifier.

        Parameters:
            delivery_points (Optional[list]): List of delivery points for which
            dynamic fields are generated. Default is None.
        """
        super().__init__(*args, **kwargs)
        self.delivery_points = renewable_delivery_points
        self.field_errors = {}

        if self.delivery_points:
            for dp in self.delivery_points:
                self.fields[f"collected_at_{dp.id}"] = forms.DateField(
                    required=False,
                    label=_("collected at"),
                    widget=forms.DateInput(attrs={"type": "date"}),
                )
                self.fields[f"meter_reading_{dp.id}"] = forms.FloatField(
                    required=False,
                    label=_("meter reading"),
                    widget=forms.TextInput(attrs={"type": "number", "min": "0"}),
                )

    def clean(self):
        """Cleans the data of the form and particularly the dynamic fields."""
        cleaned_data = super().clean()

        for dp in self.delivery_points:
            self._clean_collected_at(dp.id)
            self._clean_meter_reading(dp.id)

        if self.field_errors:
            for field, error in self.field_errors.items():
                self.add_error(field, error)
            raise forms.ValidationError(_("The form contains errors"))

        return cleaned_data

    def _clean_collected_at(self, dp_id: uuid.UUID) -> bool:
        """Cleans and validates the dynamic 'collected_at' field.

        - Collected date is required if a meter reading is provided
        - The date cannot be in the future
        - The date cannot be earlier than x days
        """
        collected_at_key = f"collected_at_{dp_id}"
        meter_reading_key = f"meter_reading_{dp_id}"

        collected_at = self.data.get(collected_at_key)
        meter_reading = self.data.get(meter_reading_key)

        if meter_reading and not collected_at:
            self.field_errors[f"collected_at_{dp_id}"] = _(
                "Collected date is required if a meter reading is provided"
            )
            return True

        if not collected_at:
            return False

        # TODO: This logic should be moved to the models or a helper function.
        # TODO: Review the logic: readings meters should be taken between the last day
        #  of the previous quarter and 'x' days before the end of the previous quarter.
        # TODO: the 'x' days should be configurable via the settings.
        date_value = datetime.datetime.strptime(collected_at, "%Y-%m-%d").date()
        today = datetime.datetime.now().date()
        min_date = today - datetime.timedelta(days=10)

        if date_value > today:
            self.field_errors[collected_at_key] = _("The date cannot be in the future")
            return True
        elif date_value < min_date:
            self.field_errors[collected_at_key] = _(
                "The date cannot be earlier than 10 days"
            )
            return True

        return False

    def _clean_meter_reading(self, dp_id: uuid.UUID) -> bool:
        """Cleans and validates the dynamic 'meter_reading' field.

        - The value must be a positive float number

        todo : if value is inferior as the previous meter reading, raise an error
        """
        meter_reading_key = f"meter_reading_{dp_id}"
        meter_reading = self.data.get(meter_reading_key)

        if not meter_reading:
            return False

        try:
            if type(meter_reading) is str:
                meter_reading = float(meter_reading.replace(",", "."))
        except ValueError:
            self.field_errors[meter_reading_key] = _("Invalid number format")
            return True

        if meter_reading < 0:
            self.field_errors[meter_reading_key] = _("The value must be positive")
            return True

        return False
