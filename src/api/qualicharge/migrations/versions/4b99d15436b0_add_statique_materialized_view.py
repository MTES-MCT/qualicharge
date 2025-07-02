"""Add statique materialized view

Revision ID: 4b99d15436b0
Revises: 9ae109e209c9
Create Date: 2025-01-16 15:02:04.004411

"""

from typing import Sequence, Union

from alembic import op
from geoalchemy2.functions import ST_GeomFromEWKB
from geoalchemy2.types import Geometry
from sqlalchemy import MetaData, select
from sqlalchemy import cast as SA_cast
from sqlalchemy.schema import Column as SAColumn
from sqlalchemy_utils.view import CreateView, DropView

from qualicharge.schemas.core import StatiqueMV, _StatiqueMV

# revision identifiers, used by Alembic.
revision: str = "4b99d15436b0"
down_revision: Union[str, None] = "9ae109e209c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_tables(connection):
    """Get SQLAlchemy tables."""
    metadata = MetaData()
    metadata.reflect(bind=connection)
    return metadata.tables


def upgrade() -> None:
    """Create the Statique Materialized view and related indexes."""
    connection = op.get_bind()
    tables = get_tables(connection)
    pointdecharge = tables["pointdecharge"]
    amenageur = tables["amenageur"]
    operateur = tables["operateur"]
    enseigne = tables["enseigne"]
    station = tables["station"]
    localisation = tables["localisation"]

    selectable = (
        select(  # type: ignore[call-overload, misc]
            pointdecharge.c.id.label("pdc_id"),
            pointdecharge.c.updated_at.label("pdc_updated_at"),
            amenageur.c.nom_amenageur,
            amenageur.c.siren_amenageur,
            amenageur.c.contact_amenageur,
            operateur.c.nom_operateur,
            operateur.c.contact_operateur,
            operateur.c.telephone_operateur,
            enseigne.c.nom_enseigne,
            station.c.id_station_itinerance,
            station.c.id_station_local,
            station.c.nom_station,
            station.c.implantation_station,
            localisation.c.adresse_station,
            localisation.c.code_insee_commune,
            SA_cast(
                localisation.c.coordonneesXY,
                Geometry(
                    geometry_type="POINT",
                    # WGS84 coordinates system
                    srid=4326,
                    spatial_index=False,
                ),
            ).label("coordonneesXY"),
            station.c.nbre_pdc,
            pointdecharge.c.id_pdc_itinerance,
            pointdecharge.c.id_pdc_local,
            pointdecharge.c.puissance_nominale,
            pointdecharge.c.prise_type_ef,
            pointdecharge.c.prise_type_2,
            pointdecharge.c.prise_type_combo_ccs,
            pointdecharge.c.prise_type_chademo,
            pointdecharge.c.prise_type_autre,
            pointdecharge.c.gratuit,
            pointdecharge.c.paiement_acte,
            pointdecharge.c.paiement_cb,
            pointdecharge.c.paiement_autre,
            pointdecharge.c.tarification,
            station.c.condition_acces,
            pointdecharge.c.reservation,
            station.c.horaires,
            pointdecharge.c.accessibilite_pmr,
            pointdecharge.c.restriction_gabarit,
            station.c.station_deux_roues,
            station.c.raccordement,
            station.c.num_pdl,
            station.c.date_mise_en_service,
            pointdecharge.c.observations,
            station.c.date_maj,
            pointdecharge.c.cable_t2_attache,
        )
        .select_from(pointdecharge)
        .join(station)
        .join(amenageur)
        .join(operateur)
        .join(enseigne)
        .join(localisation)
    )

    op.execute(CreateView("statique", selectable, materialized=True))
    op.create_geospatial_index(
        "idx_statique_coordonneesXY",
        _StatiqueMV.__table__.fullname,
        [ST_GeomFromEWKB(StatiqueMV.coordonneesXY)],
        unique=False,
        postgresql_using="gist",
    )
    for idx in _StatiqueMV.__table__.indexes:
        idx.create(op.get_bind())


def downgrade() -> None:
    """Delete the Statique Materialized View."""

    op.execute(DropView("statique", materialized=True, cascade=True))
