"""Dashboard core qualicharge adapters."""

from dataclasses import dataclass


@dataclass
class ManageStationsAdapter:
    """Encapsulation of company information."""

    id_station_itinerance: str
    nom_station: str
    num_pdl: str
    updated_at: str

    @classmethod
    def from_api_response(cls, api_data: dict) -> "ManageStationsAdapter":
        """Creates an instance from an API response."""
        return cls(
            id_station_itinerance=api_data.get("id_station_itinerance", ""),
            nom_station=api_data.get("nom_station", ""),
            num_pdl=api_data.get("num_pdl", ""),
            updated_at=api_data.get("updated_at", ""),
        )
