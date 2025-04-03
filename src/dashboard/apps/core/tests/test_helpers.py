"""Dashboard core helpers tests."""

from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError

from apps.auth.factories import UserFactory
from apps.consent import AWAITING
from apps.consent.models import Consent
from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)
from apps.core.factories import EntityFactory
from apps.core.helpers import (
    sync_delivery_points_from_qualicharge_api,
    sync_entity_from_siret,
)
from apps.core.models import DeliveryPoint, Entity
from apps.core.qualicharge_api.adapters import ManageStationsAdapter


class MockCompanyInfo(CompanyInformationAdapter):
    """Mock company info."""

    def __init__(self):
        """Initiate mock company info."""
        self.name = "Test Company"
        self.legal_form = "SARL"
        self.naf = "1234Z"
        self.siret_head_office = "56789012345678"
        self.siren = "567890123"


class MockAddressInfo(CompanyAddressAdapter):
    """Mock address info."""

    def __init__(self):
        """Initiate mock address info."""
        self.address_1 = "123 Test Street"
        self.address_2 = ""
        self.city = "Test City"
        self.zip_code = "75000"


@pytest.mark.django_db
def test_create_and_populate_entity_creates_new_entity(monkeypatch):
    """Tests if a new entity is created and populated based on SIRET."""
    mock_info = MockCompanyInfo()
    mock_address = MockAddressInfo()

    # mock CompanyInformationClient.get()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.CompanyInformationClient.get",
        lambda self, siren: mock_info,
    )
    # mock CompanyAddressClient.get()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.CompanyAddressClient.get",
        lambda self, siret: mock_address,
    )

    # no entity exists
    assert Entity.objects.all().count() == 0

    # sync a new entity
    entity = sync_entity_from_siret(mock_info.siret_head_office)

    # an entity was created with the mocked information
    assert Entity.objects.all().count() == 1
    assert entity.name == mock_info.name
    assert entity.siret == mock_info.siret_head_office
    assert entity.legal_form == mock_info.legal_form
    assert entity.naf == mock_info.naf
    assert entity.address_1 == mock_address.address_1
    assert entity.address_2 == mock_address.address_2
    assert entity.address_city == mock_address.city
    assert entity.address_zip_code == mock_address.zip_code

    # sync existing entity without users
    sync_entity_from_siret(mock_info.siret_head_office)
    # no new entity must be created
    assert Entity.objects.all().count() == 1
    assert not entity.users.exists()

    # sync existing entity with users
    user = UserFactory()
    entity = sync_entity_from_siret(mock_info.siret_head_office, user=user)
    assert Entity.objects.all().count() == 1
    assert user in entity.users.all()


@pytest.mark.django_db
def test_create_and_populate_entity_creates_new_entity_raise_error(monkeypatch):
    """Tests if a new entity raised error with a bad SIRET."""
    assert Entity.objects.all().count() == 0

    bad_siret = "1234"
    with pytest.raises(ValidationError):
        sync_entity_from_siret(bad_siret)

    assert Entity.objects.all().count() == 0


@pytest.mark.django_db
@patch("apps.core.helpers.QualiChargeApi")
def test_create_deliverypoint_from_qualicharge_api(mock_qualicharge_api):
    """Test create delivery point from QualiCharge API."""
    assert Entity.objects.all().count() == 0
    entity = EntityFactory(siret="30119246401234")
    assert entity.synced_at is None
    assert Entity.objects.all().count() == 1
    assert DeliveryPoint.objects.all().count() == 0
    assert Consent.objects.all().count() == 0

    # Simulate API response
    mock_response = [
        ManageStationsAdapter(
            id_station_itinerance="FR073P01STATIONA",
            nom_station="Station A",
            num_pdl="50088800000000",
            updated_at="2025-03-12T15:49:43.477800Z",
        ),
        ManageStationsAdapter(
            id_station_itinerance="FR073P02STB",
            nom_station="Station B",
            num_pdl="50088800000001",
            updated_at="2025-03-12T15:49:43.477800Z",
        ),
        ManageStationsAdapter(
            id_station_itinerance="FR073P02STB",
            nom_station="Station B",
            num_pdl="50088800000002",
            updated_at="2025-03-12T15:49:43.477800Z",
        ),
        ManageStationsAdapter(
            id_station_itinerance="FR073P02STC",
            nom_station="Station b2",
            num_pdl="50088800000002",
            updated_at="2025-03-12T15:49:43.477800Z",
        ),
    ]
    # mock ManageStationClient.list()
    mock_qualicharge_api.return_value.manage_stations_list.return_value = mock_response

    # create new delivery points should be ok
    delivery_points, consents = sync_delivery_points_from_qualicharge_api(entity)

    expected_count = 3
    assert len(delivery_points) == expected_count
    assert len(consents) == expected_count

    entity.refresh_from_db()
    delivery_points = DeliveryPoint.objects.all()
    consents = Consent.objects.all()
    expected_delivery_points_count = 3

    # 3 delivery_points and consents should be created
    assert delivery_points.count() == expected_delivery_points_count
    assert consents.count() == expected_delivery_points_count

    # check created delivery points
    mock_obj1 = Mock()
    mock_obj1.num_pdl = "50088800000000"
    mock_obj1.updated_at = "2025-03-12T15:49:43.477800Z"

    mock_obj2 = Mock()
    mock_obj2.num_pdl = "50088800000001"
    mock_obj2.updated_at = "2025-03-12T15:49:43.477800Z"

    mock_obj3 = Mock()
    mock_obj3.num_pdl = "50088800000002"
    mock_obj3.updated_at = "2025-03-12T15:49:43.477800Z"

    expected_created = [mock_obj1, mock_obj2, mock_obj3]

    for dp, expected in zip(delivery_points, expected_created, strict=True):
        assert dp.provider_assigned_id == expected.num_pdl
        assert dp.entity == entity

    # check created consents
    for consent, dp in zip(consents, delivery_points, strict=True):
        assert consent.delivery_point == dp
        assert consent.provider_assigned_id == dp.provider_assigned_id
        assert consent.status == AWAITING

    entity.refresh_from_db()
    assert entity.synced_at is not None

    # run function with same delivery points should not create new delivery points.
    delivery_points, consents = sync_delivery_points_from_qualicharge_api(entity)
    assert delivery_points == []
    assert consents == []
    assert DeliveryPoint.objects.all().count() == expected_delivery_points_count
    assert Consent.objects.all().count() == expected_delivery_points_count
