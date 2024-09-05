"""admin_level_population_area_data_migration

Revision ID: 161e8a262e0a
Revises: b10e85cde5d0
Create Date: 2024-09-12 14:18:23.490571

"""

from alembic import op
import geopandas as gp
import numpy as np
import pandas as pd
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "161e8a262e0a"
down_revision: Union[str, None] = "b10e85cde5d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    data_upgrades()


def downgrade() -> None:
    data_downgrades()


def data_upgrades() -> None:
    # Datasets
    root_url = "https://unpkg.com/@etalab/decoupage-administratif/data"
    ds_communes = pd.read_json(f"{root_url}/communes.json", dtype_backend="pyarrow")
    ds_epci = pd.read_json(f"{root_url}/epci.json", dtype_backend="pyarrow")

    # Load tables
    cities = gp.read_postgis("city", op.get_bind(), geom_col="geometry", crs=4326)
    departments = gp.read_postgis(
        "department", op.get_bind(), geom_col="geometry", crs=4326
    )
    epcis = gp.read_postgis("epci", op.get_bind(), geom_col="geometry", crs=4326)
    regions = gp.read_postgis("region", op.get_bind(), geom_col="geometry", crs=4326)

    # Add population
    cities["population"] = cities.merge(
        ds_communes.loc[~ds_communes["population"].isna(), ["code", "population"]],
        how="left",
        on="code",
    )["population_y"]
    departments["population"] = departments.merge(
        ds_communes.loc[
            ds_communes["type"] == "commune-actuelle", ["departement", "population"]
        ]
        .groupby("departement", as_index=False)
        .agg("sum"),
        how="left",
        left_on="code",
        right_on="departement",
    )["population_y"]
    epcis["population"] = epcis.merge(
        ds_epci[["code", "populationMunicipale"]].rename(
            columns={"populationMunicipale": "population"}
        ),
        how="left",
        on="code",
    )["population_y"]
    regions["population"] = regions.merge(
        ds_communes.loc[
            ds_communes["type"] == "commune-actuelle", ["region", "population"]
        ]
        .groupby("region", as_index=False)
        .agg("sum"),
        how="left",
        left_on="code",
        right_on="region",
    )["population_y"]

    # Calculate areas
    department_crs = pd.DataFrame.from_records(
        [(f"{d:02d}", 9794) for d in range(1, 96) if d != 20]
        + [("2A", 9794), ("2B", 9794)]
        + [
            ("971", 5490),
            ("972", 5490),
            ("973", 2972),
            ("974", 2975),
            ("975", 4467),
            ("976", 4471),
            ("977", 5490),
            ("978", 5490),
            ("984", 7080),
            ("986", 8903),
            ("987", 3296),
            ("988", 3163),
            ("989", pd.NA),
        ],
        columns=["departement", "crs"],
    )
    crss = pd.unique(
        department_crs.loc[~pd.isnull(department_crs["crs"]), ["crs"]]["crs"]
    ).tolist()
    ds_crs = ds_communes.loc[
        ds_communes["type"] == "commune-actuelle", ["code", "departement", "region"]
    ].merge(department_crs, how="left", on="departement")

    for df, right_on in (
        (cities, "code"),
        (departments, "departement"),
        (regions, "region"),
    ):
        with_crs = df.merge(
            ds_crs[[right_on, "crs"]].drop_duplicates(),
            how="left",
            left_on="code",
            right_on=right_on,
        )
        area = pd.Series()
        for crs in crss:
            area = pd.concat(
                [
                    area,
                    with_crs.loc[with_crs["crs"] == crs]["geometry"].to_crs(crs).area,
                ]
            )
        df["area"] = area
        df.replace(np.nan, pd.NA, inplace=True)

    # EPCIs
    # Add EPCI first member commune code
    ds_epci["commune"] = ds_epci["membres"].apply(lambda x: x[0]["code"])
    ds_epci["crs"] = ds_epci.merge(
        ds_crs[["code", "crs"]], how="left", left_on="commune", right_on="code"
    )["crs"]
    with_crs = epcis.merge(ds_epci[["code", "crs"]], how="left", on="code")
    area = pd.Series()
    for crs in crss:
        area = pd.concat(
            [area, with_crs.loc[with_crs["crs"] == crs]["geometry"].to_crs(crs).area]
        )
    epcis["area"] = area
    epcis.replace(np.nan, pd.NA, inplace=True)

    # Write tables
    cities.to_postgis("city", op.get_bind(), if_exists="replace")
    departments.to_postgis("department", op.get_bind(), if_exists="replace")
    epcis.to_postgis("epci", op.get_bind(), if_exists="replace")
    regions.to_postgis("region", op.get_bind(), if_exists="replace")


def data_downgrades() -> None:
    """Reset area and population fields to 0."""
    for table in ("city", "epci", "department", "region"):
        level = gp.read_postgis(table, op.get_bind(), geom_col="geometry", crs=4326)
        level["area"] = 0.0
        level["population"] = 0
        level.to_postgis(table, op.get_bind(), if_exists="replace")
