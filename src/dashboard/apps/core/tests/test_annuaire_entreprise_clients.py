"""Dashboard core annuaire entreprise API clients tests."""

from http import HTTPStatus
from urllib.parse import urlencode, urljoin

import pytest
import responses
from django.core.exceptions import ValidationError
from requests import HTTPError

from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)
from apps.core.annuaire_entreprise_api.clients import (
    AnnuaireDesEntreprises,
    AnnuaireEntrepriseBaseClient,
    CompanyAddressClient,
    CompanyInformationClient,
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


def test_annuaire_entreprise_api_initialization(settings):
    """Test the initialization of AnnuaireEntrepriseBaseClient."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseBaseClient()
    assert api_client.api_root_url == "http://example.com/api/"
    assert api_client.token == "test_token"  # noqa: S105
    assert (
        api_client.context
        == "context=test_context&object=test_object&recipient=12345678901234"
    )


@responses.activate
def test_make_request_is_valid(settings, monkeypatch):
    """Test _make_request method for API call is valid."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseBaseClient()

    # initialize request details
    endpoint = "test_endpoint"
    params = urlencode({"key1": "value1", "key2": "value2"})
    expected_response = {"data": "test_data"}
    url = urljoin(settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL, endpoint)

    # register the responses mock with http status 200
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.OK,
    )

    # make the request
    resp = api_client._get(endpoint, params=params)

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
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = AnnuaireEntrepriseBaseClient()

    # initialize request details
    endpoint = "test_endpoint"
    params = urlencode({"key1": "value1", "key2": "value2"})
    expected_response = {"data": "test_data"}
    url = urljoin(settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL, endpoint)

    # register the responses mock with http status 500
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )
    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client._get(endpoint, params=params)

    # register the responses mock with http status 404
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.NOT_FOUND,
    )
    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client._get(endpoint, params=params)


def test_get_company_info_valid_response(settings, monkeypatch):
    """Test the get_company_info method."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }
    siren = SIRET[:9]

    # mock _make_request()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.AnnuaireEntrepriseBaseClient._get",
        lambda self, endpoint, params: API_RESPONSE_COMPANY_INFO,
    )

    # test json response
    api_client = CompanyInformationClient()
    response = api_client.get(siren, json=True)
    assert response == API_RESPONSE_COMPANY_INFO

    # test object response
    response = api_client.get(siren)
    expected_response = API_RESPONSE_COMPANY_INFO["data"]
    assert (
        response.name
        == expected_response["personne_morale_attributs"]["raison_sociale"]
    )
    assert response.legal_form == expected_response["forme_juridique"]["libelle"]
    assert response.siren == expected_response["siren"]
    assert response.siret_head_office == expected_response["siret_siege_social"]


@responses.activate
def test_get_company_info_raise_error(settings, monkeypatch):
    """Test _make_request method for API call.

    - Test with valid response
    - Test invalid siren raise exception.
    - Test 404 and 500 HTTP errors raise exception.
    """
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = CompanyInformationClient()

    # initialize request details with invalid siren raise exception
    siren = "1234"
    with pytest.raises(ValidationError):
        api_client.get(siren)

    # initialize request details
    siren = SIRET[:9]
    endpoint = f"insee/sirene/unites_legales/{siren}"
    expected_response = {"data": "test_data"}
    url = urljoin(settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL, endpoint)

    # register the responses mock with http status 200
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get(siren)

    # register the responses mock with http status 404
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.NOT_FOUND,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get(siren)


def test_get_company_address_valid_response(settings, monkeypatch):
    """Test the get_company_info method."""
    # initialize API settings
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # mock _make_request()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.AnnuaireEntrepriseBaseClient._get",
        lambda self, endpoint, params: API_RESPONSE_COMPANY_ADDRESS,
    )

    # test json response
    api_client = CompanyAddressClient()
    response = api_client.get(SIRET, json=True)
    assert response == API_RESPONSE_COMPANY_ADDRESS

    # test object response
    response = api_client.get(SIRET, json=False)
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
    settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL = "http://example.com/api/"
    settings.ANNUAIRE_ENTREPRISE_API_TOKEN = "test_token"  # noqa: S105
    settings.ANNUAIRE_ENTREPRISE_API_CONTEXT = {
        "context": "test_context",
        "object": "test_object",
        "recipient": "12345678901234",
    }

    # initialize API
    api_client = CompanyAddressClient()

    # initialize request details with invalid siret raise exception
    siret = "1234"
    with pytest.raises(ValidationError):
        api_client.get(siret)

    # initialize request details with valid siret
    endpoint = f"insee/sirene/etablissements/{SIRET}/adresse"
    expected_response = {"data": "test_data"}
    url = urljoin(settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL, endpoint)

    # register the responses mock with http status 200
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get(SIRET)

    # register the responses mock with http status 404
    responses.add(
        responses.GET,
        url,
        json=expected_response,
        status=HTTPStatus.NOT_FOUND,
    )

    # make the request must raise exception
    with pytest.raises(HTTPError):
        api_client.get(SIRET)


def test_ade_facade_company_details_valid_siren(monkeypatch):
    """Tests company_details method with a valid SIREN."""
    mock_response = MockCompanyInfo()
    valid_siren = mock_response.siren

    # mock CompanyInformationClient.get()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.CompanyInformationClient.get",
        lambda self, siren: mock_response,
    )

    api_client = AnnuaireDesEntreprises()

    # test with valid SIREN
    result = api_client.company_details(valid_siren)
    assert isinstance(result, CompanyInformationAdapter)
    assert result.siren == valid_siren


def test_company_details_non_adapter_response(monkeypatch):
    """Tests company_details method with a non-adapter response."""
    # mock CompanyInformationClient.get()
    mock_response = {}
    valid_siren = "123456789"

    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.CompanyInformationClient.get",
        lambda self, siren: mock_response,
    )

    api_client = AnnuaireDesEntreprises()

    # test with a non-adapter response
    with pytest.raises(
        TypeError,
        match="Expected CompanyInformationAdapter, got <class 'dict'> instead",
    ):
        api_client.company_details(valid_siren)


def test_ade_facade_company_address_valid_siret(monkeypatch):
    """Tests company_details method with a valid SIRET."""
    mock_response = MockAddressInfo()
    valid_siret = "56789012345678"

    # mock CompanyInformationClient.get()
    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.CompanyAddressClient.get",
        lambda self, siret: mock_response,
    )

    api_client = AnnuaireDesEntreprises()

    # test with valid SIREN
    result = api_client.company_address(valid_siret)
    assert isinstance(result, CompanyAddressAdapter)


def test_ade_facade_company_address_non_adapter_response(monkeypatch):
    """Tests company_details method with a non-adapter response."""
    # mock CompanyInformationClient.get()
    mock_response = {}
    valid_siret = "56789012345678"

    monkeypatch.setattr(
        "apps.core.annuaire_entreprise_api.clients.CompanyAddressClient.get",
        lambda self, siret: mock_response,
    )

    api_client = AnnuaireDesEntreprises()

    # test with a non-adapter response
    with pytest.raises(
        TypeError, match="Expected CompanyAddressAdapter, got <class 'dict'> instead"
    ):
        api_client.company_address(valid_siret)
