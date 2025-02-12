"""Dashboard core annuaire entreprise API."""

import requests
from django.conf import settings

from apps.core.validators import validate_siren, validate_siret


class CompanyInformationAdapter:
    """Encapsulation of company information for simplified access to key details.

    Extracts and organizes essential company data from a json structure.
    Includes functionality to reformat specific codes, such as the NAF code.

    Attributes:
        company_info (dict): The raw company information data.
        name (str): The legal company name.
        legal_form (str): The legal form of the company.
        siren (str): The unique company identifier (SIREN).
        siret_siege (str): The SIRET code of the head office.
    """

    def __init__(self, company_info: dict):
        """Represents a company information with base attributes."""
        self.company_info: dict = company_info["data"]

        self.name: str = self.company_info["personne_morale_attributs"][
            "raison_sociale"
        ]
        self.legal_form: str = self.company_info["forme_juridique"]["libelle"]
        self.siren: str = self.company_info["siren"]
        self.siret_siege: str = self.company_info["siret_siege_social"]

    @property
    def naf(self) -> str:
        """Reformat NAF code.

        The NAF code from the API has the format "12.34A", but we need "1234A" to match.
        """
        return self.company_info["activite_principale"]["code"].replace(".", "")


class CompanyAddressAdapter:
    """Encapsulation of company address info for simplified access to key details.

    Extract and format the address details for a company.
    Includes functionality to reformat address line.

    Attributes:
        company_address (dict): The raw company address data.
        address_1 (str): Main address line.
        address_2 (str): Address complement.
        city (str): The city of the company.
        zip_code (str): The zip code of the company.
    """

    def __init__(self, company_address: dict):
        """Represents a company address."""
        self.company_address: dict = company_address["data"]

        self.address_2: str = self.company_address["complement_adresse"]
        self.city: str = self.company_address["libelle_commune"]
        self.zip_code: str = self.company_address["code_postal"]

    @property
    def address_1(self) -> str:
        """Returns a formatted address line based on the address components."""
        street_number: str = self.company_address["numero_voie"]
        street_repetition: str = self.company_address["indice_repetition_voie"]
        street_type: str = self.company_address["type_voie"]
        street_label: str = self.company_address["libelle_voie"]

        return (
            f"{street_number + ' ' if street_number else ''}"
            f"{street_repetition + ' ' if street_repetition else ''}"
            f"{street_type + ' ' if street_type else ''}"
            f"{street_label or ''}"
        )


class AnnuaireEntrepriseAPI:
    """Annuaire entreprise API client."""

    def __init__(self):
        """Initialize the API client."""
        self.api_url = settings.ANNUAIRE_ENTREPRISE_API_URL
        self.token = settings.ANNUAIRE_ENTREPRISE_API_TOKEN
        self.context = self._get_context()

    @staticmethod
    def _get_context():
        """Get a formatted token string used for specific API-related context.

        Returns:
            str: The constructed token string in query parameter format.
        """
        context = settings.ANNUAIRE_ENTREPRISE_API_CONTEXT["context"]
        context_object = settings.ANNUAIRE_ENTREPRISE_API_CONTEXT["object"]
        recipient = settings.ANNUAIRE_ENTREPRISE_API_CONTEXT["recipient"]

        return f"?context={context}&object={context_object}&recipient={recipient}"

    def _make_request(self, endpoint, params=None):
        """Make a request to the API."""
        url = f"{self.api_url}/{endpoint}"

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers, params=params, timeout=5000)
        response.raise_for_status()
        return response.json()

    def get_company_info(self, siren, json=False):
        """Get the company information from the API."""
        validate_siren(siren)

        endpoint = f"insee/sirene/unites_legales/{siren}{self.context}"
        company_info = self._make_request(endpoint)

        if json:
            return company_info
        return CompanyInformationAdapter(company_info)

    def get_company_address(self, siret, json=False):
        """Get the company information from the API."""
        validate_siret(siret)

        endpoint = f"insee/sirene/etablissements/{siret}/adresse{self.context}"
        company_address = self._make_request(endpoint)

        if json:
            return company_address
        return CompanyAddressAdapter(company_address)
