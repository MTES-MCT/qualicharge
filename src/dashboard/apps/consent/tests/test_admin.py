"""Dashboard consent admin tests."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from apps.auth.factories import AdminUserFactory
from apps.consent import AWAITING, REVOKED
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
def test_has_delete_permission_false_for_existing_object(rf):
    """Test that the has_delete_permission disallows deletion of an existing object."""
    # Initialize admin
    admin = ConsentAdmin(Consent, AdminSite())
    request = rf.get(reverse("admin:qcd_consent_consent_changelist"))

    # create a consent
    assert Consent.objects.count() == 0
    DeliveryPointFactory()
    assert Consent.objects.count() == 1

    consent = Consent.objects.first()
    assert admin.has_delete_permission(request, obj=consent) is False


@pytest.mark.django_db
def test_has_delete_permission_false_for_none_object(rf):
    """Test has_delete_permission disallows deletion when no object is passed (None)."""
    # Initialize admin
    admin = ConsentAdmin(Consent, AdminSite())
    request = rf.get(reverse("admin:qcd_consent_consent_changelist"))
    assert admin.has_delete_permission(request, obj=None) is False
