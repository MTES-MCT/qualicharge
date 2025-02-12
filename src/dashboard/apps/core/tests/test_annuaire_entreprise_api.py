"""Dashboard core validators tests."""

from http import HTTPStatus

import pytest
import responses
from django.core.exceptions import ValidationError
from requests import HTTPError

from ..annuaire_entreprise_api import (
    AnnuaireEntrepriseAPI,
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


def test_annuaire_entreprise_api_initialization(settings):
    """Test the initialization of AnnuaireEntrepriseAPI."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseAPI()
    assert api_client.api_url == "http://example.com/api"
    assert api_client.token == "test_token"  # noqa: S105
    assert (
        api_client.context
        == "?context=test_context&object=test_object&recipient=12345678901234"
    )


@responses.activate
def test_make_request_is_valid(settings, monkeypatch):
    """Test _make_request method for API call is valid."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseAPI()

    # initialize request details
    endpoint = "test_endpoint"
    params = {"key1": "value1", "key2": "value2"}
    expected_response = {"data": "test_data"}
    url = f"{settings.ANNUAIRE_ENTREPRISE_API_URL}/{endpoint}"

    # register the responses mock with http status 200
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.OK,
    )

    # make the request
    resp = api_client._make_request(endpoint, params=params)

    assert resp == expected_response
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == f"{url}?key1=value1&key2=value2"
    assert (
        responses.calls[0].request.headers["Authorization"]
        == f"Bearer {settings.ANNUAIRE_ENTREPRISE_API_TOKEN}"
    )


@responses.activate
def test_make_request_raise_error(settings, monkeypatch):
    """Test _make_request method for API call.

    - Test 404 and 500 HTTP errors raise exception.
    """
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseAPI()

    # initialize request details
    endpoint = "test_endpoint"
    params = {"key1": "value1", "key2": "value2"}
    expected_response = {"data": "test_data"}
    url = f"{settings.ANNUAIRE_ENTREPRISE_API_URL}/{endpoint}"

    # register the responses mock with http status 500
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client._make_request(endpoint, params=params)

    # register the responses mock with http status 404
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.NOT_FOUND,
    )
    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client._make_request(endpoint, params=params)


def test_get_company_info_valid_response(settings, monkeypatch):
    """Test the get_company_info method."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }
    siren = SIRET[:9]

    # mock _make_request()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.AnnuaireEntrepriseAPI._make_request",
        lambda self, endpoint: API_RESPONSE_COMPANY_INFO,
    )

    # test json response
    api_client = AnnuaireEntrepriseAPI()
    response = api_client.get_company_info(siren, json=True)
    assert response == API_RESPONSE_COMPANY_INFO

    # test object response
    response = api_client.get_company_info(siren, json=False)
    expected_response = API_RESPONSE_COMPANY_INFO["data"]
    assert (
        response.name
        == expected_response["personne_morale_attributs"]["raison_sociale"]
    )
    assert response.legal_form == expected_response["forme_juridique"]["libelle"]
    assert response.siren == expected_response["siren"]
    assert response.siret_siege == expected_response["siret_siege_social"]


@responses.activate
def test_get_company_info_raise_error(settings, monkeypatch):
    """Test _make_request method for API call.

    - Test with valid response
    - Test invalid siren raise exception.
    - Test 404 and 500 HTTP errors raise exception.
    """
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseAPI()

    # initialize request details with invalid siren raise exception
    siren = "1234"
    with pytest.raises(ValidationError):
        api_client.get_company_info(siren)

    # initialize request details
    siren = SIRET[:9]
    endpoint = f"insee/sirene/unites_legales/{siren}"
    expected_response = {"data": "test_data"}
    url = f"{settings.ANNUAIRE_ENTREPRISE_API_URL}/{endpoint}"

    # register the responses mock with http status 200
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get_company_info(siren)

    # register the responses mock with http status 404
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.NOT_FOUND,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get_company_info(siren)


def test_get_company_address_valid_response(settings, monkeypatch):
    """Test the get_company_info method."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # mock _make_request()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.AnnuaireEntrepriseAPI._make_request",
        lambda self, endpoint: API_RESPONSE_COMPANY_ADDRESS,
    )

    # test json response
    api_client = AnnuaireEntrepriseAPI()
    response = api_client.get_company_address(SIRET, json=True)
    assert response == API_RESPONSE_COMPANY_ADDRESS

    # test object response
    response = api_client.get_company_address(SIRET, json=False)
    expected_response = API_RESPONSE_COMPANY_ADDRESS["data"]
    expected_address = "2 PLACE AUX ETOILES"

    assert response.address_1 == expected_address
    assert response.address_2 == expected_response["complement_adresse"]
    assert response.city == expected_response["libelle_commune"]
    assert response.zip_code == expected_response["code_postal"]


@responses.activate
def test_get_company_address_raise_error(settings, monkeypatch):
    """Test _make_request method for API call.

    - test with valid response
    - test invalid siret raise exception.
    - test 404 and 500 HTTP errors raise exception.
    """
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_URL = "http://example.com/api"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseAPI()

    # initialize request details with invalid siret raise exception
    siret = "1234"
    with pytest.raises(ValidationError):
        api_client.get_company_address(siret)

    # initialize request details with valid siret
    endpoint = f"insee/sirene/etablissements/{SIRET}/adresse"
    expected_response = {"data": "test_data"}
    url = f"{settings.ANNUAIRE_ENTREPRISE_API_URL}/{endpoint}"

    # register the responses mock with http status 200
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get_company_address(SIRET)

    # register the responses mock with http status 404
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.NOT_FOUND,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get_company_address(SIRET)


def test_company_information_adapter_initialization():
    """Tests initialization of the CompanyInformationAdapter."""
    company_info = CompanyInformationAdapter(API_RESPONSE_COMPANY_INFO)
    assert company_info.name == "SOCIETE NATIONALE SNCF"
    assert company_info.legal_form == "SA à conseil d'administration (s.a.i.)"
    assert company_info.siren == "552049447"
    assert company_info.siret_siege == "55204944776279"
    assert company_info.naf == "4910Z"


def test_company_information_adapter_missing_attributs():
    """Tests handling of missing key."""
    company_info = {}
    with pytest.raises(KeyError):
        CompanyInformationAdapter(company_info)

    company_info = {
        "data": {
            "siren": "123456789",
            "siret_siege_social": "12345678900019",
        }
    }
    with pytest.raises(KeyError):
        CompanyInformationAdapter(company_info)


def test_company_address_adapter_initialization():
    """Tests initialization of the CompanyAddressAdapter."""
    company_info = CompanyAddressAdapter(API_RESPONSE_COMPANY_ADDRESS)
    assert company_info.address_1 == "2 PLACE AUX ETOILES"
    assert company_info.address_2 is None
    assert company_info.city == "SAINT-DENIS"
    assert company_info.zip_code == "93210"


def test_company_address_adapter_missing_attributs():
    """Tests handling of missing key."""
    company_info = {}
    with pytest.raises(KeyError):
        CompanyAddressAdapter(company_info)

    company_info = {
        "data": {
            "numero_voie": "2",
            "indice_repetition_voie": None,
            "type_voie": "PLACE",
        }
    }
    with pytest.raises(KeyError):
        CompanyAddressAdapter(company_info)
