"""QualiCharge static models tests."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic_extra_types.coordinate import Coordinate

from qualicharge.factories.static import StatiqueFactory
from qualicharge.models.static import Statique


def test_statique_model_coordonneesXY():
    """Test the Statique model coordonneesXY field."""
    longitude = -12.3
    latitude = 16.2

    # Expected raw input
    record = StatiqueFactory.build(
        coordonneesXY=f"[{longitude},{latitude}]",
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Tuple input
    record = StatiqueFactory.build(
        coordonneesXY=(latitude, longitude),
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Coordinate input
    record = StatiqueFactory.build(
        coordonneesXY=Coordinate(latitude, longitude),
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude

    # Geometry input
    record = StatiqueFactory.build(
        coordonneesXY=f"POINT({longitude} {latitude})",
    )
    assert record.coordonneesXY.longitude == longitude
    assert record.coordonneesXY.latitude == latitude


@pytest.mark.parametrize(
    "phone_number",
    (
        "+33144276350",
        "+33.1 44 27 63 50",
        "+33 (0)1 44 27 63 50",
        "+33 (0) 1 44 27 63 50",
        "+33 1 44 27 63 50",
        "0144276350",
        "01 44 27 63 50",
        "01-44-27-63-50",
        "(01)44276350",
    ),
)
def test_statique_model_french_phone_numbers(phone_number):
    """Test all french phone numbers formats."""
    statique = StatiqueFactory.build(telephone_operateur=phone_number)
    assert statique.telephone_operateur == "tel:+33-1-44-27-63-50"


def test_statique_model_json_schema():
    """Test the Statique model generated JSON schema."""
    schema = Statique.model_json_schema()

    expected_description = (
        "coordonneesXY is supposed to be a '[longitude,latitude]' array string"
    )
    assert schema["properties"]["coordonneesXY"]["type"] == "string"
    assert schema["properties"]["coordonneesXY"]["title"] == "coordonneesXY"
    assert schema["properties"]["coordonneesXY"]["description"] == expected_description
    assert schema["properties"]["coordonneesXY"]["examples"] == ["[12.3, 41.5]"]


def test_statique_model_afirev_previx_check():
    """Test the id_pdc/station_itinerance consistency."""
    with pytest.raises(
        ValueError,
        match=(
            "AFIREV prefixes from id_station_itinerance and "
            "id_pdc_itinerance do not match"
        ),
    ):
        StatiqueFactory.build(
            id_pdc_itinerance="FR147E0042", id_station_itinerance="FR073P00001"
        )

    # Should be a valid usage
    StatiqueFactory.build(
        id_pdc_itinerance="FR073E0042", id_station_itinerance="FR073P00001"
    )

    # Default factory behavior should be consistent
    StatiqueFactory.build()


def test_statique_model_num_pdl():
    """Test statique model accept various num_pdf patterns."""
    statique = StatiqueFactory.build(num_pdl="0" * 14)
    assert statique.num_pdl == "0" * 14

    statique = StatiqueFactory.build(num_pdl="66666/E2/0000001")
    assert statique.num_pdl == "66666/E2/0000001"

    with pytest.raises(ValueError, match="String should have at most 64 characters"):
        StatiqueFactory.build(num_pdl="a" * 65)


def test_statique_model_date_maj():
    """Test statique model accepts only a `date_maj` not in the future."""
    today = datetime.now(timezone.utc).date()
    statique = StatiqueFactory.build(date_maj=today)
    assert statique.date_maj == today

    yesterday = today - timedelta(days=1)
    statique = StatiqueFactory.build(date_maj=yesterday)
    assert statique.date_maj == yesterday

    tomorrow = today + timedelta(days=1)
    with pytest.raises(ValueError, match=f"{tomorrow} is in the future"):
        StatiqueFactory.build(date_maj=tomorrow)


def test_statique_model_date_mise_en_service():
    """Test statique model accepts only a `date_mise_en_service` not in the future."""
    today = datetime.now(timezone.utc).date()
    statique = StatiqueFactory.build(date_mise_en_service=today)
    assert statique.date_mise_en_service == today

    yesterday = today - timedelta(days=1)
    statique = StatiqueFactory.build(date_mise_en_service=yesterday)
    assert statique.date_mise_en_service == yesterday

    tomorrow = today + timedelta(days=1)
    with pytest.raises(ValueError, match=f"{tomorrow} is in the future"):
        StatiqueFactory.build(date_mise_en_service=tomorrow)


def test_statique_model_str_fields_strip():
    """Test the Statique model string fields stripping."""
    nom_amenageur = " Foo Inc.  "
    contact_amenageur = " contact@foo.org "
    nom_operateur = " Bar Inc."
    contact_operateur = "contact@bar.org  "
    telephone_operateur = " tel:+33-1-44-27-63-50  "
    nom_enseigne = " Big Company"
    id_station_itinerance = "FR073P00001  "
    id_station_local = " id-01  "
    nom_station = " Station 01  "
    adresse_station = " 1 baker street 75000 PARIS "
    code_insee_commune = "74264 "
    id_pdc_itinerance = "FR073E0042  "
    id_pdc_local = " pdc-01 "
    tarification = " It's Free!  "
    horaires = " Open 24/7  "
    restriction_gabarit = " None (for now)  "
    num_pdl = " 12345678901213  "
    observations = " None (for now)  "

    statique = StatiqueFactory.build(
        nom_amenageur=nom_amenageur,
        contact_amenageur=contact_amenageur,
        nom_operateur=nom_operateur,
        contact_operateur=contact_operateur,
        telephone_operateur=telephone_operateur,
        nom_enseigne=nom_enseigne,
        id_station_itinerance=id_station_itinerance,
        id_station_local=id_station_local,
        nom_station=nom_station,
        adresse_station=adresse_station,
        code_insee_commune=code_insee_commune,
        id_pdc_itinerance=id_pdc_itinerance,
        id_pdc_local=id_pdc_local,
        tarification=tarification,
        horaires=horaires,
        restriction_gabarit=restriction_gabarit,
        num_pdl=num_pdl,
        observations=observations,
    )

    assert statique.nom_amenageur == nom_amenageur.strip()
    assert statique.contact_amenageur == contact_amenageur.strip()
    assert statique.nom_operateur == nom_operateur.strip()
    assert statique.contact_operateur == contact_operateur.strip()
    assert statique.telephone_operateur == telephone_operateur.strip()
    assert statique.nom_enseigne == nom_enseigne.strip()
    assert statique.id_station_itinerance == id_station_itinerance.strip()
    assert statique.id_station_local == id_station_local.strip()
    assert statique.nom_station == nom_station.strip()
    assert statique.adresse_station == adresse_station.strip()
    assert statique.code_insee_commune == code_insee_commune.strip()
    assert statique.id_pdc_itinerance == id_pdc_itinerance.strip()
    assert statique.id_pdc_local == id_pdc_local.strip()
    assert statique.tarification == tarification.strip()
    assert statique.horaires == horaires.strip()
    assert statique.restriction_gabarit == restriction_gabarit.strip()
    assert statique.num_pdl == num_pdl.strip()
    assert statique.observations == observations.strip()


def test_statique_model_defaults():
    """Test the Statique model defaut values (when not provided)."""
    example = StatiqueFactory.build()
    statique = Statique(
        **example.model_dump(
            exclude={
                "nom_amenageur",
                "siren_amenageur",
                "contact_amenageur",
                "nom_operateur",
                "telephone_operateur",
            }
        )
    )

    assert statique.nom_amenageur == "NA"
    assert statique.siren_amenageur == "123456789"
    assert statique.contact_amenageur == "na@example.org"
    assert statique.nom_operateur == "NA"
    assert statique.telephone_operateur == "+33.123456789"
