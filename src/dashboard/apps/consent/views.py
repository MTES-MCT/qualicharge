"""Dashboard consent app views."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy as reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from apps.core.models import Entity
from dashboard.settings import CONTACT_EMAIL

from ..auth.models import DashboardUser
from . import AWAITING, VALIDATED
from .forms import ConsentForm
from .mixins import BreadcrumbContextMixin
from .models import Consent
from .settings import CONSENT_CONTROL_AUTHORITY, CONSENT_SIGNATURE_LOCATION


class IndexView(BreadcrumbContextMixin, TemplateView):
    """Index view of the consent app."""

    template_name = "consent/index.html"
    breadcrumb_current = _("Consent")

    def get_context_data(self, **kwargs):  # noqa: D102
        context = super().get_context_data(**kwargs)
        context["entities"] = self.request.user.get_entities()

        return context


class ConsentFormView(BreadcrumbContextMixin, FormView):
    """Updates the status of consents."""

    template_name = "consent/manage.html"
    form_class = ConsentForm

    breadcrumb_links = [
        {"url": reverse("consent:index"), "title": _("Consent")},
    ]
    breadcrumb_current = _("Manage Consents")

    def form_valid(self, form):
        """Update the consent status.

        Bulk update of the consent status:
        - validated consents are set to VALIDATED
        - infers AWAITING consents by comparing initial consents
        and user VALIDATED consents, and sets them to waiting.
        """
        selected_ids: list[str] = self.request.POST.getlist("status")

        self._bulk_update_consent(selected_ids, VALIDATED)  # type: ignore
        awaiting_ids = self._get_awaiting_ids(selected_ids)
        self._bulk_update_consent(awaiting_ids, AWAITING)  # type: ignore

        messages.success(self.request, _("Consents updated."))

        return redirect(reverse("consent:index"))

    def get_context_data(self, **kwargs):
        """Add the user's entities to the context.

        Adds to the context the entities that the user has permission to access.
        If a slug is provided, adds the entity corresponding to the slug.
        """
        context = super().get_context_data(**kwargs)
        context["control_authority"] = CONSENT_CONTROL_AUTHORITY
        context["entities"] = self._get_entities()
        context["signature_location"] = CONSENT_SIGNATURE_LOCATION
        context["mailto"] = CONTACT_EMAIL
        return context

    def _get_entities(self) -> list:
        """Return a list of entities or specific entity if slug is provided."""
        slug: str | None = self.kwargs.get("slug", None)
        user: DashboardUser = self.request.user  # type: ignore

        if slug:
            entity: Entity = get_object_or_404(Entity, slug=slug)
            if not user.can_validate_entity(entity):
                raise PermissionDenied
            return [entity]
        else:
            return list(user.get_entities())

    def _bulk_update_consent(self, ids: list[str], status: str) -> int:
        """Bulk update of the consent status for a given status and list of entities.

        Only `AWAITING` consents can be updated by users.
        """
        return (
            Consent.objects.filter(id__in=ids, status=AWAITING)
            .filter(
                Q(delivery_point__entity__users=self.request.user)
                | Q(delivery_point__entity__proxies__users=self.request.user)
            )
            .update(
                status=status,
                created_by=self.request.user,
                updated_at=timezone.now(),
            )
        )

    def _get_awaiting_ids(self, validated_ids: list[str]) -> list[str]:
        """Get the list of the non-selected IDs (awaiting IDs)."""
        if any(not isinstance(item, str) for item in validated_ids):
            raise ValueError("validated_ids must be a list of strings")

        return [
            str(c.id)
            for e in self._get_entities()
            for c in e.get_consents()
            if str(c.id) not in validated_ids
        ]
