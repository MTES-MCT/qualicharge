"""QualiCharge SQL module.

This module regroups ORM-free methods used to massively import data.
"""

import json
import logging
from typing_extensions import Optional
import uuid
from threading import local

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

    def __init__(self, df: pd.DataFrame, connection: Connection, flag_new: bool = True):
        """Add table cache keys."""
        self._statique: pd.DataFrame = df

        self._amenageur: pd.DataFrame = None
        self._enseigne: pd.DataFrame = None
        self._localisation: gp.GeoDataFrame = None
        self._operateur: pd.DataFrame = None
        self._pdc: pd.DataFrame = None
        self._station: pd.DataFrame = None

        self.connection: Connection = connection
        if flag_new:
            self._flag_new()

    def __len__(self):
        """Object length corresponds to the static dataframe length."""
        return len(self._statique.index)

    def _flag_new(self):
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
        self._statique["is_new"] = False
        self._statique.loc[self._statique["station_id"].isnull(), "is_new"] = True
        self._statique.loc[self._statique["pointdecharge_id"].isnull(), "is_new"] = True

    @staticmethod
    def _get_fields_for_schema(schema: BaseTimestampedSQLModel):
        """Get Statique fields from a core schema."""
        return list(set(Statique.model_fields.keys()) & set(schema.model_fields.keys()))

    @staticmethod
    def _add_timestamped_model_fields(df: pd.DataFrame):
        """Add required fields for a BaseTimestampedSQLModel."""
        df["id"] = None
        now = pd.Timestamp.now(tz="utc")
        df["created_at"] = now
        df["updated_at"] = now
        return df

    @staticmethod
    def _get_dataframe_for_schema(
        df: pd.DataFrame, schema: BaseTimestampedSQLModel, subset: Optional[str] = None
    ):
        """Extract Schema DataFrame from original Statique DataFrame."""
        df = df[_get_fields_for_schema(schema)]
        df = df.drop_duplicates(subset)
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
        to_save = StatiqueImporter(
            self._statique.loc[self._statique["is_new"]],
            self.connection,
            flag_new=False,
        )
        if not len(to_save):
            return 0

        localisation = to_save.localisation.loc[
            to_save._statique["station_id"].isnull()
        ]
        localisation["id"] = localisation.apply(lambda _: uuid.uuid4(), axis=1)
        # localisation.to_postgis(
        #     "localisation", to_save.connection, if_exists="append", index=False
        # )

        return len(to_save)

    def update(self) -> int:
        """Update existing entries."""
        to_update = StatiqueImporter(
            self._statique.loc[~self._statique["is_new"]],
            self.connection,
            flag_new=False,
        )
        return len(to_update)


def importer(statique: pd.DataFrame, connection: Connection):
    """FIXME."""
    station_ids = statique["id_station_itinerance"].unique()
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
    existing_stations = pd.read_sql(stations_exists_query, connection)
    statique = statique.merge(existing_stations, how="left", on="id_station_itinerance")

    pdc_ids = statique["id_pdc_itinerance"].unique()
    pdc_exists_query = (
        "SELECT id as pointdecharge_id, id_pdc_itinerance "
        "FROM pointdecharge "
        f"WHERE id_pdc_itinerance IN ('{"','".join(pdc_ids)}')"
    )
    existing_pdcs = pd.read_sql(pdc_exists_query, connection)
    statique = statique.merge(existing_pdcs, how="left", on="id_pdc_itinerance")

    to_create = statique.loc[
        statique["station_id"].isnull() | statique["pointdecharge_id"].isnull()
    ]
