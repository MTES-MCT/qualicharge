"""Dashboard consent admin tests."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from apps.auth.factories import AdminUserFactory
from apps.consent import AWAITING, REVOKED, VALIDATED
from apps.consent.admin import ConsentAdmin
from apps.consent.models import Consent
from apps.consent.tests.conftest import FAKE_TIME
from apps.core.factories import DeliveryPointFactory


@pytest.mark.django_db
def test_admin_manager_name(rf):
    """Tests the name of the manager used by the Django admin to retrieve objects.

    For the Django admin, the manager used must be the default django manager
    (`objects`) and not a custom manager, which could lead to an unwanted loss of
    display of data.
    """
    # Initialize admin
    site = AdminSite()
    admin = ConsentAdmin(Consent, site)

    # Request admin consent
    request = rf.get(reverse("admin:qcd_consent_consent_changelist"))

    # Get the queryset used by admin
    queryset = admin.get_queryset(request)

    # The manager name must be the default Django manager: `objects`.
    manager_name = queryset.model._default_manager.name
    assert manager_name == "objects"


@pytest.mark.django_db
def test_make_revoked_action(client, patch_timezone_now):
    """Tests the 'make_revoked' action for ConsentAdmin."""
    # Initialize admin user
    admin_user = AdminUserFactory()

    # create a consent
    assert Consent.objects.count() == 0
    DeliveryPointFactory()
    assert Consent.objects.count() == 1

    # Post action with selected consent
    consent = Consent.objects.first()
    assert consent.status == AWAITING
    data = {
        "action": "make_revoked",
        "_selected_action": [
            consent.id,
        ],
    }
    client.force_login(admin_user)
    client.post(reverse("admin:qcd_consent_consent_changelist"), data)

    consent.refresh_from_db()
    assert consent.status == REVOKED
    assert consent.revoked_at == FAKE_TIME
    assert consent.updated_at == FAKE_TIME


@pytest.mark.django_db
def test_make_awaiting_action(client, patch_timezone_now):
    """Tests the 'make_awaiting' action for ConsentAdmin."""
    # Initialize admin user
    admin_user = AdminUserFactory()

    # create a consent
    assert Consent.objects.count() == 0
    DeliveryPointFactory()
    assert Consent.objects.count() == 1

    # Select and update consent status to AWAITING
    consent = Consent.objects.first()
    consent.status = VALIDATED
    consent.save()
    assert consent.status == VALIDATED

    # Post action with selected consent
    data = {
        "action": "make_awaiting",
        "_selected_action": [
            consent.id,
        ],
    }
    client.force_login(admin_user)
    client.post(reverse("admin:qcd_consent_consent_changelist"), data)

    consent.refresh_from_db()
    assert consent.status == AWAITING
    assert consent.revoked_at is None
    assert consent.updated_at == FAKE_TIME
