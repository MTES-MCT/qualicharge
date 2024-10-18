"""QualiCharge SQL module.

This module regroups ORM-free methods used to massively import data.
"""

import json
import logging
import uuid

import geopandas as gp  # type: ignore
import pandas as pd
from shapely import to_wkt
from shapely.geometry import Point
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData
from typing_extensions import Optional

from ..auth.schemas import User
from ..exceptions import ObjectDoesNotExist, ProgrammingError
from ..models.static import Statique
from .audit import BaseAuditableSQLModel
from .core import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    PointDeCharge,
    Station,
)

logger = logging.getLogger(__name__)


class StatiqueImporter:
    """Statique importer from a Pandas Dataframe."""

    def __init__(
        self, df: pd.DataFrame, connection: Connection, author: Optional[User] = None
    ):
        """Add table cache keys."""
        logger.info("Loading input dataframe containing %d rows", len(df))

        self._statique: pd.DataFrame = df
        self._statique_with_fk: pd.DataFrame = self._statique.copy()
        self._saved_schemas: list[type[BaseAuditableSQLModel]] = []

        self._amenageur: Optional[pd.DataFrame] = None
        self._enseigne: Optional[pd.DataFrame] = None
        self._localisation: gp.GeoDataFrame = None
        self._operateur: Optional[pd.DataFrame] = None
        self._pdc: Optional[pd.DataFrame] = None
        self._station: Optional[pd.DataFrame] = None

        self._operational_units: Optional[pd.DataFrame] = None

        self.connection: Connection = connection
        self.author: Optional[User] = author

    def __len__(self):
        """Object length corresponds to the static dataframe length."""
        return len(self._statique)

    def _add_auditable_model_fields(self, df: pd.DataFrame):
        """Add required fields for a BaseAuditableSQLModel."""
        df["id"] = df.apply(lambda x: uuid.uuid4(), axis=1)
        now = pd.Timestamp.now(tz="utc")
        df["created_at"] = now
        df["updated_at"] = now
        df["created_by_id"] = self.author.id if self.author else None
        df["updated_by_id"] = self.author.id if self.author else None
        return df

    @staticmethod
    def _schema_fk(schema: type[BaseAuditableSQLModel]) -> str:
        """Get expected schema foreign key name."""
        return f"{schema.__table__.name}_id"  # type: ignore[attr-defined]

    @staticmethod
    def _get_schema_fks(schema: type[BaseAuditableSQLModel]) -> list[str]:
        """Get foreign key field names from a schema."""
        return [
            fk.parent.name
            for fk in schema.metadata.tables[schema.__tablename__].foreign_keys  # type: ignore[index]
        ]

    def _get_fields_for_schema(
        self, schema: type[BaseAuditableSQLModel], with_fk: bool = False
    ) -> list[str]:
        """Get Statique fields from a core schema."""
        fields = list(
            set(Statique.model_fields.keys()) & set(schema.model_fields.keys())
        )
        # Auditable model fks should be ignored
        ignored_fks = {"created_by_id", "updated_by_id"}
        if with_fk:
            fields += list(set(self._get_schema_fks(schema)) - ignored_fks)
        return fields

    def _get_dataframe_for_schema(
        self,
        schema: type[BaseAuditableSQLModel],
        subset: Optional[str] = None,
        with_fk: bool = False,
    ):
        """Extract Schema DataFrame from original Statique DataFrame."""
        src = self._statique_with_fk if with_fk else self._statique
        df = src[self._get_fields_for_schema(schema, with_fk=with_fk)]
        df = df.drop_duplicates(subset)
        df = self._add_auditable_model_fields(df)
        return df

    def _add_fk_from_saved_schema(
        self, saved: pd.DataFrame, schema: type[BaseAuditableSQLModel]
    ):
        """Add foreign keys to the statique DataFrame using saved schema."""
        fields = self._get_fields_for_schema(schema)
        # coordonneesXY field cannot be used for merging
        fields = list(set(fields) - {"coordonneesXY"})
        left = self._statique_with_fk
        right = saved[fields + [self._schema_fk(schema)]]
        self._statique_with_fk = left.merge(right, how="left", on=fields)

    def _load_operational_units(self):
        """Query database to get Operational Units."""
        logger.info("Loading operational units from database")
        self._operational_units = pd.read_sql_table(
            "operationalunit", self.connection, columns=["id", "code"]
        )

    def _add_operational_units_fk(self):
        """Add operational units fk in statique with fk dataframe."""
        logger.info("Merging operational unit foreign keys")

        if self._operational_units is not None:
            logger.warning("Operational unit foreign keys have already been set")
            return

        self._load_operational_units()

        left = self._statique_with_fk
        left["code"] = left["id_station_itinerance"].str.slice(stop=5)
        left = left.merge(self._operational_units, how="left", on="code")
        left.drop(columns="code", inplace=True)
        left.rename(columns={"id": "operational_unit_id"}, inplace=True)

        if pd.isnull(left["operational_unit_id"]).any():
            raise ObjectDoesNotExist("Operational units should be created first")
        self._statique_with_fk = left

    @property
    def amenageur(self) -> pd.DataFrame:
        """Get Amenageur Dataframe."""
        if self._amenageur is None:
            self._amenageur = self._get_dataframe_for_schema(Amenageur)
        return self._amenageur

    @property
    def enseigne(self) -> pd.DataFrame:
        """Get Enseigne Dataframe."""
        if self._enseigne is None:
            self._enseigne = self._get_dataframe_for_schema(Enseigne)
        return self._enseigne

    @property
    def localisation(self) -> pd.DataFrame:
        """Get localisation DataFrame."""
        if self._localisation is None:
            df = self._get_dataframe_for_schema(Localisation)
            # We need a WKT representation for bulk insertion
            df["coordonneesXY"] = (
                df["coordonneesXY"].map(json.loads).map(Point).map(to_wkt)
            )
            self._localisation = df
        return self._localisation

    @property
    def operateur(self) -> pd.DataFrame:
        """Get Operateur Dataframe."""
        if self._operateur is None:
            self._operateur = self._get_dataframe_for_schema(Operateur)
        return self._operateur

    @property
    def pdc(self) -> pd.DataFrame:
        """Get PointDeCharge Dataframe."""
        if self._pdc is None:
            self._pdc = self._get_dataframe_for_schema(PointDeCharge, with_fk=True)
        return self._pdc

    @property
    def station(self) -> pd.DataFrame:
        """Get Station Dataframe."""
        if self._station is None:
            self._station = self._get_dataframe_for_schema(Station, with_fk=True)
        return self._station

    def _save_schema(
        self,
        df: pd.DataFrame,
        schema: type[BaseAuditableSQLModel],
        constraint: Optional[str] = None,
        index_elements: Optional[list[str]] = None,
        chunksize: int = 1000,
    ) -> pd.DataFrame:
        """Save given dataframe records to the corresponding schema."""
        logger.info("Saving schema %s (%d rows)", schema.__qualname__, len(df))

        if schema in self._saved_schemas:
            raise ProgrammingError(
                (
                    "You cannot save the same schema more than once. "
                    "You should create a new StatiqueImporter instance instead."
                )
            )

        schema_table = Table(
            schema.__table__.name,  # type: ignore[attr-defined]
            MetaData(),
            autoload_with=self.connection,
        )

        fks = pd.Series()
        for chunk in [df[i : i + chunksize] for i in range(0, len(df), chunksize)]:
            stmt = insert(schema_table).values(chunk.to_dict("records"))
            updates_on_conflict = {
                f: stmt.excluded.get(f)
                for f in self._get_fields_for_schema(schema, with_fk=True)
            }
            updates_on_conflict.update({
                "updated_at": stmt.excluded.updated_at,
                "updated_by_id": stmt.excluded.updated_by_id,
            })
            stmt = stmt.on_conflict_do_update(
                constraint=constraint,
                index_elements=index_elements,
                set_=updates_on_conflict,
            )
            stmt_ret = stmt.returning(schema_table.c.id)

            result = self.connection.execute(stmt_ret)
            fks = pd.concat(
                [
                    fks,
                    pd.Series(data=[row.id for row in result.all()], index=chunk.index),
                ]
            )

        # Leave the original dataframe untouched
        cp = df.copy(deep=True)
        cp.insert(0, self._schema_fk(schema), fks)
        self._add_fk_from_saved_schema(cp, schema)
        self._saved_schemas += [schema]

        return cp

    def save(self):
        """Save (or update) statique entries."""
        self._add_operational_units_fk()

        self._save_schema(
            self.amenageur,
            Amenageur,
            constraint="amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key",
        )
        self._save_schema(
            self.operateur,
            Operateur,
            constraint="operateur_nom_operateur_contact_operateur_telephone_operate_key",
        )
        self._save_schema(
            self.enseigne,
            Enseigne,
            constraint="enseigne_nom_enseigne_key",
        )
        self._save_schema(
            self.localisation,
            Localisation,
            constraint="localisation_coordonneesXY_key",
        )
        self._save_schema(
            self.station,
            Station,
            index_elements=["id_station_itinerance"],
        )
        self._save_schema(
            self.pdc,
            PointDeCharge,
            index_elements=["id_pdc_itinerance"],
        )
