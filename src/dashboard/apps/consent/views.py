"""Dashboard consent app views."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import F, Q
from django.db.models.functions import JSONObject
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy as reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from apps.core.models import Entity

from ..auth.models import DashboardUser
from . import AWAITING, VALIDATED
from .forms import ConsentForm
from .mixins import BreadcrumbContextMixin
from .models import Consent
from .settings import CONSENT_DONE_AT
from .utils import get_validate_company_representative, get_validate_control_authority


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

        self._bulk_update_consent(selected_ids, VALIDATED, form)  # type: ignore
        awaiting_ids = self._get_awaiting_ids(selected_ids)
        self._bulk_update_consent(awaiting_ids, AWAITING, form)  # type: ignore

        messages.success(self.request, _("Consents updated."))

        return redirect(reverse("consent:index"))

    def get_context_data(self, **kwargs):
        """Add the user's entities to the context.

        Adds to the context the entities that the user has permission to access.
        If a slug is provided, adds the entity corresponding to the slug.
        """
        context = super().get_context_data(**kwargs)
        context["entities"] = self._get_entities()
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

    def _bulk_update_consent(self, ids: list[str], status: str, form: ConsentForm) -> int:
        """Bulk update of the consent status for a given status and list of entities.

        Only `AWAITING` consents can be updated by users.
        """
        # todo: try/except => admin log + user message
        control_authority = get_validate_control_authority()
        company_representative = get_validate_company_representative(self.request.user)

        # todo: ne fonctionne pas "Joined field references are not permitted in this query",
        #  solution = découper la récupération de company_json ?
        consents = (
            Consent.objects.filter(
                id__in=ids,
                status=AWAITING,
            )
            .filter(
                Q(delivery_point__entity__users=self.request.user) |
                Q(delivery_point__entity__proxies__users=self.request.user)
            )
            .annotate(
                company_json=JSONObject(
                    name=F('delivery_point__entity__name'),
                    company_type=F('delivery_point__entity__company_type'),
                    legal_form=F('delivery_point__entity__legal_form'),
                    trade_name=F('delivery_point__entity__trade_name'),
                    siret=F('delivery_point__entity__siret'),
                    naf=F('delivery_point__entity__naf'),
                    address=JSONObject(
                        line_1=F('delivery_point__entity__address_1'),
                        line_2=F('delivery_point__entity__address_2'),
                        zip_code=F('delivery_point__entity__address_zip_code'),
                        city=F('delivery_point__entity__address_city'),
                    ),
                )
            )
        )

        consents.update(
            status=status,
            created_by=self.request.user,
            updated_at=timezone.now(),
            company=F('company_json'),  # Utiliser l'annotation dans la mise à jour
            control_authority=control_authority,
            company_representative=company_representative,
            signed_at=timezone.now(),
            done_at=CONSENT_DONE_AT,
        )

        return consents

        # return (
        #     Consent.objects.filter(id__in=ids, status=AWAITING)
        #     .filter(
        #         Q(delivery_point__entity__users=self.request.user)
        #         | Q(delivery_point__entity__proxies__users=self.request.user)
        #     )
        #     .update(
        #         status=status,
        #         created_by=self.request.user,
        #         updated_at=timezone.now(),
        #
        #         # Contractual fields of the company
        #         # Fields populated with data from the linked entity.
        #         company=JSONObject(
        #             name=F('delivery_point__entity__name'),
        #             company_type=F('delivery_point__entity__company_type'),
        #             legal_form=F('delivery_point__entity__legal_form'),
        #             trade_name=F('delivery_point__entity__trade_name'),
        #             siret=F('delivery_point__entity__siret'),
        #             naf=F('delivery_point__entity__naf'),
        #             address=JSONObject(
        #                 line_1=F('delivery_point__entity__address_1'),
        #                 line_2=F('delivery_point__entity__address_2'),
        #                 zip_code=F('delivery_point__entity__zip_code'),
        #                 city=F('delivery_point__entity__town'),
        #             ),
        #         ),
        #
        #         # Contractual fields of the control authority
        #         # Fields populated via `settings.CONSENT_CONTROL_AUTHORITY`.
        #         control_authority = control_authority,
        #
        #         # Contractual fields of the company representative
        #         # Fields populated with the current user data.
        #         company_representative=company_representative,
        #
        #         # # Fields populated via the consent form
        #         # is_authorized_signatory=form.cleaned_data["is_authorized_signatory"],
        #         # allows_measurements=form.cleaned_data["allows_measurements"],
        #         # allows_daily_index_readings=form.cleaned_data[
        #         #     "allows_daily_index_readings"],
        #         # allows_max_daily_power=form.cleaned_data["allows_max_daily_power"],
        #         # allows_load_curve=form.cleaned_data["allows_load_curve"],
        #         # allows_technical_contractual_data=form.cleaned_data[
        #         #     "allows_technical_contractual_data"],
        #         signed_at=timezone.now(),
        #         done_at=CONSENT_DONE_AT,
        #     )
        # )

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
