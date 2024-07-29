---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.2
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Import IRVE static data

```python
import os
from sqlalchemy import create_engine, text

# Get database URL from the environment
database_url = os.getenv("DATABASE_URL")

# Create a database engine that will be used to generate connections
engine = create_engine(database_url)
```

```python
from pathlib import Path
import uuid

import geopandas as gp
import pandas as pd
```

## Load development dataset

```python
static_file = Path("../../../data/irve-statique.parquet")
static = gp.read_file(static_file)
```

## Handle Enums

```python
from enum import StrEnum

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

enum_to_replace = []
enum_value = []

for enm in (ImplantationStationEnum, ConditionAccesEnum, AccessibilitePMREnum, RaccordementEnum):
    for k in enm:
        enum_to_replace.append(str(k.name))
        enum_value.append(k.value)

print(f"{enum_to_replace=}")
print(f"{enum_value=}")
```

## Transform dataframe and save to database

```python
from typing import Union

from geopandas import GeoDataFrame
from pandas import DataFrame
from sqlalchemy import Engine
from sqlalchemy import types as sa_types


def save(data: Union[DataFrame, GeoDataFrame], engine: Engine, table: str, truncate: bool = False, dtype: dict = None):
    """Save dataframe to database."""
    if truncate:
        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            conn.commit()

    dtype = dtype if dtype else {}
    dtype.update({"id": sa_types.UUID})
    
    to_database = data.to_sql
    if isinstance(data, GeoDataFrame):
        to_database = data.to_postgis
        
    to_database(table, engine, if_exists="append", index=False, dtype=dtype)


def add_timestamped_table_fields(data: Union[DataFrame, GeoDataFrame]) -> Union[DataFrame, GeoDataFrame]:
    """Add required fields for a BaseTimestampedSQLModel."""
    data["id"] = data.apply(lambda x: uuid.uuid4(), axis=1)
    now = pd.Timestamp.now(tz="utc")
    data['created_at'] = now
    data['updated_at'] = now
    return data
```

### Localisation

```python
import json

from shapely.geometry import Point

# Extract Localisation fields
localisation_fields = ["adresse_station", "code_insee_commune", "coordonneesXY"]
localisation = static[localisation_fields]

# Remove duplicates
localisation = localisation.drop_duplicates()

# Transform coordinates to POINT()
localisation["geometry"] = localisation.apply(lambda x: Point(*json.loads(x["coordonneesXY"])), axis=1)
localisation.drop(columns="coordonneesXY", inplace=True)
localisation.rename(columns={"geometry": "coordonneesXY"}, inplace=True)

# Add missing columns (to fit with the ORM)
localisation = add_timestamped_table_fields(localisation)

# Convert to a GeoDataFrame
localisation = gp.GeoDataFrame(localisation, crs="EPSG:4326", geometry="coordonneesXY")
localisation[localisation["code_insee_commune"] == "77018"]
```

```python
save(localisation, engine, "localisation", truncate=True)

# Just to check.
saved = gp.GeoDataFrame.from_postgis("SELECT * FROM localisation", engine, geom_col="coordonneesXY")
saved
```

## Amenageur

```python
# Extract model fields
amenageur_fields = ["nom_amenageur", "siren_amenageur", "contact_amenageur"]
amenageur = static[amenageur_fields]

# Remove duplicates
amenageur = amenageur.drop_duplicates()

# Add missing columns (to fit with the ORM)
amenageur = add_timestamped_table_fields(amenageur)
```

```python
save(amenageur, engine, "amenageur", truncate=True)

saved = pd.read_sql("SELECT * FROM amenageur", engine)
saved
```

### Operateur

```python
# Extract model fields
operateur_fields = ["nom_operateur", "telephone_operateur", "contact_operateur"]
operateur = static[operateur_fields]

# Remove duplicates
operateur = operateur.drop_duplicates()

# Add missing columns (to fit with the ORM)
operateur = add_timestamped_table_fields(operateur)
operateur
```

```python
save(operateur, engine, "operateur", truncate=True)

saved = pd.read_sql("SELECT * FROM operateur", engine)
saved
```

### Enseigne

```python
# Extract model fields
enseigne_fields = ["nom_enseigne",]
enseigne = static[enseigne_fields]

# Remove duplicates
enseigne = enseigne.drop_duplicates()

# Add missing columns (to fit with the ORM)
enseigne = add_timestamped_table_fields(enseigne)
enseigne
```

```python
save(enseigne, engine, "enseigne", truncate=True)

saved = pd.read_sql("SELECT * FROM enseigne", engine)
saved
```

### Get operational units

```python
operational_units = pd.read_sql("SELECT * FROM operationalunit", engine)
operational_units
```

### Handle foreign keys

```python
def add_ids(left: DataFrame, right: DataFrame, fields: list, fk_name: str) -> DataFrame:
    """Add missings related object ids."""
    with_ids = left.merge(right, how="left", on=fields)
    with_ids.drop(columns=["created_at", "updated_at"], inplace=True)
    return with_ids.rename(columns={"id": fk_name})

static_with_ids = add_ids(static, amenageur, amenageur_fields, "amenageur_id")
static_with_ids = add_ids(static_with_ids, operateur, operateur_fields, "operateur_id")
static_with_ids = add_ids(static_with_ids, enseigne, enseigne_fields, "enseigne_id")

# Get back to coordinates as a string for comparison
localisation_with_geom_string = localisation.drop(columns="coordonneesXY")
localisation_with_geom_string["coordonneesXY"] = static.loc[localisation_with_geom_string.index]["coordonneesXY"]

static_with_ids = add_ids(static_with_ids, localisation_with_geom_string, localisation_fields, "localisation_id")
static_with_ids
```

### Station

```python
# Extract model fields
station_fields = [
    "id_station_itinerance",
    "id_station_local",
    "nom_station",
    "implantation_station",
    "nbre_pdc",
    "condition_acces",
    "horaires",
    "station_deux_roues",
    "raccordement",
    "num_pdl",
    "date_maj",
    "date_mise_en_service",
]
station = static[station_fields]

# Remove duplicates
station = station.drop_duplicates()

# Add missing columns (to fit with the ORM)
station = add_timestamped_table_fields(station)

# Add foreign keys
station["amenageur_id"] = static_with_ids.loc[station.index]["amenageur_id"]
station["operateur_id"] = static_with_ids.loc[station.index]["operateur_id"]
station["enseigne_id"] = static_with_ids.loc[station.index]["enseigne_id"]
station["localisation_id"] = static_with_ids.loc[station.index]["localisation_id"]

# Add operational units
station["operational_unit"] = station.apply(lambda x: x["id_station_itinerance"][:5], axis=1)
station = station.merge(operational_units[["id", "code"]], how="left", left_on="operational_unit", right_on="code")
station.drop(columns=["operational_unit", "code"], inplace=True)
station.rename(columns={"id_x": "id", "id_y": "operational_unit_id"}, inplace=True)

# Fix Enums
station = station.replace(to_replace=enum_value, value=enum_to_replace)
station
```

```python
dtype = {
    "implantation_station": sa_types.Enum,
    "condition_acces": sa_types.Enum,
    "condition_acces": sa_types.Enum,
    "raccordement": sa_types.Enum,
    "date_maj": sa_types.Date,
    "date_mise_en_service": sa_types.Date,
    "amenageur_id": sa_types.UUID,
    "operateur_id": sa_types.UUID,
    "enseigne_id": sa_types.UUID,
    "localisation_id": sa_types.UUID,
    "operational_unit_id": sa_types.UUID,
}
save(station, engine, "station", truncate=True, dtype=dtype)

saved = pd.read_sql("SELECT * FROM station", engine)
saved
```

```python
static_with_ids = add_ids(static_with_ids, station, "id_station_itinerance", "station_id")
static_with_ids
```

### Point of charge

```python
# Extract model fields
pdc_fields = [
    "id_pdc_itinerance",
    "id_pdc_local",
    "puissance_nominale",
    "prise_type_ef",
    "prise_type_2",
    "prise_type_combo_ccs",
    "prise_type_chademo",
    "prise_type_autre",
    "gratuit",
    "paiement_acte",
    "paiement_cb",
    "paiement_autre",
    "tarification",
    "reservation",
    "accessibilite_pmr",
    "restriction_gabarit",
    "observations",
    "cable_t2_attache",
]
pdc = static_with_ids[pdc_fields]

# Remove duplicates
pdc = pdc.drop_duplicates()

# Add missing columns (to fit with the ORM)
pdc = add_timestamped_table_fields(pdc)

# Add foreign keys
pdc["station_id"] = static_with_ids.loc[pdc.index]["station_id"]

# Fix Enums
pdc = pdc.replace(to_replace=enum_value, value=enum_to_replace)
pdc
```

```python
dtype = {
    "accessibilite_pmr": sa_types.Enum,
    "station_id": sa_types.UUID,
    "gratuit": sa_types.Boolean,
    "paiement_cb": sa_types.Boolean,
    "paiement_autre": sa_types.Boolean,
    "cable_t2_attache": sa_types.Boolean,
}
save(pdc, engine, "pointdecharge", truncate=True, dtype=dtype)

saved = pd.read_sql("SELECT * FROM PointDeCharge", engine)
saved
```

## Alternate version using raw SQLAlchemy

```python
amenageur_fields = ["nom_amenageur", "siren_amenageur", "contact_amenageur"]
amenageur = static[amenageur_fields]

# Remove duplicates
amenageur = amenageur.drop_duplicates()

# Add missing columns (to fit with the ORM)
amenageur = add_timestamped_table_fields(amenageur)
amenageur
```

```python
%%time
from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.schema import MetaData

def save_amenageur(df):
    metadata_obj = MetaData()
    t_amenageur = Table("amenageur", metadata_obj, autoload_with=engine)
    
    amenageur.drop("amenageur_id", axis=1, inplace=True, errors="ignore")
    
    stmt = insert(t_amenageur).values(amenageur.to_dict("records"))
    stmt = stmt.on_conflict_do_update(
        constraint="amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key",
        set_=dict(
            nom_amenageur=stmt.excluded.nom_amenageur, 
            siren_amenageur=stmt.excluded.siren_amenageur, 
            contact_amenageur=stmt.excluded.contact_amenageur,
            updated_at=stmt.excluded.updated_at
        )
    )
    stmt = stmt.returning(t_amenageur.c.id)
    
    with engine.connect() as conn:
        result = conn.execute(stmt)
    
    ids = pd.Series(data=(row.id for row in result.all()), index=amenageur.index)
    
    amenageur.insert(0, "amenageur_id", ids)
    return amenageur
    
amenageur = save_amenageur(amenageur)
amenageur
```

```python
%%time

def save_amenageur_by_chunks(df, n=10000):
    metadata_obj = MetaData()
    t_amenageur = Table("amenageur", metadata_obj, autoload_with=engine)
    
    df.drop("amenageur_id", axis=1, inplace=True, errors="ignore")

    chunks = [df[i:i+n] for i in range(0,len(df),n)]
    for chunk in chunks:
        stmt = insert(t_amenageur).values(chunk.to_dict("records"))
        stmt = stmt.on_conflict_do_update(
            constraint="amenageur_nom_amenageur_siren_amenageur_contact_amenageur_key",
            set_=dict(
                nom_amenageur=stmt.excluded.nom_amenageur, 
                siren_amenageur=stmt.excluded.siren_amenageur, 
                contact_amenageur=stmt.excluded.contact_amenageur,
                updated_at=stmt.excluded.updated_at
            )
        )
        stmt = stmt.returning(t_amenageur.c.id)
        
        with engine.connect() as conn:
            result = conn.execute(stmt)
        
        ids = pd.Series(data=(row.id for row in result.all()), index=chunk.index)
        
        chunk.insert(0, "amenageur_id", ids)
    return amenageur
    
amenageur = save_amenageur_by_chunks(amenageur, n=2000)
```
