"""Dashboard renewable app forms."""

from datetime import date, timedelta
from typing import Tuple

from django import forms
from django.conf import settings
from django.forms import BaseModelFormSet
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from apps.core.models import DeliveryPoint
from apps.core.utils import get_previous_quarter_date_range
from apps.renewable.models import Renewable

DateRange = Tuple[date, date]


class RenewableCheckboxInput(forms.CheckboxInput):
    """Custom CheckboxInput widget for rendering a checkbox input field."""

    template_name = "renewable/forms/widgets/checkbox.html"


class RenewableForm(forms.ModelForm):
    """Form for managing renewable meter readings."""

    BASE_WIDGET_ATTRS = {
        "class": "fr-input",
    }

    meter_reading = forms.FloatField(
        required=False,
        widget=forms.NumberInput(
            attrs={
                **BASE_WIDGET_ATTRS,
                "type": "number",
                "min": "0",
                "step": "0.01",
            }
        ),
    )
    collected_at = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                **BASE_WIDGET_ATTRS,
                "type": "date",
            }
        ),
    )

    class Meta:  # noqa: D106
        model = Renewable
        fields = ["meter_reading", "collected_at"]

    def __init__(self, *args, **kwargs):
        """Initializes the form with error classes and aria-describedby attributes."""
        super().__init__(*args, **kwargs)
        self._add_error_classes_to_fields()

    def _add_error_classes_to_fields(self):
        """Add error widget attributes to fields with errors."""
        if not self.errors:
            return

        for field_name, field in self.fields.items():
            if field_name in self.errors:
                current_class = field.widget.attrs.get("class", "")

                field.widget.attrs.update(
                    {
                        "class": f"{current_class} fr-input--error",
                        "aria-describedby": f"{ field_name }-desc-error",
                    }
                )

    def clean_collected_at(self):
        """Validates the collected_at field.

        - collected_at is required when a meter reading is provided
        - collected_at must be within the authorized date range
        - authorized date range:
            [previous_quarter_end - x_days] and [previous_quarter_end]
        - collected_at cannot be a future date
        """
        collected_at = self.cleaned_data.get("collected_at")
        meter_reading = self.cleaned_data.get("meter_reading")

        if meter_reading and not collected_at:
            raise forms.ValidationError(
                _("Collected date is required if a meter reading is provided")
            )

        if not collected_at:
            return collected_at

        min_date, end_date = self._get_authorized_date_range()

        if collected_at > end_date:
            raise forms.ValidationError(
                mark_safe(  # noqa: S308
                    _(
                        "The date cannot be in the future. <br />"
                        "Collected date should be "
                        "between %(min_date)s "
                        "and %(end_date)s."
                    )
                    % {
                        "min_date": min_date.strftime("%d/%m/%Y"),
                        "end_date": end_date.strftime("%d/%m/%Y"),
                    }
                )
            )
        elif collected_at < min_date:
            raise forms.ValidationError(
                mark_safe(  # noqa: S308
                    _(
                        "The date cannot be earlier than %(min_date)s."
                        "<br />"
                        "Collected date should be "
                        "between %(min_date_range)s "
                        "and %(end_date)s."
                    )
                    % {
                        "min_date": min_date.strftime("%d/%m/%Y"),
                        "min_date_range": min_date.strftime("%d/%m/%Y"),
                        "end_date": end_date.strftime("%d/%m/%Y"),
                    }
                )
            )

        return collected_at

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


class RenewableFormSet(BaseModelFormSet):
    """Formset for managing renewable meter readings.

    Custom formset class designed to manage forms related to renewable energy
    data collection and validation.
    Handles field-specific validations and instance saving operations.

    Attributes:
        has_confirmed_information_accuracy (BooleanField): Global checkbox requiring the
        user's agreement to confirm information accuracy and consent for data
        processing.
    """

    # todo: add real content to the label
    HAS_CONFIRMED_FIELD_NAME = "has_confirmed_information_accuracy"

    has_confirmed_information_accuracy = forms.BooleanField(
        required=True,
        initial=False,
        widget=RenewableCheckboxInput(
            attrs={
                "label": _(
                    "je certifie production à l’aval du PDL et compteur homologué "
                    "dédié, possibilité de contrôle sur site"
                ),
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initializes the formset with the user object."""
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def get_has_confirmed_information_accuracy_field(self):
        """Returns the rendered widget for field has_confirmed_information_accuracy."""
        return self.has_confirmed_information_accuracy.widget.render(
            name=self.HAS_CONFIRMED_FIELD_NAME,
            value=None,
            attrs={
                "id": f"id_{self.HAS_CONFIRMED_FIELD_NAME}",
                "required": "required",
            },
        )

    def clean(self):
        """Validates the formset data and updates instances if all forms are valid."""
        if any(self.errors):
            return

        cleaned_has_confirmed = self.clean_has_confirmed_information_accuracy()

        now = timezone.now()
        for form in self.forms:
            form.instance.created_by = self.user
            form.instance.signed_at = now
            form.instance.signature_location = settings.CONSENT_SIGNATURE_LOCATION
            form.instance.has_confirmed_information_accuracy = cleaned_has_confirmed

    def clean_has_confirmed_information_accuracy(self):
        """Validates the has_confirmed_information_accuracy field."""
        value = self.data.get(self.HAS_CONFIRMED_FIELD_NAME)
        if not value:
            raise forms.ValidationError(
                _("You must confirm the accuracy of the information")
            )

        return value == "on"

    def save(self, commit=True):
        """Saves the formset data to the database."""
        instances = []
        for form in self.forms:
            if (
                form.cleaned_data
                and form.cleaned_data.get("meter_reading")
                and form.cleaned_data.get("collected_at")
            ):
                instance = form.save(commit=False)
                instances.append(instance)

        if commit and instances:
            Renewable.objects.bulk_create(instances)

        return instances


class DeliveryPointRenewableForm(forms.ModelForm):
    """Form for managing renewable delivery points."""

    class Meta:  # noqa: D106
        model = DeliveryPoint
        fields = ["has_renewable"]
