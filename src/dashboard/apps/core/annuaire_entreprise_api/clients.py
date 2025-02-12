"""Dashboard core annuaire entreprises clients."""

from urllib.parse import urlencode, urljoin

import requests
from django.conf import settings

from apps.core.annuaire_entreprise_api.adapters import (
    CompanyAddressAdapter,
    CompanyInformationAdapter,
)
from apps.core.validators import validate_siren, validate_siret

TIMEOUT = 5  # Request timeout in seconds


class AnnuaireEntrepriseBaseClient:
    """Base Client for `Annuaire des Entreprises` API."""

    def __init__(self):
        """Initialize the API client."""
        self.api_url = settings.ANNUAIRE_ENTREPRISE_API_URL
        self.token = settings.ANNUAIRE_ENTREPRISE_API_TOKEN
        self.context = self._get_context()

    def _get(self, endpoint, params=None):
        """Make a GET request to the API."""
        url = urljoin(self.api_url, endpoint)
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

        response.raise_for_status()
        return response.json()

    @staticmethod
    def _get_context():
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

    def get(self, siren: str, json=False) -> CompanyInformationAdapter:
        """Retrieves company information from the SIREN and adapts it."""
        validate_siren(siren)
        api_response = self._get(f"{self.endpoint}{siren}", params=self.context)

        if json:
            return api_response
        return CompanyInformationAdapter.from_api_response(api_response)


class CompanyAddressClient(AnnuaireEntrepriseBaseClient):
    """Client for the company address endpoint."""

    def get(self, siret: str, json=False) -> CompanyAddressAdapter:
        """Retrieves company address from the SIRET and adapts it."""
        validate_siret(siret)
        endpoint = f"insee/sirene/etablissements/{siret}/adresse"
        api_response = self._get(endpoint, params=self.context)

        if json:
            return api_response
        return CompanyAddressAdapter.from_api_response(api_response)
