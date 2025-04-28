"""Dashboard renewable app forms."""

import datetime

from django import forms
from django.conf import settings
from django.forms import BaseModelFormSet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.renewable.models import Renewable


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
        """Validates the collected_at field."""
        collected_at = self.cleaned_data.get("collected_at")
        meter_reading = self.cleaned_data.get("meter_reading")

        if meter_reading and not collected_at:
            raise forms.ValidationError(
                _("Collected date is required if a meter reading is provided")
            )

        if not collected_at:
            return collected_at

        # TODO: This logic should be moved to the models or a helper function.
        # TODO: Review the logic: readings meters should be taken between the last day
        #  of the previous quarter and 'x' days before the end of the previous quarter.
        # TODO: the 'x' days should be configurable via the settings.
        today = datetime.datetime.now().date()
        min_date = today - datetime.timedelta(days=10)

        if collected_at > today:
            raise forms.ValidationError(_("The date cannot be in the future"))
        elif collected_at < min_date:
            raise forms.ValidationError(
                _(f"The date cannot be earlier than {min_date}")
            )

        return collected_at


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
