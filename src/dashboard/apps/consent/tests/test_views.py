"""Dashboard consent views tests."""

import datetime
import uuid
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.urls import reverse

from apps.auth.factories import UserFactory
from apps.consent import AWAITING, REVOKED, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.consent.models import Consent
from apps.consent.views import ConsentFormView
from apps.core.factories import DeliveryPointFactory, EntityFactory

FORM_CLEANED_DATA = {
    "is_authoritative_signatory": True,
    "allows_measurements": True,
    "allows_daily_index_readings": True,
    "allows_max_daily_power": True,
    "allows_load_curve": True,
    "allows_technical_contractual_data": True,
    "consent_agreed": True,
    "signed_at": "2025-03-01",
}


@pytest.mark.django_db
def test_bulk_update_consent_status_without_ids(rf):
    """Test no status is updated if no ID is passed."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    size = 4
    DeliveryPointFactory.create_batch(size)

    # check data before update
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))

    # bulk update to VALIDATED of… nothing, and check 0 record have been updated.
    mock_form = MagicMock()
    mock_form.cleaned_data = FORM_CLEANED_DATA
    assert view._bulk_update_consent([], VALIDATED, mock_form) == 0

    # and checks that the data has not changed after the update.
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))


@pytest.mark.django_db
def test_bulk_update_consent_status(rf):  # noqa: PLR0915
    """Test all consents are correctly updated."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create entity for the user and consents for the entity
    size = 3
    entity = EntityFactory(users=(user,))
    DeliveryPointFactory.create_batch(size, entity=entity)
    ids = list(Consent.objects.values_list("id", flat=True))

    # check data before update
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))

    mock_form = MagicMock()
    mock_form.cleaned_data = FORM_CLEANED_DATA

    # bulk update to VALIDATED, and check all records have been updated.
    assert view._bulk_update_consent(ids, VALIDATED, mock_form) == size

    # and checks that the data has changed to VALIDATED after the update.
    assert all(c == VALIDATED for c in Consent.objects.values_list("status", flat=True))
    for c in Consent.objects.all():
        assert c.signed_at == datetime.datetime(
            2025, 3, 1, 0, 0, tzinfo=datetime.timezone.utc
        )
        assert c.signature_location == settings.CONSENT_SIGNATURE_LOCATION

        # check company data are present in company json field
        assert c.company is not None
        assert c.company["company_type"] == entity.company_type
        assert c.company["name"] == entity.name
        assert c.company["legal_form"] == entity.legal_form
        assert c.company["trade_name"] == entity.trade_name
        assert c.company["siret"] == entity.siret
        assert c.company["naf"] == entity.naf
        assert c.company["address_1"] == entity.address_1
        assert c.company["address_2"] == entity.address_2
        assert c.company["zip_code"] == entity.address_zip_code
        assert c.company["city"] == entity.address_city

        # check company representative data are present
        assert c.company is not None
        assert c.company_representative["firstname"] == user.first_name
        assert c.company_representative["lastname"] == user.last_name
        assert c.company_representative["email"] == user.email

        # check control authority data are presents
        assert c.control_authority is not None
        control_authority = settings.CONSENT_CONTROL_AUTHORITY
        assert c.control_authority["name"] == control_authority["name"]
        assert (
            c.control_authority["represented_by"] == control_authority["represented_by"]
        )
        assert c.control_authority["email"] == control_authority["email"]
        assert c.control_authority["address_1"] == control_authority["address_1"]
        assert c.control_authority["address_2"] == control_authority["address_2"]
        assert c.control_authority["zip_code"] == control_authority["zip_code"]
        assert c.control_authority["city"] == control_authority["city"]

        # check authorizations (boolean fields)
        assert c.is_authoritative_signatory is True
        assert c.allows_measurements is True
        assert c.allows_max_daily_power is True
        assert c.allows_load_curve is True
        assert c.allows_technical_contractual_data is True

    # bulk update from VALIDATED to AWAITING: no data must be updated.
    assert view._bulk_update_consent(ids, AWAITING, mock_form) == 0
    # and checks that the status has not changed after the update.
    assert all(c == VALIDATED for c in Consent.objects.values_list("status", flat=True))

    # bulk update from VALIDATED to REVOKED: no data must be updated.
    assert view._bulk_update_consent(ids, REVOKED, mock_form) == 0
    # and checks that the status has not changed after the update.
    assert all(c == VALIDATED for c in Consent.objects.values_list("status", flat=True))


@pytest.mark.django_db
def test_bulk_update_consent_status_with_fake_id(rf):
    """Test update with wrong ID in list of IDs to update."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create entity for the user and consents for the entity
    size = 3
    entity = EntityFactory(users=(user,))
    DeliveryPointFactory.create_batch(size, entity=entity)
    ids = list(Consent.objects.values_list("id", flat=True))

    # add a fake ID to the IDs to update
    ids.append("fa62cf1d-c510-498a-b428-fdf72fa35651")

    # check data before update
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))

    # bulk update to VALIDATED,
    # and check all records have been updated except the fake id.
    mock_form = MagicMock()
    mock_form.cleaned_data = FORM_CLEANED_DATA
    assert view._bulk_update_consent(ids, VALIDATED, mock_form) == size

    # and checks that the data has changed to VALIDATED after the update.
    assert all(c == VALIDATED for c in Consent.objects.values_list("status", flat=True))


@pytest.mark.django_db
def test_bulk_update_consent_without_user_perms(rf):
    """Test the update of consents for which the user does not have the rights."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create entity for the user and consents for the entity
    size = 3
    entity = EntityFactory(users=(user,))
    DeliveryPointFactory.create_batch(size, entity=entity)
    ids = list(Consent.objects.values_list("id", flat=True))

    # create wrong consent
    wrong_user = UserFactory()
    wrong_entity = EntityFactory(users=(wrong_user,))
    wrong_consent = ConsentFactory(delivery_point__entity=wrong_entity)

    # add wrong_id to IDs
    ids.append(wrong_consent.id)
    assert len(ids) == size + 1
    assert wrong_consent.id in ids

    # check data before update
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))

    # bulk update to VALIDATED,
    # and check all records have been updated except the wrong ID.
    mock_form = MagicMock()
    mock_form.cleaned_data = FORM_CLEANED_DATA
    assert view._bulk_update_consent(ids, VALIDATED, mock_form) == size

    # and checks that the data has changed to VALIDATED after the update.
    assert all(
        c == VALIDATED
        for c in Consent.objects.filter(delivery_point__entity=entity).values_list(
            "status", flat=True
        )
    )
    assert all(
        c == AWAITING
        for c in Consent.objects.filter(
            delivery_point__entity=wrong_entity
        ).values_list("status", flat=True)
    )


@pytest.mark.django_db
def test_get_awaiting_ids_with_bad_parameters(rf):
    """Test get_awaiting_ids() with bad parameters raise exception."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create a list of UUID instead of str
    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    # check _get_awaiting_ids() raise exception
    # (IDs must be a list of string not of UUID)
    with pytest.raises(ValueError):
        view._get_awaiting_ids(validated_ids=ids)


@pytest.mark.django_db
def test_get_awaiting_ids(rf):
    """Test getting of awaiting IDs inferred from validated consents."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create entity for the user and consents for the entity
    size = 3
    entity = EntityFactory(users=(user,))
    DeliveryPointFactory.create_batch(size, entity=entity)
    ids = [
        str(c.id) for c in Consent.active_objects.filter(delivery_point__entity=entity)
    ]

    # removes one `id` from the list `ids`,
    # this is the one we must find with _get_awaiting_ids()
    id_not_include = ids.pop()
    assert len(ids) == size - 1

    # check awaiting id is the expected
    awaiting_ids = view._get_awaiting_ids(validated_ids=ids)
    assert len(awaiting_ids) == 1
    assert id_not_include in awaiting_ids


@pytest.mark.django_db
def test_templates_render_with_entities_without_consents(rf):
    """Test the templates without consents are rendered with expected content."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # check the context
    context = view.get_context_data()
    assert context["entities"] == [entity]

    # get response object
    response = view.dispatch(request)
    assert response.status_code == HTTPStatus.OK

    # force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    # the id of the global consent checkbox must be present in HTML
    expected = 'id="id_consent_agreed"'
    assert (expected in html) is True

    # no checkbox with name “status” should be present in the HTML
    not_expected = '<input type="checkbox" name="status"'
    assert (not_expected not in html) is True


@pytest.mark.django_db
def test_templates_render_html_content_with_consents(rf):
    """Test the HTML content of the templates with entities and consents."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # check the context
    context = view.get_context_data()
    assert context["entities"] == [entity]

    # create consents
    size = 3
    DeliveryPointFactory.create_batch(size, entity=entity)
    consents = Consent.objects.filter(delivery_point__entity=entity)

    # get response object
    response = view.dispatch(request)
    assert response.status_code == HTTPStatus.OK

    # and force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    assert (entity.name in html) is True
    assert all(str(dl.id) in html for dl in consents)


@pytest.mark.django_db
def test_form_post_empty(rf):
    """POST request without required field values will display error."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.post(reverse("consent:manage", kwargs={"slug": entity_name}), {})
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # Get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK

    html = rendered.content.decode()
    expected = 'id="checkboxes-error-message-error"'
    assert (expected in html) is True


@pytest.mark.django_db
def test_manage_url_redirect(client):
    """Test direct access to manage page is redirected to consent index page."""
    # create and connect user
    user = UserFactory()
    client.force_login(user)

    # Get response object
    response = client.get(reverse("consent:manage"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("consent:index")


@pytest.mark.django_db
def test_send_email_notification_populated(rf):
    """Test `_send_email` is sent."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    with patch("apps.consent.views.AnymailMessage") as mock_message:
        email_send_mock = mock_message.return_value.send
        view._send_email()

        email_config = settings.DASHBOARD_EMAIL_CONFIGS["consent_validation"]
        mock_message.assert_called_once_with(
            to=[user.email],
            template_id=email_config.get("template_id"),
            merge_data={
                user.email: {
                    "last_name": user.last_name,
                    "first_name": user.first_name,
                    "link": email_config.get("link"),
                }
            },
        )
        email_send_mock.assert_called_once()
