"""QualiCharge SQL module.

This module regroups ORM-free methods used to massively import data.
"""

import json
import logging

import geopandas as gp
import pandas as pd
from shapely.geometry import Point
from sqlalchemy.engine import Connection

from ..models.static import Statique
from . import BaseTimestampedSQLModel
from .core import Amenageur, Enseigne, Localisation, Operateur, PointDeCharge, Station

logger = logging.getLogger(__name__)


class StatiqueImporter:
    """Statique model data frame."""

    def __init__(self, df: pd.DataFrame, connection: Connection):
        """Add table cache keys."""
        self._statique: pd.DataFrame = df

        self._amenageur: pd.DataFrame = None
        self._enseigne: pd.DataFrame = None
        self._localisation: gp.GeoDataFrame = None
        self._operateur: pd.DataFrame = None
        self._pdc: pd.DataFrame = None
        self._station: pd.DataFrame = None

        self.connection: Connection = connection
        self.flag_new()

    def flag_new(self):
        """Add existing PDC or Station (and related)."""
        station_ids = self._statique["id_station_itinerance"].unique()
        stations_exists_query = (
            "SELECT "
            "id as station_id, "
            "amenageur_id, "
            "operateur_id, "
            "enseigne_id, "
            "localisation_id, "
            "operational_unit_id, "
            "id_station_itinerance "
            "FROM station "
            "WHERE id_station_itinerance IN "
            f"('{"','".join(station_ids)}')"
        )
        existing_stations = pd.read_sql(stations_exists_query, self.connection)
        self._statique = self._statique.merge(
            existing_stations, how="left", on="id_station_itinerance"
        )

        pdc_ids = self._statique["id_pdc_itinerance"].unique()
        pdc_exists_query = (
            "SELECT id as pointdecharge_id, id_pdc_itinerance "
            "FROM pointdecharge "
            f"WHERE id_pdc_itinerance IN ('{"','".join(pdc_ids)}')"
        )
        existing_pdcs = pd.read_sql(pdc_exists_query, self.connection)
        self._statique = self._statique.merge(
            existing_pdcs, how="left", on="id_pdc_itinerance"
        )
        self._statique["new"] = self._statique.apply(
            lambda x: False if all((x["station_id"], x["pointdecharge_id"])) else True,
            axis=1,
        )

    def _get_fields_for_schema(self, schema: BaseTimestampedSQLModel):
        """Get Statique fields from a core schema."""
        return list(set(Statique.model_fields.keys()) & set(schema.model_fields.keys()))

    def _add_timestamped_model_fields(self, df: pd.DataFrame):
        """Add required fields for a BaseTimestampedSQLModel."""
        df["id"] = None
        now = pd.Timestamp.now(tz="utc")
        df["created_at"] = now
        df["updated_at"] = now
        return df

    def _get_dataframe_for_schema(self, schema: BaseTimestampedSQLModel):
        """Extract Schema DataFrame from original Statique DataFrame."""
        df = self._statique[self._get_fields_for_schema(schema)]
        df = df.drop_duplicates()
        df = self._add_timestamped_model_fields(df)
        return df

    @property
    def amenageur(self):
        """Get Amenageur Dataframe."""
        if self._amenageur is None:
            self._amenageur = self._get_dataframe_for_schema(Amenageur)
        return self._amenageur

    @property
    def enseigne(self):
        """Get Enseigne Dataframe."""
        if self._enseigne is None:
            self._enseigne = self._get_dataframe_for_schema(Enseigne)
        return self._enseigne

    @property
    def localisation(self):
        """Get localisation DataFrame."""
        if self._localisation is None:
            df = self._get_dataframe_for_schema(Localisation)
            df["geometry"] = df.apply(
                lambda x: Point(*json.loads(x["coordonneesXY"])), axis=1
            )
            df.drop(columns="coordonneesXY", inplace=True)
            df.rename(columns={"geometry": "coordonneesXY"}, inplace=True)
            self._localisation = gp.GeoDataFrame(
                df, crs="EPSG:4326", geometry="coordonneesXY"
            )
        return self._localisation

    @property
    def operateur(self):
        """Get Operateur Dataframe."""
        if self._operateur is None:
            self._operateur = self._get_dataframe_for_schema(Operateur)
        return self._operateur

    @property
    def pdc(self):
        """Get PointDeCharge Dataframe."""
        if self._pdc is None:
            self._pdc = self._get_dataframe_for_schema(PointDeCharge)
        return self._pdc

    @property
    def station(self):
        """Get Station Dataframe."""
        if self._station is None:
            self._station = self._get_dataframe_for_schema(Station)
        return self._station

    def save(self) -> int:
        """Save new entries."""
        to_save = self._statique.loc[self._statique["new"]]
        return len(to_save.index)

    def update(self) -> int:
        """Update existing entries."""
        to_update = self._statique.loc[~self._statique["new"]]
        return len(to_update.index)
