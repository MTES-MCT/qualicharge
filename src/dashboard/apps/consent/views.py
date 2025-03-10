"""Dashboard consent app views."""

import sentry_sdk
from anymail.exceptions import AnymailRequestsAPIError
from anymail.message import AnymailMessage
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy as reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, ListView, TemplateView

from apps.auth.models import DashboardUser
from apps.core.models import Entity
from apps.core.views import BaseView

from . import AWAITING, VALIDATED
from .forms import ConsentForm
from .models import Consent


class IndexView(BaseView, TemplateView):
    """Index view of the consent app."""

    template_name = "consent/index.html"
    breadcrumb_current = _("Consent")

    def get_context_data(self, **kwargs):
        """Add user's entities to the context."""
        context = super().get_context_data(**kwargs)
        context["entities"] = self.request.user.get_entities()
        context["has_awaiting_consent"] = any(
            entity.count_awaiting_consents() for entity in context["entities"]
        )
        context["has_validated_consent"] = any(
            entity.count_validated_consents() for entity in context["entities"]
        )

        return context


class ConsentFormView(BaseView, FormView):
    """Updates the status of consents."""

    ERROR_MESSAGE = _(
        "An error occurred while validating the form. "
        "Our team has been notified and will get back to you shortly."
    )

    template_name = "consent/manage.html"
    form_class = ConsentForm
    success_url = reverse("consent:index")

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

        try:
            self._bulk_update_consent(selected_ids, VALIDATED, form)  # type: ignore
            awaiting_ids = self._get_awaiting_ids(selected_ids)
            self._bulk_update_consent(awaiting_ids, AWAITING, form)  # type: ignore
        except ValidationError as e:
            sentry_sdk.capture_exception(e)
            form.add_error(None, self.ERROR_MESSAGE)
            return self.form_invalid(form)

        # send email notification to the user
        self._send_email()

        messages.success(self.request, _("Consents updated."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Add context data for the view."""
        context = super().get_context_data(**kwargs)
        context["control_authority"] = settings.CONSENT_CONTROL_AUTHORITY
        context["entity"] = self._get_entity()
        context["signature_location"] = settings.CONSENT_SIGNATURE_LOCATION

        return context

    def _get_entity(self) -> Entity:
        """Return the specific entity with the provided slug."""
        slug: str | None = self.kwargs.get("slug", None)
        user: DashboardUser = self.request.user  # type: ignore

        if not slug:
            raise Http404

        entity: Entity = get_object_or_404(Entity, slug=slug)
        if not user.can_validate_entity(entity):
            raise PermissionDenied
        return entity

    def _bulk_update_consent(
        self, ids: list[str], status: str, form: ConsentForm
    ) -> HttpResponse | int:
        """Bulk update of the consent status for a given status and list of entities.

        This method updates the consent statuses, and their related information:
        - company information,
        - control authority information,
        - company representative information,
        - form data,
        - date of signature,
        - signature location,

        Note: Only `AWAITING` consents can be updated by users.
        """
        # retrieve consents to update
        consents = (
            Consent.objects.filter(
                id__in=ids,
                status=AWAITING,
            )
            .filter(
                Q(delivery_point__entity__users=self.request.user)
                | Q(delivery_point__entity__proxies__users=self.request.user)
            )
            .select_related("delivery_point__entity")
        )

        # build consent object with validated fields to update
        update_objects = [
            self._build_consent_object(status, form.cleaned_data, consent)
            for consent in consents
        ]

        # and finally, bulk update the consents
        return Consent.objects.bulk_update(
            update_objects,
            fields=[
                "status",
                "created_by",
                "updated_at",
                "company",
                "control_authority",
                "company_representative",
                "is_authoritative_signatory",
                "allows_measurements",
                "allows_daily_index_readings",
                "allows_max_daily_power",
                "allows_load_curve",
                "allows_technical_contractual_data",
                "signed_at",
                "signature_location",
            ],
        )

    def _get_awaiting_ids(self, validated_ids: list[str]) -> list[str]:
        """Get the list of the non-selected IDs (awaiting IDs)."""
        if any(not isinstance(item, str) for item in validated_ids):
            raise ValueError("validated_ids must be a list of strings")

        entity = self._get_entity()
        return [
            str(c.id) for c in entity.get_consents() if str(c.id) not in validated_ids
        ]

    def _build_consent_object(
        self,
        status: str,
        form_values: dict,
        consent: Consent,
    ) -> Consent:
        """Builds and returns a `Consent` object with validated data.

        Parameters:
        - status (str): Consent status (e.g., “AWAITING”, “VALIDATED”).
        - form_values (dict): Validated data from the consent form.
        - control_authority (dict): Details about the control authority.
        - company_representative (dict): Information about the company representative.
        - consent (dict): Consent data, including the identifier, and the related
        entity information.
        """
        # Get related company data from consent
        consent_entity = consent.delivery_point.entity
        company_data = {
            "name": consent_entity.name,
            "company_type": consent_entity.company_type,
            "legal_form": consent_entity.legal_form,
            "trade_name": consent_entity.trade_name,
            "siret": consent_entity.siret,
            "naf": consent_entity.naf,
            "address_1": consent_entity.address_1,
            "address_2": consent_entity.address_2,
            "zip_code": consent_entity.address_zip_code,
            "city": consent_entity.address_city,
        }

        company_representative = {
            "firstname": self.request.user.first_name,  # type: ignore[union-attr]
            "lastname": self.request.user.last_name,  # type: ignore[union-attr]
            "email": self.request.user.email,  # type: ignore[union-attr]
        }

        # remove `consent_agreed` from `form_values`, which is not stored in db
        form_values_copy = form_values.copy()
        form_values_copy.pop("consent_agreed", None)

        # build a Consent object with all validated data
        return Consent(
            id=consent.id,
            status=status,
            created_by=self.request.user,  # type: ignore[misc]
            updated_at=timezone.now(),
            company=company_data,
            control_authority=settings.CONSENT_CONTROL_AUTHORITY,
            company_representative=company_representative,
            **form_values_copy,
            signature_location=settings.CONSENT_SIGNATURE_LOCATION,
        )

    def _send_email(self) -> None:
        """Send an email to the user for consent validation.

        This method constructs and sends an email using the Anymail library based on
        predefined configurations.
        It logs errors with Sentry and fails silently in case of API errors.
        The email contains user information and a link to return in the dashboard.

        Raises:
            AnymailRequestsAPIError: If an error occurs while sending the email.
        """
        user = self.request.user
        email_config = settings.DASHBOARD_EMAIL_CONFIGS["consent_validation"]

        email_data = {
            user.email: {  # type: ignore[union-attr]
                "last_name": user.last_name,  # type: ignore[union-attr]
                "first_name": user.first_name,  # type: ignore[union-attr]
                "link": email_config.get("link"),
            }
        }

        email = AnymailMessage(
            to=[
                user.email,  # type: ignore[union-attr]
            ],
            template_id=email_config.get("template_id"),
            merge_data=email_data,
        )

        try:
            email.send()
        except AnymailRequestsAPIError as e:
            # fail silently and send a sentry log
            sentry_sdk.capture_exception(e)
            return


class ValidatedConsentView(BaseView, ListView):
    """Validated consents view of the consent app."""

    context_object_name = "consents"
    template_name = "consent/validated.html"
    paginate_by = 50

    breadcrumb_links = [
        {"url": reverse("consent:index"), "title": _("Consent")},
    ]
    breadcrumb_current = _("Followed stations")

    def get_queryset(self):
        """Filter queryset to only return validated consents for the current user.

        Returns:
            QuerySet: A QuerySet of validated consents if the user has permission,
            and the slug is valid.

        Raises:
            PermissionDenied: If the user does not have permission to validate the
            entity.
        """
        slug: str | None = self.kwargs.get("slug", None)
        user: DashboardUser = self.request.user  # type: ignore

        entity: Entity = get_object_or_404(Entity, slug=slug)
        if not user.can_validate_entity(entity):
            raise PermissionDenied

        return entity.get_validated_consents()
