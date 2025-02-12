"""Dashboard core annuaire entreprises adapters."""

from dataclasses import dataclass


@dataclass
class CompanyInformationAdapter:
    """Encapsulation of company information."""

    name: str
    legal_form: str
    siren: str
    siret_head_office: str
    naf: str
    raw_data: dict

    @classmethod
    def from_api_response(cls, api_data: dict) -> "CompanyInformationAdapter":
        """Creates an instance from an API response."""
        data = api_data["data"]
        return cls(
            name=data.get("personne_morale_attributs", {}).get("raison_sociale", ""),
            legal_form=data.get("forme_juridique", {}).get("libelle", ""),
            siren=data.get("siren"),
            siret_head_office=data.get("siret_siege_social", ""),
            naf=cls.format_naf_code(
                data.get("activite_principale", {}).get("code", "")
            ),
            raw_data=data,
        )

    @staticmethod
    def format_naf_code(naf_code: str) -> str:
        """Reformat NAF code.

        The NAF code from the API has the format "12.34A", but we need "1234A" to match.
        """
        return naf_code.replace(".", "")


@dataclass
class CompanyAddressAdapter:
    """Encapsulation of company address info."""

    address_1: str
    address_2: str
    city: str
    zip_code: str
    raw_data: dict

    @classmethod
    def from_api_response(cls, api_data: dict) -> "CompanyAddressAdapter":
        """Creates an instance from an API response."""
        data = api_data["data"]
        return cls(
            address_1=cls._get_formatted_address_1(data),
            address_2=data.get("complement_adresse", ""),
            city=data.get("libelle_commune", ""),
            zip_code=data.get("code_postal", ""),
            raw_data=data,
        )

    @staticmethod
    def _get_formatted_address_1(data: dict) -> str:
        """Returns a formatted address line based on the address components."""
        components = [
            data.get("numero_voie", ""),
            data.get("indice_repetition_voie", ""),
            data.get("type_voie", ""),
            data.get("libelle_voie", ""),
        ]
        return " ".join(filter(None, components))
