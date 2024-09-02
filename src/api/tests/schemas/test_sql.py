"""Tests for QualiCharge SQL importer."""

from io import StringIO
from math import isclose

import pandas as pd
import pytest
from sqlalchemy import func
from sqlmodel import select

from qualicharge.exceptions import ObjectDoesNotExist, ProgrammingError
from qualicharge.factories.static import StatiqueFactory
from qualicharge.schemas.core import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    PointDeCharge,
    Station,
)
from qualicharge.schemas.sql import StatiqueImporter


def test_statique_importer_properties(db_session):
    """Test the StatiqueImporter properties."""
    # Create statique data to import
    size = 5
    statiques = StatiqueFactory.batch(size=size)
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )
    importer = StatiqueImporter(df, db_session.connection())

    assert len(importer) == size
    assert len(importer.amenageur.index) == size
    assert len(importer.enseigne.index) == size
    assert len(importer.operateur.index) == size
    assert len(importer.localisation.index) == size

    with pytest.raises(KeyError, match="not in index"):
        assert importer.station

    with pytest.raises(KeyError, match="not in index"):
        assert importer.pdc


def test_statique_importer_unknown_operational_unit(db_session):
    """Test the StatiqueImporter when dealing with an unknown operational unit."""
    size = 5
    statiques = StatiqueFactory.batch(size=size)
    statiques[1].id_station_itinerance = f"DE{statiques[1].id_station_itinerance[2:]}"
    statiques[3].id_station_itinerance = f"ES{statiques[3].id_station_itinerance[2:]}"
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )

    importer = StatiqueImporter(df, db_session.connection())
    with pytest.raises(
        ObjectDoesNotExist, match="Operational units should be created first"
    ):
        importer.save()


def test_statique_importer_save_or_update(db_session):
    """Test the StatiqueImporter save (or update) feature."""
    # Create statique data to import
    size = 5
    statiques = StatiqueFactory.batch(size=size)
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )
    importer = StatiqueImporter(df, db_session.connection())

    # No database records exist yet
    assert db_session.exec(select(func.count(Amenageur.id))).one() == 0
    assert db_session.exec(select(func.count(Enseigne.id))).one() == 0
    assert db_session.exec(select(func.count(Localisation.id))).one() == 0
    assert db_session.exec(select(func.count(Operateur.id))).one() == 0
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 0
    assert db_session.exec(select(func.count(Station.id))).one() == 0

    # Save to database
    importer.save()

    # Assert we've created expected records
    assert db_session.exec(select(func.count(Amenageur.id))).one() == size
    assert db_session.exec(select(func.count(Enseigne.id))).one() == size
    assert db_session.exec(select(func.count(Localisation.id))).one() == size
    assert db_session.exec(select(func.count(Operateur.id))).one() == size
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size

    # Check save() cannot be used more than once
    with pytest.raises(
        ProgrammingError, match="You cannot save the same schema more than once."
    ):
        importer.save()

    # Save it again and make sure we've updated records
    importer = StatiqueImporter(df, db_session.connection())
    importer.save()

    # Assert we've created expected records
    assert (
        db_session.exec(select(func.count(Amenageur.id))).one() >= size
    )  # too permissive :(
    assert db_session.exec(select(func.count(Enseigne.id))).one() == size
    assert db_session.exec(select(func.count(Localisation.id))).one() == size
    assert db_session.exec(select(func.count(Operateur.id))).one() >= size  # ditto
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size


def test_statique_importer_consistency(db_session):
    """Test the StatiqueImporter consistency."""
    # Create statique data to import
    size = 20
    statiques = StatiqueFactory.batch(size=size)
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )
    importer = StatiqueImporter(df, db_session.connection())
    importer.save()

    for statique in statiques:
        pdc = db_session.exec(
            select(PointDeCharge).where(
                PointDeCharge.id_pdc_itinerance == statique.id_pdc_itinerance
            )
        ).one()
        assert pdc.id_pdc_itinerance == statique.id_pdc_itinerance
        assert pdc.id_pdc_local == statique.id_pdc_local
        assert isclose(pdc.puissance_nominale, statique.puissance_nominale)
        assert pdc.prise_type_ef == statique.prise_type_ef
        assert pdc.prise_type_2 == statique.prise_type_2
        assert pdc.prise_type_combo_ccs == statique.prise_type_combo_ccs
        assert pdc.prise_type_chademo == statique.prise_type_chademo
        assert pdc.prise_type_autre == statique.prise_type_autre
        assert pdc.gratuit == statique.gratuit
        assert pdc.paiement_acte == statique.paiement_acte
        assert pdc.paiement_cb == statique.paiement_cb
        assert pdc.paiement_autre == statique.paiement_autre
        assert pdc.tarification == statique.tarification
        assert pdc.reservation == statique.reservation
        assert pdc.accessibilite_pmr == statique.accessibilite_pmr
        assert pdc.restriction_gabarit == statique.restriction_gabarit
        assert pdc.observations == statique.observations
        assert pdc.cable_t2_attache == statique.cable_t2_attache
        assert pdc.station.id_station_itinerance == statique.id_station_itinerance
        assert pdc.station.id_station_local == statique.id_station_local
        assert pdc.station.nom_station == statique.nom_station
        assert pdc.station.implantation_station == statique.implantation_station
        assert pdc.station.nbre_pdc == statique.nbre_pdc
        assert pdc.station.condition_acces == statique.condition_acces
        assert pdc.station.horaires == statique.horaires
        assert pdc.station.station_deux_roues == statique.station_deux_roues
        assert pdc.station.raccordement == statique.raccordement
        assert pdc.station.num_pdl == statique.num_pdl
        assert pdc.station.date_maj == statique.date_maj
        assert pdc.station.date_mise_en_service == statique.date_mise_en_service
        assert pdc.station.amenageur.nom_amenageur == statique.nom_amenageur
        assert pdc.station.amenageur.siren_amenageur == statique.siren_amenageur
        assert pdc.station.amenageur.contact_amenageur == statique.contact_amenageur
        assert pdc.station.operateur.nom_operateur == statique.nom_operateur
        assert pdc.station.operateur.contact_operateur == statique.contact_operateur
        assert pdc.station.operateur.telephone_operateur == statique.telephone_operateur
        assert pdc.station.enseigne.nom_enseigne == statique.nom_enseigne
        assert pdc.station.localisation.adresse_station == statique.adresse_station
        assert (
            pdc.station.localisation.code_insee_commune == statique.code_insee_commune
        )
        assert (
            pdc.station.localisation._wkb_to_coordinates(
                pdc.station.localisation.coordonneesXY
            )
            == statique.coordonneesXY
        )
        assert pdc.station.operational_unit.code == statique.id_station_itinerance[:5]
