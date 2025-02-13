"""Dashboard consent app forms."""

from datetime import datetime

from django import forms
from django.forms.widgets import CheckboxInput
from django.utils.translation import gettext_lazy as _


class ConsentCheckboxInput(CheckboxInput):
    """Custom CheckboxInput widget for rendering a checkbox input field."""

    template_name = "consent/forms/widgets/checkbox.html"


class ConsentForm(forms.Form):
    """Save user consent through a checkbox field.

    Note: all texts of this form (attributes: `label`, `description`, `help_text`)
    are intended to appear in a contract and must therefore be in French and
    non-translatable.
    """

    # Specific authorisation checkbox
    is_authoritative_signatory = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": "Le signataire du présent formulaire déclare être dûment "
                "habilité par le client pour la signature du présent "
                "document.",
            },
        ),
    )

    allows_measurements = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": "L'historique des mesures, en kWh,",
                "description": "du site (et puissances atteintes et dépassements "
                "de puissance) : sur la période souhaitée, de 36 mois "
                "maximum à compter de la date de la demande "
                "(période limitée à la date de début du contrat)",
            },
        ),
    )
    allows_daily_index_readings = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": "L'historique des relevés d'index quotidiens, en kWh, ",
                "description": "du site; sur la période souhaitée, de 36 mois maximum "
                "à compter de la date de la demande (période limitée "
                "à la date de début du contrat)",
            },
        ),
    )
    allows_max_daily_power = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": "L'historique de la puissance maximale quotidienne, en kVA "
                "ou kWh,",
                "description": "du site ; sur la période souhaitée, de 36 mois maximum "
                "à compter de la date de la demande (période limitée à "
                "la date de début du contrat)",
            },
        ),
    )
    allows_load_curve = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": "L'historique de courbe de charge, aux pas restitués "
                "par Enedis,",
                "description": "du site<sup>1</sup>; sur la période souhaitée, "
                "de 24 mois maximum "
                "à compter de la date de la demande (période limitée à "
                "la date de début du contrat)",
                "help_text": "<sup>1</sup> Ensembles de valeurs moyennes horodatées "
                "de la puissance active ou réactive soutirée, sur des "
                "périodes d'intégrations consécutives et de même durée.",
            },
        ),
    )
    allows_technical_contractual_data = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": "Les données techniques et contractuelles disponibles ",
                "description": "du site ; Caractéristiques du raccordement, du "
                "dispositif de comptage et des informations "
                "contractuelles (option tarifaire, puissance "
                "souscrite...)",
            },
        ),
    )

    signed_at = forms.DateField(
        initial=datetime.now().strftime("%d/%m/%Y"),
        required=True,
        widget=forms.HiddenInput(attrs={"readonly": "readonly"}),
    )

    # Global authorisation checkbox - this field must be in last position.
    consent_agreed = forms.BooleanField(
        required=True,
        initial=False,
        widget=ConsentCheckboxInput(
            attrs={
                "label": _(
                    "Je confirme l'exactitude des informations du présent "
                    "formulaire et consent au traitement de mes données Enedis "
                    "par la DGEC"
                ),
            },
        ),
    )
