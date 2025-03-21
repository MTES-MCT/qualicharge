"""Consent management duplicate consents commands."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.consent.models import Consent
from apps.consent.utils import consent_end_date
from apps.core.management.commands.base_command import DashboardBaseCommand


class Command(DashboardBaseCommand):
    """Command for duplicating expiring consents."""

    help = __doc__

    def handle(self, *args, **options):
        """Executes the command for duplicating expiring consents."""
        self.duplicate_expiring_consents()

    def duplicate_expiring_consents(self):
        """Duplicate expiring consents.

        date de debut du nouveau consentement = date de fin du consentement précédent
        date de fin du nouveau consentement =
            si CONSENT_UPCOMING_DAYS_LIMIT => consent_end_date() + 1 year
            sinon => consent_end_date()
        """
        limit_date = timezone.now() + timedelta(
            days=settings.CONSENT_UPCOMING_DAYS_LIMIT
        )

        # Récupérer les consentements qui expirent dans x jours
        # todo: vérifier selon heure
        expiring_consents = list(Consent.active_objects.filter(end__date=limit_date))

        # Définir les nouvelles dates pour les duplications
        next_year_end = consent_end_date()
        if not settings.CONSENT_UPCOMING_DAYS_LIMIT:
            # todo revoir year + 1
            next_year_end += next_year_end.replace(next_year_end.year + 1)

        new_consents = []
        for consent in expiring_consents:
            # Vérifier si un consentement identique existe déjà pour l'année suivante
            if not Consent.objects.filter(
                delivery_point=consent.delivery_point,
                id_station_itinerance=consent.id_station_itinerance,
                station_name=consent.station_name,
                provider_assigned_id=consent.provider_assigned_id,
                start=consent.end,
                end=next_year_end,
            ).exists():
                # Ajouter un nouveau consentement s'il n'existe pas déjà
                new_consents.append(
                    Consent(
                        delivery_point=consent.delivery_point,
                        id_station_itinerance=consent.id_station_itinerance,
                        station_name=consent.station_name,
                        provider_assigned_id=consent.provider_assigned_id,
                        start=consent.end,
                        end=next_year_end,
                    )
                )

        # Insérer les nouveaux consentements en masse
        if new_consents:
            with transaction.atomic():
                Consent.objects.bulk_create(new_consents)
