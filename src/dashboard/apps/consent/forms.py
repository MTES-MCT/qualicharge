"""Dashboard consent app forms."""

from django import forms
from django.forms.widgets import CheckboxInput
from django.utils.translation import gettext_lazy as _


class ConsentCheckboxInput(CheckboxInput):
    """Custom CheckboxInput widget for rendering a checkbox input field."""

    template_name = "consent/forms/widgets/checkbox.html"


class ConsentForm(forms.Form):
    """Save user consent through a checkbox field."""

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
