"""QualiCharge schemas utilities tests."""

from random import sample
from typing import cast

import pytest
from pydantic_extra_types.coordinate import Coordinate
from sqlalchemy import Column as SAColumn
from sqlalchemy import func
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import GroupOperationalUnit, UserGroup
from qualicharge.exceptions import (
    DatabaseQueryException,
    IntegrityError,
    ObjectDoesNotExist,
)
from qualicharge.factories.static import (
    AmenageurFactory,
    StationFactory,
    StatiqueFactory,
)
from qualicharge.schemas.core import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    OperationalUnit,
    PointDeCharge,
    Station,
)
from qualicharge.schemas.utils import (
    EntryStatus,
    are_pdcs_allowed_for_user,
    build_statique,
    get_or_create,
    is_pdc_allowed_for_user,
    list_statique,
    pdc_to_statique,
    save_schema_from_statique,
    save_statique,
    save_statiques,
    update_statique,
)


def test_get_or_create(db_session):
    """Test get_or_create utility."""
    amenageur = AmenageurFactory.build()

    # Create case
    status, db_entry = get_or_create(db_session, amenageur)
    assert status == EntryStatus.CREATED
    assert db_entry.id is not None
    assert db_entry.id == amenageur.id
    assert db_entry.nom_amenageur == amenageur.nom_amenageur
    assert db_entry.siren_amenageur == amenageur.siren_amenageur
    assert db_entry.contact_amenageur == amenageur.contact_amenageur

    # Get case
    status, db_entry = get_or_create(db_session, amenageur)
    assert status == EntryStatus.EXISTS
    assert db_entry.id == amenageur.id
    assert db_entry.nom_amenageur == amenageur.nom_amenageur
    assert db_entry.siren_amenageur == amenageur.siren_amenageur
    assert db_entry.contact_amenageur == amenageur.contact_amenageur


def test_get_or_create_update(db_session):
    """Test get_or_create utility with update=True."""
    station = StationFactory.build(num_pdl="01234567890123")

    # Create station
    status, db_entry = get_or_create(
        db_session, station, fields={"id_station_itinerance"}
    )
    assert status == EntryStatus.CREATED
    assert db_entry.num_pdl == "01234567890123"

    # Update case
    num_pdl = "12345678901234"
    to_update = station.model_copy(update={"num_pdl": num_pdl})
    status, db_entry = get_or_create(
        db_session, to_update, fields={"id_station_itinerance"}, update=True
    )
    assert status == EntryStatus.UPDATED
    assert db_entry.id == station.id
    assert db_entry.num_pdl == num_pdl


def test_get_or_create_with_explicit_fields_selection(db_session):
    """Test get_or_create utility using explicit fields selection."""
    amenageur = AmenageurFactory.build()
    fields = {
        "contact_amenageur",
    }

    # Create case
    status, db_entry = get_or_create(db_session, amenageur, fields=fields)
    assert status == EntryStatus.CREATED
    assert db_entry.id is not None
    assert db_entry.id == amenageur.id
    assert db_entry.nom_amenageur == amenageur.nom_amenageur
    assert db_entry.siren_amenageur == amenageur.siren_amenageur
    assert db_entry.contact_amenageur == amenageur.contact_amenageur

    # Get case
    status, db_entry = get_or_create(db_session, amenageur, fields=fields)
    assert status == EntryStatus.EXISTS
    assert db_entry.id == amenageur.id
    assert db_entry.nom_amenageur == amenageur.nom_amenageur
    assert db_entry.siren_amenageur == amenageur.siren_amenageur
    assert db_entry.contact_amenageur == amenageur.contact_amenageur


def test_get_or_create_with_multiple_existing_entries(db_session):
    """Test get_or_create utility when multiple entries exist."""
    AmenageurFactory.__session__ = db_session

    nom_amenageur = "ACME Inc."
    amenageurs = AmenageurFactory.create_batch_sync(2, nom_amenageur=nom_amenageur)

    with pytest.raises(
        DatabaseQueryException,
        match="Multiple results found for input fields {'nom_amenageur'}",
    ):
        get_or_create(db_session, amenageurs[0], fields={"nom_amenageur"})


def test_save_schema_from_statique(db_session):
    """Test save_schema_from_statique utility."""
    statique = StatiqueFactory.build()

    # Create entry
    status, amenageur = save_schema_from_statique(db_session, Amenageur, statique)
    assert amenageur.id is not None
    assert status == EntryStatus.CREATED

    # Check database entry
    db_amenageur = db_session.exec(
        select(Amenageur).where(Amenageur.id == amenageur.id)
    ).one_or_none()
    assert db_amenageur == amenageur


def test_save_statique(db_session):
    """Test save_statique utility."""
    statique = StatiqueFactory.build()

    db_statique = save_statique(db_session, statique)
    assert statique == db_statique

    amenageur = db_session.exec(select(Amenageur)).first()
    operateur = db_session.exec(select(Operateur)).first()
    enseigne = db_session.exec(select(Enseigne)).first()
    localisation = db_session.exec(select(Localisation)).first()
    station = db_session.exec(select(Station)).first()
    pdc = db_session.exec(select(PointDeCharge)).first()

    assert db_statique.nom_amenageur == amenageur.nom_amenageur
    assert db_statique.siren_amenageur == amenageur.siren_amenageur
    assert db_statique.contact_amenageur == amenageur.contact_amenageur

    assert db_statique.nom_operateur == operateur.nom_operateur
    assert db_statique.contact_operateur == operateur.contact_operateur
    assert db_statique.telephone_operateur == operateur.telephone_operateur

    assert db_statique.nom_enseigne == enseigne.nom_enseigne

    assert db_statique.adresse_station == localisation.adresse_station
    assert db_statique.code_insee_commune == localisation.code_insee_commune
    assert db_statique.coordonneesXY == Localisation._wkb_to_coordinates(
        localisation.coordonneesXY
    )

    assert db_statique.id_station_itinerance == station.id_station_itinerance
    assert db_statique.id_station_local == station.id_station_local
    assert db_statique.nom_station == station.nom_station
    assert db_statique.implantation_station == station.implantation_station
    assert db_statique.nbre_pdc == station.nbre_pdc
    assert db_statique.condition_acces == station.condition_acces
    assert db_statique.horaires == station.horaires
    assert db_statique.station_deux_roues == station.station_deux_roues
    assert db_statique.raccordement == station.raccordement
    assert db_statique.num_pdl == station.num_pdl
    assert db_statique.date_maj == station.date_maj
    assert db_statique.date_mise_en_service == station.date_mise_en_service

    assert db_statique.id_pdc_itinerance == pdc.id_pdc_itinerance
    assert db_statique.id_pdc_local == pdc.id_pdc_local
    assert db_statique.puissance_nominale == pdc.puissance_nominale
    assert db_statique.prise_type_ef == pdc.prise_type_ef
    assert db_statique.prise_type_2 == pdc.prise_type_2
    assert db_statique.prise_type_combo_ccs == pdc.prise_type_combo_ccs
    assert db_statique.prise_type_chademo == pdc.prise_type_chademo
    assert db_statique.prise_type_autre == pdc.prise_type_autre
    assert db_statique.gratuit == pdc.gratuit
    assert db_statique.paiement_acte == pdc.paiement_acte
    assert db_statique.paiement_cb == pdc.paiement_cb
    assert db_statique.paiement_autre == pdc.paiement_autre
    assert db_statique.tarification == pdc.tarification
    assert db_statique.reservation == pdc.reservation
    assert db_statique.accessibilite_pmr == pdc.accessibilite_pmr
    assert db_statique.restriction_gabarit == pdc.restriction_gabarit
    assert db_statique.observations == pdc.observations
    assert db_statique.cable_t2_attache == pdc.cable_t2_attache


def test_update_statique(db_session):
    """Test update_statique utility."""
    id_pdc_itinerance = "FR911E1111ER1"
    statique = StatiqueFactory.build(
        id_pdc_itinerance=id_pdc_itinerance,
        nom_amenageur="ACME Inc.",
        nom_operateur="ACME Inc.",
        nom_enseigne="ACME Inc.",
        coordonneesXY=Coordinate(-1.0, 1.0),
        station_deux_roues=False,
        cable_t2_attache=False,
    )
    db_statique = save_statique(db_session, statique)
    assert statique == db_statique

    assert db_session.exec(select(func.count(Operateur.id))).one() == 1
    assert db_session.exec(select(func.count(Enseigne.id))).one() == 1
    assert db_session.exec(select(func.count(Amenageur.id))).one() == 1
    assert db_session.exec(select(func.count(Localisation.id))).one() == 1
    assert db_session.exec(select(func.count(Station.id))).one() == 1
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 1

    # Update statique fields
    statique.contact_operateur = "john@doe.com"
    statique.nom_amenageur = "Magma Corp."
    statique.nom_operateur = "Magma Corp."
    statique.nom_enseigne = "Magma Corp."
    statique.coordonneesXY = Coordinate(1.0, 2.0)
    statique.station_deux_roues = True
    statique.cable_t2_attache = True

    db_statique = update_statique(db_session, statique.id_pdc_itinerance, statique)
    assert db_statique.contact_operateur == "john@doe.com"
    assert db_statique.nom_amenageur == "Magma Corp."
    assert db_statique.nom_operateur == "Magma Corp."
    assert db_statique.nom_enseigne == "Magma Corp."
    assert db_statique.coordonneesXY == Coordinate(1.0, 2.0)
    assert db_statique.station_deux_roues
    assert db_statique.cable_t2_attache

    # We expect to create a new operator that will be linked to this statique
    expected = 2
    assert db_session.exec(select(func.count(Operateur.id))).one() == expected
    assert db_session.exec(select(func.count(Enseigne.id))).one() == expected
    assert db_session.exec(select(func.count(Amenageur.id))).one() == expected
    assert db_session.exec(select(func.count(Localisation.id))).one() == 1
    assert db_session.exec(select(func.count(Station.id))).one() == 1
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 1


def test_update_statique_with_wrong_pdc_id_itinerance(db_session):
    """Test the update_statique utility with wrong id_pdc_itinerance."""
    with pytest.raises(
        IntegrityError,
        match="Cannot update statique with a different id_pdc_itinerance",
    ):
        update_statique(db_session, "foo", StatiqueFactory.build())


def test_update_statique_when_statique_does_not_exist(db_session):
    """Test the update_statique utility when statique does not exist."""
    statique = StatiqueFactory.build()
    with pytest.raises(
        ObjectDoesNotExist, match="Statique with id_pdc_itinerance does not exist"
    ):
        update_statique(db_session, statique.id_pdc_itinerance, statique)


def test_save_statiques(db_session):
    """Test save_statiques utility."""
    statiques = sorted(StatiqueFactory.batch(2), key=lambda s: s.id_pdc_itinerance)
    save_statiques(db_session, statiques)

    db_statiques = list(list_statique(db_session))
    assert db_statiques[0] == statiques[0]
    assert db_statiques[1] == statiques[1]


def test_save_statiques_with_same_amenageur(db_session):
    """Test save_statiques utility with the same amenageur."""
    statiques = sorted(
        StatiqueFactory.batch(
            2,
            nom_amenageur="ACME Inc.",
            siren_amenageur="123456789",
            contact_amenageur="john.doe@acme.com",
        ),
        key=lambda s: s.id_pdc_itinerance,
    )
    save_statiques(db_session, statiques)

    db_statiques = list(list_statique(db_session))
    assert db_statiques[0] == statiques[0]
    assert db_statiques[1] == statiques[1]

    # We should only have created one Amenageur and two PointDeCharge
    assert db_session.exec(select(func.count(Amenageur.siren_amenageur))).one() == 1
    assert db_session.exec(
        select(func.count(PointDeCharge.id_pdc_itinerance))
    ).one() == len(statiques)


def test_save_statiques_with_same_localisation(db_session):
    """Test save_statiques utility with the same localisation."""
    statiques = sorted(
        StatiqueFactory.batch(
            2,
            adresse_station="221B Baker street, London",
            code_insee_commune="21231",
            coordonneesXY="[-3.129447,45.700327]",
        ),
        key=lambda s: s.id_pdc_itinerance,
    )
    save_statiques(db_session, statiques)

    db_statiques = list(list_statique(db_session))
    assert db_statiques[0] == statiques[0]
    assert db_statiques[1] == statiques[1]

    # We should only have created one Amenageur and two PointDeCharge
    assert db_session.exec(select(func.count(Localisation.adresse_station))).one() == 1
    assert db_session.exec(
        select(func.count(PointDeCharge.id_pdc_itinerance))
    ).one() == len(statiques)


def test_save_statiques_with_same_amenageur_twice(db_session):
    """Test save_statiques utility with the same amenageur, twice."""
    statiques = sorted(
        StatiqueFactory.batch(
            2,
            nom_amenageur="ACME Inc.",
            siren_amenageur="123456789",
            contact_amenageur="john.doe@acme.com",
        ),
        key=lambda s: s.id_pdc_itinerance,
    )
    save_statiques(db_session, statiques)

    db_statiques = list(list_statique(db_session))
    assert db_statiques[0] == statiques[0]
    assert db_statiques[1] == statiques[1]

    # We should only have created one Amenageur and two PointDeCharge
    assert db_session.exec(select(func.count(Amenageur.siren_amenageur))).one() == 1
    assert db_session.exec(
        select(func.count(PointDeCharge.id_pdc_itinerance))
    ).one() == len(statiques)


def test_build_statique(db_session):
    """Test build_statique utility."""
    # Create a Statique instance and save it to database
    statique = StatiqueFactory.build()
    save_statique(db_session, statique)

    # Rebuild statique from database records
    db_statique = build_statique(db_session, statique.id_pdc_itinerance)
    assert db_statique == statique

    # Create another statique and rebuild both
    another_statique = StatiqueFactory.build()
    save_statique(db_session, another_statique)
    db_statique = build_statique(db_session, statique.id_pdc_itinerance)
    assert db_statique == statique
    db_another_statique = build_statique(db_session, another_statique.id_pdc_itinerance)
    assert db_another_statique == another_statique


def test_build_statique_when_statique_does_not_exist(db_session):
    """Test build_statique utility when statique does not exist."""
    statique = StatiqueFactory.build()
    with pytest.raises(
        ObjectDoesNotExist, match="Statique with id_pdc_itinerance does not exist"
    ):
        build_statique(db_session, statique.id_pdc_itinerance)


def test_list_statique(db_session):
    """Test list_statique utility."""
    # Create statiques in database
    ids_pdc_itinerance = []
    n_statiques = 22
    for _ in range(n_statiques):
        statique = StatiqueFactory.build()
        ids_pdc_itinerance.append(statique.id_pdc_itinerance)
        save_statique(db_session, statique)
    ids_pdc_itinerance.sort()

    limit = 10
    for offset in range(0, 30, 10):
        statiques = list(list_statique(db_session, offset=offset, limit=limit))
        size = limit if offset + limit < n_statiques else n_statiques - offset
        assert len(statiques) == size
        assert {statique.id_pdc_itinerance for statique in statiques} == set(
            ids_pdc_itinerance[offset : offset + size]
        )


def test_list_statique_operational_units_filtering(db_session):
    """Test list_statique utility filtering by operational units."""
    # Save random statiques
    n_statiques = 20
    save_statiques(db_session, StatiqueFactory.batch(n_statiques))

    # Select operational units linked to stations
    operational_units = db_session.exec(
        select(OperationalUnit)
        .join_from(
            Station, OperationalUnit, Station.operational_unit_id == OperationalUnit.id
        )
        .where(Station.operational_unit_id is not None)
        .distinct()
    ).all()

    # Select operational units randomly
    n_operational_units = 3
    selected_operational_units = sample(operational_units, n_operational_units)

    # Expected PDC
    selected_pdcs = db_session.exec(
        select(PointDeCharge)
        .join_from(PointDeCharge, Station, PointDeCharge.station_id == Station.id)
        .join_from(
            Station, OperationalUnit, Station.operational_unit_id == OperationalUnit.id
        )
        .where(
            cast(SAColumn, OperationalUnit.id).in_(
                ou.id for ou in selected_operational_units
            )
        )
    ).all()
    expected_statiques = [pdc_to_statique(pdc) for pdc in selected_pdcs]
    statiques = list(
        list_statique(db_session, operational_units=selected_operational_units)
    )
    assert len(statiques) == len(expected_statiques)
    assert {s.id_pdc_itinerance for s in statiques} == {
        s.id_pdc_itinerance for s in expected_statiques
    }


def test_is_pdc_allowed_for_user(db_session):
    """Test the is_pdc_allowed_for_user utility."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    id_pdc_itinerance = "FRS63E0001"
    id_station_itinerance = "FRS63P0001"

    # Superuser
    user = UserFactory.create_sync(is_superuser=True)
    assert is_pdc_allowed_for_user(id_pdc_itinerance, user) is True

    # Normal user with no assigned operational units
    user = UserFactory.create_sync(is_superuser=False)
    assert user.operational_units == []
    assert is_pdc_allowed_for_user(id_pdc_itinerance, user) is False

    # Normal user with matching assigned operational units
    save_statique(
        db_session,
        StatiqueFactory.build(
            id_pdc_itinerance=id_pdc_itinerance,
            id_station_itinerance=id_station_itinerance,
        ),
    )
    group = GroupFactory.create_sync()
    db_session.add(
        GroupOperationalUnit(
            group_id=group.id,
            operational_unit_id=db_session.exec(
                select(OperationalUnit.id).where(
                    OperationalUnit.code == id_pdc_itinerance[:5]
                )
            ).one(),
        )
    )
    user = UserFactory.create_sync(is_superuser=False)
    db_session.add(UserGroup(user_id=user.id, group_id=group.id))
    assert is_pdc_allowed_for_user(id_pdc_itinerance, user) is True

    # Normal user with assigned operational units not linked to the point of charge
    group = GroupFactory.create_sync()
    db_session.add(
        GroupOperationalUnit(
            group_id=group.id,
            operational_unit_id=db_session.exec(
                select(OperationalUnit.id).where(OperationalUnit.code == "FRS72")
            ).one(),
        )
    )
    user = UserFactory.create_sync(is_superuser=False)
    db_session.add(UserGroup(user_id=user.id, group_id=group.id))
    assert is_pdc_allowed_for_user(id_pdc_itinerance, user) is False


def test_are_pdcs_allowed_for_user(db_session):
    """Test the are_pdcs_allowed_for_user utility."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    # Superuser
    user = UserFactory.create_sync(is_superuser=True)
    assert are_pdcs_allowed_for_user(["FRFASE001", "FRS63E0001"], user) is True
    assert are_pdcs_allowed_for_user({"FRFASE001", "FRS63E0001"}, user) is True

    # Normal user with no assigned operational units
    user = UserFactory.create_sync(is_superuser=False)
    assert user.operational_units == []
    assert are_pdcs_allowed_for_user(["FRFASE001", "FRS63E0001"], user) is False

    # Create groups linked to Operational Units
    groups = GroupFactory.create_batch_sync(3)
    operational_units = db_session.exec(select(OperationalUnit).limit(3)).all()
    for group, operational_unit in zip(groups, operational_units, strict=True):
        db_session.add(
            GroupOperationalUnit(
                group_id=group.id, operational_unit_id=operational_unit.id
            )
        )

    # And a user belonging to groups linked to those operational units
    user = UserFactory.create_sync(is_superuser=False, groups=groups)
    assert {ou.code for ou in user.operational_units} == {
        ou.code for ou in operational_units
    }

    ids_pdc_itinerance = [f"{ou.code}P001" for ou in operational_units]
    assert are_pdcs_allowed_for_user(ids_pdc_itinerance, user) is True
    assert are_pdcs_allowed_for_user(ids_pdc_itinerance + ["FRFASP0001"], user) is False
