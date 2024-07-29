"""import admin geo fixtures

Revision ID: f5416bc7dd5f
Revises: 7b8c33d8399d
Create Date: 2024-07-29 09:03:55.369265

"""

import gzip
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Sequence, Union


import httpx
import geopandas as gp
import pandas as pd
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f5416bc7dd5f"
down_revision: Union[str, None] = "7b8c33d8399d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


@dataclass
class AdministrativeBoundary:
    """An administrative boundary level."""

    path: Path
    url: str
    table: str


def download_fixtures() -> Dict[str, AdministrativeBoundary]:
    """Download GeoJSON files from Etalab."""
    levels = ("communes", "epci", "departements", "regions")
    tables = ("city", "epci", "department", "region")
    etalab_root_url = (
        "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2024/geojson"
    )
    resolution = "100m"
    boundaries = {}

    tmp_dirname = tempfile.mkdtemp()
    for level, table in zip(levels, tables):
        boundaries[level] = AdministrativeBoundary(
            path=Path(f"{tmp_dirname}/{level}.geojson.gz"),
            url=f"{etalab_root_url}/{level}-{resolution}.geojson.gz",
            table=table,
        )

    # Download
    for level, ab in boundaries.items():
        print(f"Downloading {level} file to {ab.path}...")
        response = httpx.get(ab.url)
        with open(ab.path, "wb") as output_file:
            output_file.write(gzip.decompress(response.content))

    return boundaries


def load_level(input_file: Path) -> gp.GeoDataFrame:
    """Load administrative boundaries level."""
    boundaries = gp.read_file(f"GeoJSON:{input_file}")

    # Add missing columns (to fit with the ORM)
    boundaries["id"] = boundaries.apply(lambda x: uuid.uuid4(), axis=1)
    now = pd.Timestamp.now(tz="utc")
    boundaries["created_at"] = now
    boundaries["updated_at"] = now

    return boundaries


def import_fixtures():
    """Import administrative boundaries."""
    boundaries = download_fixtures()

    # -- Regions
    print("Importing regions...")
    regions = load_level(boundaries["regions"].path)
    regions.rename(columns={"nom": "name"}, inplace=True)
    regions.to_postgis(boundaries["regions"].table, op.get_bind(), if_exists="append")

    # -- Departments
    print("Importing departments...")
    departments = load_level(boundaries["departements"].path)
    departments.rename(columns={"nom": "name"}, inplace=True)
    # Handle foreign keys
    departments = departments.merge(
        regions[["id", "code"]],
        how="outer",
        left_on="region",
        right_on="code",
        suffixes=("_dept", "_reg"),
    )
    departments.rename(
        columns={"code_dept": "code", "id_dept": "id", "id_reg": "region_id"},
        inplace=True,
    )
    departments.drop(["code_reg", "region"], axis=1, inplace=True)
    departments.to_postgis(
        boundaries["departements"].table, op.get_bind(), if_exists="append"
    )

    # -- EPCI
    print("Importing epci...")
    epci = load_level(boundaries["epci"].path)
    epci.rename(columns={"nom": "name"}, inplace=True)
    epci.to_postgis(boundaries["epci"].table, op.get_bind(), if_exists="append")

    # -- Cities
    print("Importing cities...")
    cities = load_level(boundaries["communes"].path)
    cities.rename(columns={"nom": "name"}, inplace=True)
    # Handle foreign keys: department
    cities = cities.merge(
        departments[["id", "code"]],
        how="outer",
        left_on="departement",
        right_on="code",
        suffixes=("_city", "_dept"),
    )
    cities.rename(
        columns={"code_city": "code", "id_city": "id", "id_dept": "department_id"},
        inplace=True,
    )
    cities.drop(
        ["code_dept", "region", "commune", "departement", "plm"], axis=1, inplace=True
    )
    # Handle foreign keys: epci
    cities = cities.merge(
        epci[["id", "code"]],
        how="outer",
        left_on="epci",
        right_on="code",
        suffixes=("_city", "_epci"),
    )
    cities.rename(
        columns={"code_city": "code", "id_city": "id", "id_epci": "epci_id"},
        inplace=True,
    )
    cities.drop(["code_epci", "epci"], axis=1, inplace=True)
    cities.to_postgis(boundaries["communes"].table, op.get_bind(), if_exists="append")


def remove_fixtures():
    """Remove database administrative boundaries."""
    tables = ("region", "departement", "epci", "city")
    for table in tables:
        op.execute(f"TRUNCATE TABLE {table} CASCADE")


def upgrade() -> None:
    import_fixtures()


def downgrade() -> None:
    remove_fixtures()
