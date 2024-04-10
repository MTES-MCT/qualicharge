"""QualiCharge static models."""

import json
from enum import StrEnum
from typing import Optional

from pydantic import (
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    PlainSerializer,
    PositiveFloat,
    PositiveInt,
    WithJsonSchema,
)
from pydantic.types import PastDate
from pydantic_extra_types.coordinate import Coordinate
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing_extensions import Annotated


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


class RaccordementEmum(StrEnum):
    """Statique.raccordement field enum."""

    DIRECT = "Direct"
    INDIRECT = "Indirect"


class FrenchPhoneNumber(PhoneNumber):
    """A phone number with french defaults."""

    default_region_code = "FR"


# A pivot type to handle DataGouv coordinates de/serialization.
DataGouvCoordinate = Annotated[
    Coordinate,
    # Input string format is: "[longitude: float, latitude: float]". It is converted to
    # a reversed tuple (latitude: float, longitude: float) that will be used as
    # Coordinate input.
    BeforeValidator(
        lambda x: tuple(reversed(json.loads(x))) if isinstance(x, str) else x
    ),
    # When serializing a coordinate we want a string array: "[long,lat]"
    PlainSerializer(lambda x: f"[{x.longitude},{x.latitude}]", return_type=str),
    # Document expected longitude/latitude order in the description
    WithJsonSchema(
        {
            "type": "string",
            "title": "coordonneesXY",
            "description": (
                "coordonneesXY is supposed to be a "
                "'[longitude,latitude]' array string"
            ),
            "examples": [
                "[12.3, 41.5]",
            ],
        },
    ),
]


class Statique(BaseModel):
    """IRVE static model."""

    nom_amenageur: Optional[str]
    siren_amenageur: Optional[Annotated[str, Field(pattern=r"^\d{9}$")]]
    contact_amenageur: Optional[EmailStr]
    nom_operateur: Optional[str]
    contact_operateur: EmailStr
    telephone_operateur: Optional[FrenchPhoneNumber]
    nom_enseigne: str
    id_station_itinerance: Annotated[
        str, Field(pattern="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$")
    ]
    id_station_local: Optional[str]
    nom_station: str
    implantation_station: ImplantationStationEnum
    adresse_station: str
    code_insee_commune: Optional[
        Annotated[str, Field(pattern=r"^([013-9]\d|2[AB1-9])\d{3}$")]
    ]
    coordonneesXY: DataGouvCoordinate
    nbre_pdc: PositiveInt
    id_pdc_itinerance: Optional[
        Annotated[
            str, Field(pattern="(?:(?:^|,)(^[A-Z]{2}[A-Z0-9]{4,33}$|Non concerné))+$")
        ]
    ]
    id_pdc_local: Optional[str]
    puissance_nominale: PositiveFloat
    prise_type_ef: bool
    prise_type_2: bool
    prise_type_combo_ccs: bool
    prise_type_chademo: bool
    prise_type_autre: bool
    gratuit: Optional[bool]
    paiement_acte: bool
    paiement_cb: Optional[bool]
    paiement_autre: Optional[bool]
    tarification: Optional[str]
    condition_acces: ConditionAccesEnum
    reservation: bool
    horaires: Annotated[
        str, Field(pattern=r"(.*?)((\d{1,2}:\d{2})-(\d{1,2}:\d{2})|24/7)")
    ]
    accessibilite_pmr: AccessibilitePMREnum
    restriction_gabarit: str
    station_deux_roues: bool
    raccordement: Optional[RaccordementEmum]
    num_pdl: Optional[Annotated[str, Field(pattern=r"^\d{14}$")]]
    date_mise_en_service: Optional[PastDate]
    observations: Optional[str]
    date_maj: PastDate
    cable_t2_attache: Optional[bool]
