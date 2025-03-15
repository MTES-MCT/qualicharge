"""Dashboard core annuaire entreprise API adapters tests."""

import pytest

from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)

SIRET = "55204944712345"
API_RESPONSE_COMPANY_INFO = {
    "data": {
        "siren": "552049447",
        "siret_siege_social": "55204944776279",
        "personne_morale_attributs": {
            "raison_sociale": "SOCIETE NATIONALE SNCF",
            "sigle": "SNCF",
        },
        "forme_juridique": {
            "code": "5599",
            "libelle": "SA à conseil d'administration (s.a.i.)",
        },
        "activite_principale": {
            "code": "49.10Z",
            "nomenclature": "NAFRev2",
            "libelle": "Transport ferroviaire interurbain de voyageurs",
        },
    },
}
API_RESPONSE_COMPANY_ADDRESS = {
    "data": {
        "numero_voie": "2",
        "indice_repetition_voie": None,
        "type_voie": "PLACE",
        "libelle_voie": "AUX ETOILES",
        "complement_adresse": None,
        "code_commune": "93066",
        "libelle_commune": "SAINT-DENIS",
        "code_postal": "93210",
    }
}


def test_company_information_adapter_initialization():
    """Tests initialization of the CompanyInformationAdapter."""
    company_info = CompanyInformationAdapter.from_api_response(
        API_RESPONSE_COMPANY_INFO
    )
    assert company_info.name == "SOCIETE NATIONALE SNCF"
    assert company_info.legal_form == "SA à conseil d'administration (s.a.i.)"
    assert company_info.siren == "552049447"
    assert company_info.siret_head_office == "55204944776279"
    assert company_info.naf == "4910Z"


def test_company_information_adapter_missing_attributs():
    """Tests handling of missing key."""
    # test without attributs
    company_info = {}
    with pytest.raises(KeyError):
        CompanyInformationAdapter.from_api_response(company_info)

    # test with missing attributs
    company_info = {
        "data": {
            "siren": "123456789",
            "siret_siege_social": "12345678900019",
        }
    }
    data = CompanyInformationAdapter.from_api_response(company_info)
    assert data.name == ""
    assert data.legal_form == ""
    assert data.siren == "123456789"
    assert data.siret_head_office == "12345678900019"
    assert data.naf == ""


def test_company_address_adapter_initialization():
    """Tests initialization of the CompanyAddressAdapter."""
    company_info = CompanyAddressAdapter.from_api_response(API_RESPONSE_COMPANY_ADDRESS)
    assert company_info.address_1 == "2 PLACE AUX ETOILES"
    assert company_info.address_2 is None
    assert company_info.city == "SAINT-DENIS"
    assert company_info.zip_code == "93210"


def test_company_address_adapter_missing_attributs():
    """Tests handling of missing key."""
    # test without attributs
    company_info = {}
    with pytest.raises(KeyError):
        CompanyAddressAdapter.from_api_response(company_info)

    # test with missing attributs
    company_info = {
        "data": {
            "numero_voie": "2",
            "indice_repetition_voie": None,
            "type_voie": "PLACE",
        }
    }
    data = CompanyAddressAdapter.from_api_response(company_info)
    assert data.address_1 == "2 PLACE"
    assert data.address_2 == ""
    assert data.city == ""
    assert data.zip_code == ""
