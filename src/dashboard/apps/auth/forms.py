"""Dashboard auth forms."""

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import gettext_lazy as _

from .models import DashboardUser


class SiretSyncButtonWidget(forms.Widget):
    """Custom widget for the siret field.

    The widget adds a button to the form to trigger the entity synchronization.
    """

    template_name = "auth/widgets/siret_sync_button.html"

    def __init__(self, *args, user_instance=None, **kwargs):
        """Initialize the widget."""
        self.user_instance = user_instance
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        """Add custom context to the widget template."""
        context = super().get_context(name, value, attrs)
        context["entities"] = self.get_user_entities()
        return context

    def get_user_entities(self):
        """Returns entities linked to the user instance."""
        if self.user_instance:
            return self.user_instance.get_entities()
        return None


class DashboardUserForm(UserChangeForm):
    """Dashboard user form."""

    class Meta:
        """Meta for DashboardUserForm."""

        model = DashboardUser
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        """Initialize the form and add a custom widget to the 'siret' field."""
        self.instance = kwargs.get("instance")
        super().__init__(*args, **kwargs)

        # add a custom widget to the siret field
        siret = self.fields.get("siret")
        if siret:
            siret.widget = SiretSyncButtonWidget(user_instance=self.instance)
            siret.help_text = _(
                "Synchronize the entity with the 'Annuaire des Entreprises' "
                "API and attach the user to it."
            )
