"""Dashboard renewable app forms."""

from datetime import date, datetime, timedelta
from typing import Tuple

from django import forms
from django.conf import settings
from django.forms import ModelForm
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.consent.forms import ConsentCheckboxInput
from apps.core.utils import get_previous_quarter_date_range
from apps.renewable.models import Renewable

DateRange = Tuple[date, date]


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
        """Cleans the data of the form and add custom clean for the dynamic fields."""
        cleaned_data = super().clean()

        for dp in self.delivery_points:
            collected_at_key = f"collected_at_{dp.id}"
            meter_reading_key = f"meter_reading_{dp.id}"

            self._clean_collected_at(collected_at_key, meter_reading_key)
            self._clean_meter_reading(dp.id)

        if self.field_errors:
            for field, error in self.field_errors.items():
                self.add_error(field, error)
            raise forms.ValidationError(_("The form contains errors"))

        return cleaned_data

    def _clean_collected_at(
        self, collected_at_key: str, meter_reading_key: str
    ) -> bool:
        """Cleans and validates the dynamic 'collected_at' field.

        - Collected date is required if a meter reading is provided
        - The collected date must not exceed the end date of the previous quarter
        - The collected date must not be earlier than x days before the end date of the
        previous quarter.
        - x is defined in the settings.RENEWABLE_MIN_DAYS_FOR_METER_READING
        """
        collected_at = self.data.get(collected_at_key)
        meter_reading = self.data.get(meter_reading_key)

        if meter_reading and not collected_at:
            self.field_errors[collected_at_key] = _(
                "Collected date is required if a meter reading is provided"
            )
            return True

        if not collected_at:
            return False

        collected_date = datetime.strptime(collected_at, "%Y-%m-%d").date()
        min_date, end_date = self._get_authorized_date_range()

        if collected_date > end_date:
            self.field_errors[collected_at_key] = _(
                f"The date cannot be in the future. "
                f"Collected date should be between {min_date} and {end_date}."
            )
            return True
        elif collected_date < min_date:
            self.field_errors[collected_at_key] = _(
                f"The date cannot be earlier than {min_date}. "
                f"Collected date should be between {min_date} and {end_date}."
            )
            return True

        return False

    @staticmethod
    def _get_authorized_date_range() -> DateRange:
        """Returns the authorized date range for the meter reading.

        The method calculates the quarter date range based on the current date
        and ensures the start date aligns with the minimum required days for readings.

        Returns:
            Tuple[datetime, datetime]: A tuple containing the min date and end date
            for the authorized date range.
        """
        now = timezone.now()

        start_date, end_date = get_previous_quarter_date_range(now)
        min_date = end_date - timedelta(
            days=settings.RENEWABLE_MIN_DAYS_FOR_METER_READING
        )

        return min_date, end_date

    def _clean_meter_reading(self, meter_reading_key: str) -> bool:
        """Cleans and validates the dynamic 'meter_reading' field.

        - The value must be a positive float number
        - todo : if value is inferior as the previous meter reading, raise an error
        """
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
