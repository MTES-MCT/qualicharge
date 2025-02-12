"""Dashboard core annuaire entreprises clients."""

from typing import Any
from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings

from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)
from apps.core.validators import validate_siren, validate_siret


def _validate_company_info_type(value: Any) -> CompanyInformationAdapter:
    """Ensure the provided value is a CompanyInformationAdapter."""
    if not isinstance(value, CompanyInformationAdapter):
        raise TypeError(
            f"Expected CompanyInformationAdapter, got {type(value)} instead."
        )
    return value


def _validate_company_address_type(value: Any) -> CompanyAddressAdapter:
    """Ensure the provided value is a CompanyAddressAdapter."""
    if not isinstance(value, CompanyAddressAdapter):
        raise TypeError(f"Expected CompanyAddressAdapter, got {type(value)} instead.")
    return value


class AnnuaireDesEntreprises:
    """Facade class to simplify usage of the Annuaire des Entreprises API."""

    def __init__(self):
        """Initialize the clients."""
        self.company_info_client = CompanyInformationClient()
        self.company_address_client = CompanyAddressClient()

    def company_details(self, siren: str) -> CompanyInformationAdapter:
        """Get company information from a SIREN number.

        Returns:
            CompanyInformationAdapter: Adapted company information.
        """
        return _validate_company_info_type(self.company_info_client.get(siren))

    def company_address(self, siret: str) -> CompanyAddressAdapter:
        """Get company address from a SIRET number.

        Returns:
            CompanyAddressAdapter: Adapted company address.
        """
        return _validate_company_address_type(self.company_address_client.get(siret))


class AnnuaireEntrepriseBaseClient:
    """Base Client for `Annuaire des Entreprises` API."""

    def __init__(self):
        """Initialize the API client."""
        self.api_root_url = settings.ANNUAIRE_ENTREPRISE_API_ROOT_URL
        self.token = settings.ANNUAIRE_ENTREPRISE_API_TOKEN
        self.context = self._get_context()

    def _get(self, endpoint: str, params: str | None = None) -> dict:
        """Make a GET request to the API."""
        url = urljoin(self.api_root_url, endpoint)
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=settings.ANNUAIRE_ENTREPRISE_API_TIMEOUT,
        )

        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_context() -> str:
        """Get a formatted token string used for specific API-related context."""
        context_settings = settings.ANNUAIRE_ENTREPRISE_API_CONTEXT
        return urlencode(
            {
                "context": context_settings["context"],
                "object": context_settings["object"],
                "recipient": context_settings["recipient"],
            }
        )


class CompanyInformationClient(AnnuaireEntrepriseBaseClient):
    """Client for the company information ("unites legales") endpoint."""

    endpoint = "insee/sirene/unites_legales/"

    def get(self, siren: str, json: bool = False) -> CompanyInformationAdapter | dict:
        """Retrieves company information from the SIREN and adapts it."""
        validate_siren(siren)
        api_response: dict = self._get(f"{self.endpoint}{siren}", params=self.context)

        if json:
            return api_response
        return CompanyInformationAdapter.from_api_response(api_response)


class CompanyAddressClient(AnnuaireEntrepriseBaseClient):
    """Client for the company address endpoint."""

    def get(self, siret: str, json: bool = False) -> CompanyAddressAdapter | dict:
        """Retrieves company address from the SIRET and adapts it."""
        validate_siret(siret)
        endpoint: str = f"insee/sirene/etablissements/{siret}/adresse"
        api_response: dict = self._get(endpoint, params=self.context)

        if json:
            return api_response
        return CompanyAddressAdapter.from_api_response(api_response)
