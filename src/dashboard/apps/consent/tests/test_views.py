"""Dashboard consent views tests."""

import uuid
from datetime import timedelta
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings as django_settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.auth.factories import UserFactory
from apps.consent import AWAITING, REVOKED, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.consent.models import Consent
from apps.consent.tests.conftest import FAKE_TIME
from apps.consent.views import (
    ConsentFormView,
    UpcomingConsentFormView,
    ValidatedConsentView,
)
from apps.core.factories import DeliveryPointFactory, EntityFactory
from apps.core.models import DeliveryPoint, Entity

FORM_CLEANED_DATA = {
    "contract_holder_name": "<NAME>",
    "contract_holder_email": "contact@domain.com",
    "contract_holder_phone": "+33.500000000",
    "is_authoritative_signatory": True,
    "allows_measurements": True,
    "allows_daily_index_readings": True,
    "allows_max_daily_power": True,
    "allows_load_curve": True,
    "allows_technical_contractual_data": True,
    "consent_agreed": True,
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
def test_bulk_update_consent_status(rf, patch_timezone_now):  # noqa: PLR0915
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
        assert c.signed_at == FAKE_TIME
        assert c.signature_location == django_settings.CONSENT_SIGNATURE_LOCATION

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
        control_authority = django_settings.CONSENT_CONTROL_AUTHORITY
        assert c.control_authority["name"] == control_authority["name"]
        assert (
            c.control_authority["represented_by"] == control_authority["represented_by"]
        )
        assert c.control_authority["email"] == control_authority["email"]
        assert c.control_authority["address_1"] == control_authority["address_1"]
        assert c.control_authority["address_2"] == control_authority["address_2"]
        assert c.control_authority["zip_code"] == control_authority["zip_code"]
        assert c.control_authority["city"] == control_authority["city"]

        # check contract holder data are presents
        assert c.contract_holder is not None
        assert c.contract_holder["name"] == FORM_CLEANED_DATA["contract_holder_name"]
        assert c.contract_holder["email"] == FORM_CLEANED_DATA["contract_holder_email"]
        assert c.contract_holder["phone"] == FORM_CLEANED_DATA["contract_holder_phone"]

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
def test_update_entity_with_valid_data(rf):
    """Test the update of an entity."""
    user = UserFactory()

    # create entity without contract holder data
    assert Entity.objects.count() == 0
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    assert Entity.objects.count() == 1
    assert entity.contract_holder_name is None
    assert entity.contract_holder_email is None
    assert entity.contract_holder_phone is None

    # Set up the view and the mock form
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user
    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    mock_form = MagicMock()
    mock_form.cleaned_data = FORM_CLEANED_DATA
    mock_form.is_valid()

    # Call _update_entity with the mock form
    updated_entity = view._update_entity(mock_form)

    # Verify that the entity fields have been updated
    assert (
        updated_entity.contract_holder_name == FORM_CLEANED_DATA["contract_holder_name"]
    )
    assert (
        updated_entity.contract_holder_email
        == FORM_CLEANED_DATA["contract_holder_email"]
    )
    assert (
        updated_entity.contract_holder_phone
        == FORM_CLEANED_DATA["contract_holder_phone"]
    )
    assert Entity.objects.count() == 1
    assert (
        Entity.objects.first().contract_holder_name
        == FORM_CLEANED_DATA["contract_holder_name"]
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
    view.setup(request, slug=entity_name)

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
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    # create consents for the entity
    size = 3
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
def test_get_entity_without_slug_raise_404(rf):
    """Test _get_entity() with slug=None raises Http404."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    with pytest.raises(Http404):
        view._get_entity()


@pytest.mark.django_db
def test_templates_render_with_entity_without_consents(rf):
    """Test the templates without consents are rendered with expected content."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    # check the context
    consents = entity.get_consents()
    assert consents.count() == 0
    context = view.get_context_data()
    assert context["entity"] == entity
    assert len(context["consents"]) == 0

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
def test_templates_render_html_content_with_consents(rf, settings):
    """Test the HTML content of the templates with entities and consents."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    # create consents
    size = 3
    DeliveryPointFactory.create_batch(size, entity=entity)

    # upcoming consent limit
    settings.CONSENT_UPCOMING_DAYS_LIMIT = 30

    # create upcoming consents in futur period (+30 days)
    dp = DeliveryPoint.objects.first()
    ConsentFactory(
        delivery_point=dp,
        created_by=user,
        status=AWAITING,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    # check the context
    assert Consent.objects.count() == size + 1
    consents = entity.get_consents()
    assert len(consents) == size

    context = view.get_context_data()
    assert context["entity"] == entity
    assert len(context["consents"]) == size
    for c, o in zip(context["consents"], consents, strict=True):
        assert c.id == o.id
        assert c.status == o.status
        assert c.delivery_point == o.delivery_point

    # get response object
    response = view.dispatch(request)
    assert response.status_code == HTTPStatus.OK

    # and force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    assert (entity.name in html) is True
    assert all(str(c.id) in html for c in consents)


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
    view.setup(request, slug=entity_name)

    # Get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK

    html = rendered.content.decode()
    expected = 'id="id_is_authoritative_signatory--message-error"'
    assert (expected in html) is True


@pytest.mark.django_db
def test_form_post_empty_contract_holder(rf):
    """POST request without required `contract holder` fields will display error."""
    user = UserFactory()

    # all mandatory are posted expected contract holder data
    posted_data = {
        "is_authoritative_signatory": True,
        "allows_measurements": True,
        "allows_daily_index_readings": True,
        "allows_max_daily_power": True,
        "allows_load_curve": True,
        "allows_technical_contractual_data": True,
        "consent_agreed": True,
    }

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.post(
        reverse("consent:manage", kwargs={"slug": entity_name}), posted_data
    )
    request.user = user

    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    # Get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK

    html = rendered.content.decode()
    expected = 'id="id_contract_holder_name--message-error"'
    assert (expected in html) is True

    # all mandatory are posted expected contract holder data email and phone.
    posted_data["contract_holder_name"] = "<NAME>"
    request = rf.post(
        reverse("consent:manage", kwargs={"slug": entity_name}), posted_data
    )
    request.user = user
    view.setup(request, slug=entity_name)
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK
    html = rendered.content.decode()
    expected = 'id="id_contract_holder_email--message-error"'
    assert (expected in html) is True

    # all mandatory are posted expected contract holder phone.
    posted_data["contract_holder_email"] = "test@domain.com"
    request = rf.post(
        reverse("consent:manage", kwargs={"slug": entity_name}), posted_data
    )
    request.user = user
    view.setup(request, slug=entity_name)
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK
    html = rendered.content.decode()
    expected = 'id="id_contract_holder_phone--message-error"'
    assert (expected in html) is True


@pytest.mark.django_db
def test_manage_url_without_slug_is_redirected(client):
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

        email_config = django_settings.DASHBOARD_EMAIL_CONFIGS["consent_validation"]
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


@pytest.mark.django_db
def test_get_validated_consents_raises_permission_denied(rf):
    """Test PermissionDenied is raised when the user does not have permission."""
    user = UserFactory()

    # create a consent without the declared user
    entity = EntityFactory()
    DeliveryPointFactory(entity=entity)

    request = rf.get(reverse("consent:validated", kwargs={"slug": entity.slug}))
    request.user = user

    view = ValidatedConsentView()
    view.request = request
    view.kwargs = {"slug": entity.slug}

    # the user has no perms to this consent
    with pytest.raises(PermissionDenied):
        view.get_queryset()


@pytest.mark.django_db
def test_get_validated_consents_return_queryset(rf):
    """Test _get_validated_consents returns the correct QuerySet."""
    user = UserFactory()

    # create and get 2 validated consents for the user
    entity = EntityFactory(users=(user,))
    dl1 = DeliveryPointFactory(entity=entity)
    dl2 = DeliveryPointFactory(entity=entity)
    consent1 = Consent.objects.get(delivery_point=dl1)
    consent2 = Consent.objects.get(delivery_point=dl2)
    for consent in Consent.objects.all():
        consent.status = VALIDATED
        consent.save()

    # and and get an awaiting consent
    dl3 = DeliveryPointFactory(entity=entity)
    consent3 = Consent.objects.get(delivery_point=dl3)

    # check the number of validated consents
    expected_validated_consent = 2
    assert (
        Consent.objects.filter(status=VALIDATED).count() == expected_validated_consent
    )

    request = rf.get(reverse("consent:validated", kwargs={"slug": entity.slug}))
    request.user = user
    view = ValidatedConsentView()
    view.request = request
    view.kwargs = {"slug": entity.slug}

    # we expected to retrieve only the 2 VALIDATED consents in the result
    result = view.get_queryset()
    assert len(result) == expected_validated_consent

    consent_ids = [consent.id for consent in result]
    assert consent1.id in consent_ids
    assert consent2.id in consent_ids
    assert consent3.id not in consent_ids


@pytest.mark.django_db
def test_validated_url_without_slug_is_redirected(client):
    """Test direct access to validated url is redirected to consent index page."""
    # create and connect user
    user = UserFactory()
    client.force_login(user)

    # Get response object
    response = client.get(reverse("consent:validated"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("consent:index")


@pytest.mark.django_db
def test_display_form_if_entity_contract_holder_is_not_set(rf):
    """Test the form is displayed if the entity has no contract holder data."""
    user = UserFactory()

    # create entity without contract holder data
    assert Entity.objects.count() == 0
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    assert Entity.objects.count() == 1
    assert entity.contract_holder_name is None
    assert entity.contract_holder_email is None
    assert entity.contract_holder_phone is None

    # Set up the view
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    # Get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK

    html = rendered.content.decode()
    expected_name = '<input type="text" name="contract_holder_name"'
    expected_email = '<input type="email" name="contract_holder_email"'
    expected_phone = '<input type="text" name="contract_holder_phone"'
    assert (expected_name in html) is True
    assert (expected_email in html) is True
    assert (expected_phone in html) is True
    not_expected = 'id="table-contract-holder-component"'
    assert (not_expected not in html) is True


@pytest.mark.django_db
def test_display_table_if_entity_contract_holder_is_set(rf):
    """Test the table is displayed if the entity has contract holder data."""
    user = UserFactory()

    # create entity without contract holder data
    assert Entity.objects.count() == 0
    entity_name = "entity-1"
    entity = EntityFactory(
        users=(user,),
        name=entity_name,
        contract_holder_name="John Doe",
        contract_holder_email="contact@domain.com",
        contract_holder_phone="+33.1234567890",
    )
    assert Entity.objects.count() == 1
    assert entity.contract_holder_name == "John Doe"
    assert entity.contract_holder_email == "contact@domain.com"
    assert entity.contract_holder_phone == "+33.1234567890"

    # Set up the view
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = ConsentFormView()
    view.setup(request, slug=entity_name)

    # Get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    assert response.status_code == HTTPStatus.OK

    html = rendered.content.decode()
    expected_id = 'id="table-contract-holder-component"'
    expected_name = '<input type="hidden" name="contract_holder_name"'
    expected_email = '<input type="hidden" name="contract_holder_email"'
    expected_phone = '<input type="hidden" name="contract_holder_phone"'
    assert (expected_id in html) is True
    assert (expected_name in html) is True
    assert (expected_email in html) is True
    assert (expected_phone in html) is True


@pytest.mark.django_db
def test_upcoming_consent_form_get_context_data(rf):
    """Test the upcoming consent form context data without consents."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage", kwargs={"slug": entity_name}))
    request.user = user

    view = UpcomingConsentFormView()
    view.setup(request, slug=entity_name)

    # Test without consents
    # check the context
    consents = entity.get_upcoming_consents()
    assert consents.count() == 0
    context = view.get_context_data()
    assert context["entity"] == entity
    assert len(context["consents"]) == 0

    # Test with consents
    # create consents
    size = 3
    DeliveryPointFactory.create_batch(size, entity=entity)

    # upcoming consent limit
    django_settings.CONSENT_UPCOMING_DAYS_LIMIT = 30

    # create upcoming consents in futur period (+30 days)
    dp = DeliveryPoint.objects.first()
    ConsentFactory(
        delivery_point=dp,
        created_by=user,
        status=AWAITING,
        start=timezone.now() + timedelta(days=30),
        end=timezone.now() + timedelta(days=90),
    )

    # check the context
    assert Consent.objects.count() == size + 1
    upcoming_consents = entity.get_upcoming_consents()
    assert len(upcoming_consents) == 1

    context = view.get_context_data()
    assert context["entity"] == entity
    assert len(context["consents"]) == 1
    for c, o in zip(context["consents"], upcoming_consents, strict=True):
        assert c.id == o.id
        assert c.status == o.status
        assert c.delivery_point == o.delivery_point


@pytest.mark.django_db
def test_upcoming_consent_form_get_awaiting_ids_with_bad_parameters(rf):
    """Test get_awaiting_ids() with bad parameters raise exception."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage-upcoming", kwargs={"slug": entity_name}))
    request.user = user

    view = UpcomingConsentFormView()
    view.setup(request, slug=entity_name)

    # create a list of UUID instead of str
    ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

    # check _get_awaiting_ids() raise exception
    # (IDs must be a list of string not of UUID)
    with pytest.raises(ValueError):
        view._get_awaiting_ids(validated_ids=ids)


@pytest.mark.django_db
def test_upcoming_consent_form_get_awaiting_ids(rf):
    """Test getting of awaiting IDs inferred from validated consents."""
    user = UserFactory()

    # create entity
    entity_name = "entity-1"
    entity = EntityFactory(users=(user,), name=entity_name)
    request = rf.get(reverse("consent:manage-upcoming", kwargs={"slug": entity_name}))
    request.user = user

    view = UpcomingConsentFormView()
    view.setup(request, slug=entity_name)

    # create consents for the entity
    assert Consent.objects.count() == 0
    size = 3
    DeliveryPointFactory.create_batch(size, entity=entity)
    assert Consent.objects.count() == size

    # upcoming consent limit
    django_settings.CONSENT_UPCOMING_DAYS_LIMIT = 30

    # create upcoming consents in futur period (+30 days)
    for dp in DeliveryPoint.objects.all():
        ConsentFactory(
            delivery_point=dp,
            created_by=user,
            status=AWAITING,
            start=timezone.now() + timedelta(days=30),
            end=timezone.now() + timedelta(days=90),
        )
    upcoming_size = 3
    assert Consent.objects.count() == size + upcoming_size

    ids = [
        str(c.id)
        for c in Consent.upcoming_objects.filter(delivery_point__entity=entity)
    ]
    assert len(ids) == upcoming_size

    # removes one `id` from the list `ids`,
    # this is the one we must find with _get_awaiting_ids()
    id_not_include = ids.pop()
    assert len(ids) == size - 1

    # check awaiting id is the expected
    awaiting_ids = view._get_awaiting_ids(validated_ids=ids)
    assert len(awaiting_ids) == 1
    assert id_not_include in awaiting_ids
