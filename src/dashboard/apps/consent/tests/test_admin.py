"""Dashboard consent admin tests."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from apps.consent.admin import ConsentAdmin
from apps.consent.models import Consent


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
