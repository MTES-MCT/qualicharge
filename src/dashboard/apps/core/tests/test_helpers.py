"""Dashboard core helpers tests."""

import pytest
from django.core.exceptions import ValidationError

from apps.auth.factories import UserFactory
from apps.core.helpers import sync_entity_from_siret
from apps.core.models import Entity


@pytest.mark.django_db
def test_create_and_populate_entity_creates_new_entity(monkeypatch):
    """Tests if a new entity is created and populated based on SIRET."""
    # mock info data of the company
    mock_info = type("MockCompanyInfo", (object,), {})()
    mock_info.name = "Test Company"
    mock_info.legal_form = "SARL"
    mock_info.naf = "1234Z"
    mock_info.siret_siege = "56789012345678"
    mock_info.siren = "567890123"

    # mock address data of the company
    mock_address = type("MockCompanyAddress", (object,), {})()
    mock_address.address_1 = "123 Test Street"
    mock_address.address_2 = ""
    mock_address.city = "Test City"
    mock_address.zip_code = "75000"

    # mock get_company_info()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.AnnuaireEntrepriseAPI.get_company_info",
        lambda self, siren: mock_info,
    )
    # mock get_company_address()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.AnnuaireEntrepriseAPI.get_company_address",
        lambda self, siret: mock_address,
    )

    # no entity exists
    assert Entity.objects.all().count() == 0

    # sync a new entity
    entity = sync_entity_from_siret(mock_info.siret_siege)

    # an entity was created with the mocked information
    assert Entity.objects.all().count() == 1
    assert entity.name == mock_info.name
    assert entity.siret == mock_info.siret_siege
    assert entity.legal_form == mock_info.legal_form
    assert entity.naf == mock_info.naf
    assert entity.address_1 == mock_address.address_1
    assert entity.address_2 == mock_address.address_2
    assert entity.address_city == mock_address.city
    assert entity.address_zip_code == mock_address.zip_code

    # sync existing entity without users
    sync_entity_from_siret(mock_info.siret_siege)
    # no new entity must be created
    assert Entity.objects.all().count() == 1
    assert not entity.users.exists()

    # sync existing entity with users
    user = UserFactory()
    entity = sync_entity_from_siret(mock_info.siret_siege, user=user)
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
