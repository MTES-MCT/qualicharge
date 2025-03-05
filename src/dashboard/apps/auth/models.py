"""Dashboard auth models."""

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from apps.core.models import Entity


class DashboardUser(AbstractUser):
    """Represents a user in the Dashboard application, extending the AbstractUser model.

    Designed to be used as part of the system's authentication and user
    management functionality, incorporating the fields and methods provided by the
    AbstractUser model in Django.
    """

    siret = models.CharField(_("SIRET"), max_length=14, default="", blank=True)
    is_validated = models.BooleanField(
        _("is validated"),
        default=False,
        help_text=_(
            "Designates whether this user has been validated by the QualiCharge team."
        ),
    )

    def save(self, *args, **kwargs):
        """Override the save method to send a validation email."""
        # Check if `is_validated` changes to True
        if self.pk:
            previous = DashboardUser.objects.filter(pk=self.pk).first()
            if not previous.is_validated and self.is_validated:
                self.send_validation_email()

        super().save(*args, **kwargs)

    def get_entities(self) -> QuerySet[Entity]:
        """Get a list of entities, and their proxies associated."""
        return Entity.objects.filter(Q(users=self) | Q(proxies__users=self)).distinct()

    def can_validate_entity(self, entity: Entity) -> bool:
        """Determines if the provided entity can be validated."""
        return entity in self.get_entities()

    def send_validation_email(self) -> None:
        """Send a validation email to the user."""
        email_to = self.email
        email_config = settings.DASHBOARD_EMAIL_CONFIGS["validated_user"]
        email_data = {
            email_to: {
                "last_name": self.last_name,  # type: ignore[union-attr]
                "first_name": self.first_name,  # type: ignore[union-attr]
                "link": email_config.get("link"),
                "support_email": settings.CONTACT_EMAIL,
            },
        }

        email = AnymailMessage(
            to=[
                email_to,
            ],
            template_id=email_config.get("template_id"),
            merge_data=email_data,
        )

        try:
            email.send()
        except AnymailRequestsAPIError as e:
            # fail silently and send a sentry log
            sentry_sdk.capture_exception(e)
