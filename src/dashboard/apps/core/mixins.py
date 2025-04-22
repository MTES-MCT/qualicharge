"""Dashboard core mixins."""

from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404

from apps.auth.models import DashboardUser
from apps.core.models import Entity


class EntityMixin:
    """Mixin to retrieve a specific entity with permission validation."""

    kwargs: dict[str, Any]
    request: Any

    def get_entity(self) -> Entity:
        """Return the specific entity with the provided slug."""
        slug: str | None = self.kwargs.get("slug", None)
        user: DashboardUser = self.request.user

        if not slug:
            raise Http404

        entity: Entity = get_object_or_404(Entity, slug=slug)
        if not user.can_validate_entity(entity):
            raise PermissionDenied
        return entity
