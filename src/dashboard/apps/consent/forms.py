"""Dashboard consent app forms."""

from django import forms
from django.forms.widgets import CheckboxInput
from django.utils.translation import gettext_lazy as _


class ConsentCheckboxInput(CheckboxInput):
    """Custom CheckboxInput widget for rendering a checkbox input field."""

    template_name = "consent/forms/widgets/checkbox.html"


class ConsentForm(forms.Form):
    """Save user consent through a checkbox field."""

    # Specific authorisation checkbox
    is_authorized_signatory = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("the signatory is authorized"),
            },
        ),
    )

    allows_measurements = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("allows historical measurements in kWh"),
            },
        ),
    )
    allows_daily_index_readings = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("allow history of daily index readings in kWh")
            },
        ),
    )
    allows_max_daily_power = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("allows historical maximum daily power in kVa or kWh "),
            },
        ),
    )
    allows_load_curve = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("allows history of load curve, at steps returned by Enedis"),
            },
        ),
    )
    allows_technical_contractual_data = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("allows the technical and contractual data available"),
            },
        ),
    )

    # Global authorisation checkbox
    consent_agreed = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _("I agree to give my consent"),
                "help_text": _("Please confirm your consent by checking this box."),
            },
        ),
    )
