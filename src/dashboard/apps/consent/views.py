"""Dashboard consent app views."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import TextField
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy as reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from apps.core.models import Entity

from . import AWAITING, VALIDATED
from .models import Consent


class IndexView(TemplateView):
    """Index view of the consent app."""

    template_name = "consent/index.html"

    def get_context_data(self, **kwargs):
        """Add custom context to the view."""
        context = super().get_context_data(**kwargs)
        context["entities"] = self.request.user.get_entities()

        context["breadcrumb_data"] = {
            "current": _("Consent"),
        }
        return context


def consent_form_view(request, slug=None):
    """Manage consent forms.

    This function performs the following actions:
    - Retrieves the entity associated with the given slug, if provided.
    - Fetches consents awaiting validation for the current user and the specified
    entity.
    - If a POST request is received, updates the consent status to either VALIDATED
    or AWAITING based on user selections and existing data.
    """
    template_name = "consent/manage.html"

    entities = []
    if slug:
        entity = get_object_or_404(Entity, slug=slug)
        if not request.user.can_validate_entity(entity):
            raise PermissionDenied
        entities.append(entity)
    else:
        entities = request.user.get_entities()

    if request.POST:
        selected_ids = request.POST.getlist("status")
        update_consent_status(request.user, entities, selected_ids)

        messages.success(request, _("Consents updated."))
        return redirect(reverse("consent:index"))

    breadcrumb_data = {
        "links": [
            {"url": reverse("consent:index"), "title": _("Consent")},
        ],
        "current": _("Manage Consents"),
    }

    return render(
        request=request,
        template_name=template_name,
        context={"entities": entities, "breadcrumb_data": breadcrumb_data},
    )


def update_consent_status(user, entities, selected_ids):
    """Updates the status of consents.."""

    def _bulk_update_consent(ids: list[str], status: str):
        """Bulk update of the consent status for a given status and list of entities."""
        Consent.objects.filter(id__in=ids).update(
            status=status,
            created_by=user,
            updated_at=timezone.now(),
        )

    def _get_awaiting_ids(entities, ids):
        """Get the a list of the non selected ids (awaiting ids)."""
        base_ids = []
        for entity in entities:
            base_ids.extend(
                list(
                    entity.get_consents()
                    .annotate(str_id=Cast("id", output_field=TextField()))
                    .values_list("str_id", flat=True)
                )
            )
        return list(set(base_ids) - set(ids))

    _bulk_update_consent(selected_ids, VALIDATED)
    awaiting_ids = _get_awaiting_ids(entities, selected_ids)
    _bulk_update_consent(awaiting_ids, AWAITING)
