"""QualiCharge static models."""

import json
import re
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Optional

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    PlainSerializer,
    PositiveFloat,
    PositiveInt,
    WithJsonSchema,
    model_validator,
)
from pydantic_extra_types.coordinate import Coordinate
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing_extensions import Annotated, Self

from .utils import ModelSchemaMixin


class ImplantationStationEnum(StrEnum):
    """Statique.implantation_station field enum."""

    VOIRIE = "Voirie"
    PARKING_PUBLIC = "Parking public"
    PARKING_PRIVE_USAGE_PUBLIC = "Parking privé à usage public"
    PARKING_PRIVE_CLIENTELE = "Parking privé réservé à la clientèle"
    STATION_RECHARGE_RAPIDE = "Station dédiée à la recharge rapide"


class ConditionAccesEnum(StrEnum):
    """Statique.condition_acces field enum."""

    ACCESS_LIBRE = "Accès libre"
    ACCESS_RESERVE = "Accès réservé"


class AccessibilitePMREnum(StrEnum):
    """Statique.accessibilite_pmr field enum."""

    RESERVE_PMR = "Réservé PMR"
    NON_RESERVE = "Accessible mais non réservé PMR"
    NON_ACCESSIBLE = "Non accessible"
    INCONNUE = "Accessibilité inconnue"


class RaccordementEnum(StrEnum):
    """Statique.raccordement field enum."""

    DIRECT = "Direct"
    INDIRECT = "Indirect"


class FrenchPhoneNumber(PhoneNumber):
    """A phone number with french defaults."""

    default_region_code = "FR"


def to_coordinates_tuple(value):
    """Convert input string to a Coordinate tuple.

    Three string formats are supported:

    1. "[longitude: float, latitude: float]"
    2. "POINT(longitude latitude)"
    3. "SRID=0000;POINT(longitude latitude)"

    In all cases, the input string is converted to a reversed tuple
    (latitude: float, longitude: float) that will be used as Coordinate input.
    """
    if not isinstance(value, str):
        return value
    if m := re.match(
        r"(?:SRID=\d{4};)?POINT\((?P<longitude>-?\d+\.\d+) (?P<latitude>-?\d+\.\d+)\)",
        value,
    ):
        return (m["latitude"], m["longitude"])
    return tuple(reversed(json.loads(value)))


# A pivot type to handle DataGouv coordinates de/serialization.
DataGouvCoordinate = Annotated[
    Coordinate,
    # Convert input string to a (latitude, longitude) Coordinate tuple input
    BeforeValidator(to_coordinates_tuple),
    # When serializing a coordinate we want a string array: "[long,lat]"
    PlainSerializer(lambda x: f"[{x.longitude}, {x.latitude}]", return_type=str),
    # Document expected longitude/latitude order in the description
    WithJsonSchema(
        {
            "type": "string",
            "title": "coordonneesXY",
            "description": (
                "coordonneesXY is supposed to be a '[longitude,latitude]' array string"
            ),
            "examples": [
                "[12.3, 41.5]",
            ],
        },
    ),
]


def not_future(value: date):
    """Ensure date is not in the future."""
    today = datetime.now(timezone.utc).date()
    if value > today:
        raise ValueError(f"{value} is in the future")
    return value


# A date not in the future (today or in the past)
NotFutureDate = Annotated[date, AfterValidator(not_future)]

# Default values (if not provided)
DEFAULT_CHAR_VALUE: str = "NA"
DEFAULT_EMAIL_ADDRESS: str = "na@example.org"
DEFAULT_PHONE_NUMBER: FrenchPhoneNumber = FrenchPhoneNumber("+33.123456789")
DEFAULT_SIREN_NUMBER: str = "123456789"


class Statique(ModelSchemaMixin, BaseModel):
    """IRVE static model."""

    nom_amenageur: Optional[str] = DEFAULT_CHAR_VALUE
    siren_amenageur: Optional[
        Annotated[
            str,
            Field(
                pattern=r"^\d{9}$",
                examples=[
                    "853300010",
                ],
            ),
        ]
    ] = DEFAULT_SIREN_NUMBER
    contact_amenageur: Optional[EmailStr] = DEFAULT_EMAIL_ADDRESS
    nom_operateur: Optional[str] = DEFAULT_CHAR_VALUE
    contact_operateur: EmailStr
    telephone_operateur: Optional[FrenchPhoneNumber] = DEFAULT_PHONE_NUMBER
    nom_enseigne: str
    id_station_itinerance: Annotated[
        str, Field(pattern="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$")
    ]
    id_station_local: Optional[str] = None
    nom_station: str
    implantation_station: ImplantationStationEnum
    adresse_station: str
    code_insee_commune: Annotated[str, Field(pattern=r"^([013-9]\d|2[AB1-9])\d{3}$")]
    coordonneesXY: DataGouvCoordinate
    nbre_pdc: PositiveInt
    id_pdc_itinerance: Annotated[
        str,
        Field(
            pattern="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$",
            examples=["FR0NXEVSEXB9YG", "FRFASE3300405", "FR073012308585"],
        ),
    ]
    id_pdc_local: Optional[str] = None
    puissance_nominale: PositiveFloat
    prise_type_ef: bool
    prise_type_2: bool
    prise_type_combo_ccs: bool
    prise_type_chademo: bool
    prise_type_autre: bool
    gratuit: Optional[bool] = None
    paiement_acte: bool
    paiement_cb: Optional[bool] = None
    paiement_autre: Optional[bool] = None
    tarification: Optional[str] = None
    condition_acces: ConditionAccesEnum
    reservation: bool
    horaires: Annotated[
        str, Field(pattern=r"(.*?)((\d{1,2}:\d{2})-(\d{1,2}:\d{2})|24/7)")
    ]
    accessibilite_pmr: AccessibilitePMREnum
    restriction_gabarit: str
    station_deux_roues: bool
    raccordement: Optional[RaccordementEnum] = None
    num_pdl: Optional[Annotated[str, Field(max_length=64)]]
    date_mise_en_service: Optional[NotFutureDate] = None
    observations: Optional[str] = None
    date_maj: NotFutureDate
    cable_t2_attache: Optional[bool] = None

    @model_validator(mode="after")
    def check_afirev_prefix(self) -> Self:
        """Check that id_pdc_itinerance and id_station_itinerance prefixes match."""
        if self.id_pdc_itinerance[:5] != self.id_station_itinerance[:5]:
            raise ValueError(
                (
                    "AFIREV prefixes from id_station_itinerance and "
                    "id_pdc_itinerance do not match"
                )
            )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300401",
                    "id_pdc_local": "FRFASE3300401",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": True,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": True,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": True,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300402",
                    "id_pdc_local": "FRFASE3300402",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": True,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": True,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": True,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300403",
                    "id_pdc_local": "FRFASE3300403",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": False,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": False,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": False,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300404",
                    "id_pdc_local": "FRFASE3300404",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": False,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": False,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": False,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300405",
                    "id_pdc_local": "FRFASE3300405",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": False,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": False,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": False,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300406",
                    "id_pdc_local": "FRFASE3300406",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": False,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": False,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": False,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300407",
                    "id_pdc_local": "FRFASE3300407",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": False,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": False,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": False,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire de la Plaine du Forez Est",
                    "id_station_itinerance": "FRFASE33004",
                    "id_station_local": "FRFASE33004",
                    "nom_station": "Fastned Aire de la Plaine du Forez Est",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire de la Plaine du Forez A72, 42600 Magneux",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.156034, 45.679959]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300408",
                    "id_pdc_local": "FRFASE3300408",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": False,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": False,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-12-02",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": False,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire d’Ambrussum Nord",
                    "id_station_itinerance": "FRFASE33007",
                    "id_station_local": "FRFASE33007",
                    "nom_station": "Fastned Aire d’Ambrussum Nord",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire d’Ambrussum Nord A9, 34400 Villetelle",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.13341, 43.715255]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300701",
                    "id_pdc_local": "FRFASE3300701",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": True,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": True,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-11-22",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": True,
                },
                {
                    "nom_amenageur": "Fastned France",
                    "siren_amenageur": "853300010",
                    "contact_amenageur": "support@fastned.nl",
                    "nom_operateur": "Fastned France",
                    "contact_operateur": "support@fastned.nl",
                    "telephone_operateur": "tel:+33-1-84-71-00-62",
                    "nom_enseigne": "Fastned Aire d’Ambrussum Nord",
                    "id_station_itinerance": "FRFASE33007",
                    "id_station_local": "FRFASE33007",
                    "nom_station": "Fastned Aire d’Ambrussum Nord",
                    "implantation_station": "Station dédiée à la recharge rapide",
                    "adresse_station": "Aire d’Ambrussum Nord A9, 34400 Villetelle",
                    "code_insee_commune": "42130",
                    "coordonneesXY": "[4.13341, 43.715255]",
                    "nbre_pdc": 8,
                    "id_pdc_itinerance": "FRFASE3300702",
                    "id_pdc_local": "FRFASE3300702",
                    "puissance_nominale": 20.0,
                    "prise_type_ef": False,
                    "prise_type_2": True,
                    "prise_type_combo_ccs": True,
                    "prise_type_chademo": True,
                    "prise_type_autre": True,
                    "gratuit": False,
                    "paiement_acte": True,
                    "paiement_cb": True,
                    "paiement_autre": True,
                    "tarification": "0,40€ par KWh pour les non abonnés",
                    "condition_acces": "Accès libre",
                    "reservation": False,
                    "horaires": "24/7",
                    "accessibilite_pmr": "Accessible mais non réservé PMR",
                    "restriction_gabarit": "Hauteur maximale 3m",
                    "station_deux_roues": False,
                    "raccordement": "Direct",
                    "num_pdl": "00001234567890",
                    "date_mise_en_service": "2022-11-22",
                    "observations": "Néant",
                    "date_maj": "2024-06-04",
                    "cable_t2_attache": True,
                },
            ]
        }
    }
