"""Dashboard auth models."""

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

    def get_entities(self) -> QuerySet[Entity]:
        """Get a list of entities, and their proxies associated."""
        return Entity.objects.filter(Q(users=self) | Q(proxies__users=self)).distinct()

    def can_validate_entity(self, entity: Entity) -> bool:
        """Determines if the provided entity can be validated."""
        return entity in self.get_entities()
