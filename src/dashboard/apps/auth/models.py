"""Dashboard auth models."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from apps.auth.mails import send_validation_email
from apps.core.models import Entity


class DashboardUser(AbstractUser):
    """Represents a user in the Dashboard application, extending the AbstractUser model.

    Designed to be used as part of the system's authentication and user
    management functionality, incorporating the fields and methods provided by the
    AbstractUser model in Django.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
            if previous and not previous.is_validated and self.is_validated:
                send_validation_email(self)

        super().save(*args, **kwargs)

    def get_entities(self) -> QuerySet[Entity]:
        """Get a list of entities, and their proxies associated."""
        return Entity.objects.filter(Q(users=self) | Q(proxies__users=self)).distinct()

    def can_validate_entity(self, entity: Entity) -> bool:
        """Determines if the provided entity can be validated."""
        return entity in self.get_entities()
