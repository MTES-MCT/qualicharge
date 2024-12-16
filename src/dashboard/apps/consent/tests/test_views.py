"""Dashboard consent views tests."""

import uuid
from http import HTTPStatus

import pytest
from django.urls import reverse

from apps.auth.factories import UserFactory
from apps.consent import AWAITING, VALIDATED
from apps.consent.factories import ConsentFactory
from apps.consent.models import Consent
from apps.consent.views import ConsentFormView
from apps.core.factories import DeliveryPointFactory, EntityFactory


@pytest.mark.django_db
def test_bulk_update_consent_status_without_ids(rf):
    """Test no status is updated if no ID is passed."""
    request = rf.get(reverse("consent:manage"))
    request.user = UserFactory()

    view = ConsentFormView()
    view.setup(request)

    size = 4
    DeliveryPointFactory.create_batch(size)

    # check data before update
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))

    # bulk update to VALIDATED of… nothing, and check 0 record have been updated.
    assert view._bulk_update_consent([], VALIDATED) == 0

    # and checks that the data has not changed after the update.
    assert all(c == AWAITING for c in Consent.objects.values_list("status", flat=True))


@pytest.mark.django_db
def test_bulk_update_consent_status(rf):
    """Test all consents are correctly updated."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
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

    # bulk update to VALIDATED, and check all records have been updated.
    assert view._bulk_update_consent(ids, VALIDATED) == size

    # and checks that the data has changed to VALIDATED after the update.
    assert all(c == VALIDATED for c in Consent.objects.values_list("status", flat=True))


@pytest.mark.django_db
def test_bulk_update_consent_status_with_fake_id(rf):
    """Test update with wrong ID in list of IDs to update."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
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
    assert view._bulk_update_consent(ids, VALIDATED) == size

    # and checks that the data has changed to VALIDATED after the update.
    assert all(c == VALIDATED for c in Consent.objects.values_list("status", flat=True))


@pytest.mark.django_db
def test_bulk_update_consent_without_user_perms(rf):
    """Test the update of consents for which the user does not have the rights."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
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
    assert view._bulk_update_consent(ids, VALIDATED) == size

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

    request = rf.get(reverse("consent:manage"))
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

    request = rf.get(reverse("consent:manage"))
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
def test_templates_render_without_entities(rf):
    """Test the templates are rendered without entities, and with expected content."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # check the context
    context = view.get_context_data()
    assert context["entities"] == []

    # Get response object
    response = view.dispatch(request)
    assert response.status_code == HTTPStatus.OK

    # force template rendering
    rendered = response.render()
    html = rendered.content.decode()

    # the id of the global consent checkbox shouldn't be present in HTML
    not_expected = 'id="id_consent_agreed"'
    assert (not_expected not in html) is True

    # checkbox with name “status” shouldn't be present in the HTML
    not_expected = '<input type="checkbox" name="status"'
    assert (not_expected not in html) is True


@pytest.mark.django_db
def test_templates_render_with_entities_without_consents(rf):
    """Test the templates without consents are rendered with expected content."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create entity
    entity = EntityFactory(users=(user,))

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
def test_templates_render_with_slug(rf):
    """Accessing the form with a slug must initialize the entity in the context."""
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


@pytest.mark.django_db
def test_templates_render_html_content_with_consents(rf):
    """Test the HTML content of the templates with entities and consents."""
    user = UserFactory()

    request = rf.get(reverse("consent:manage"))
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # create entity
    size = 3
    entity = EntityFactory(users=(user,))
    DeliveryPointFactory.create_batch(size, entity=entity)
    consents = Consent.objects.filter(delivery_point__entity=entity)

    # get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    html = rendered.content.decode()

    assert (entity.name in html) is True
    assert all(str(dl.id) in html for dl in consents)


@pytest.mark.django_db
def test_form_post_empty(rf):
    """POST request without required field values will display error."""
    user = UserFactory()
    EntityFactory(users=(user,))

    request = rf.post(reverse("consent:manage"), {})
    request.user = user

    view = ConsentFormView()
    view.setup(request)

    # Get response object and force template rendering
    response = view.dispatch(request)
    rendered = response.render()
    html = rendered.content.decode()

    expected = 'id="checkboxes-error-message-error"'
    assert (expected in html) is True
