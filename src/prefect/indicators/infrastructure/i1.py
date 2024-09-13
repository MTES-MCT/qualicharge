"""QualiCharge prefect indicators: infrastructure.

I1: the number of publicly open points of charge.
"""

from datetime import datetime
from string import Template
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd
from prefect import flow, runtime, task
from prefect.artifacts import create_markdown_artifact
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from ..conf import settings
from ..models import Indicator, IndicatorPeriod, Level


@task
def get_database_engine() -> Engine:
    """Get QualiCharge API database engine."""
    return create_engine(str(settings.DATABASE_URL))


@task(task_run_name="targets-for-level-{level:02d}")
def get_targets_for_level(connection: Connection, level: Level) -> pd.DataFrame:
    """Get registered targets for level from QualiCharge database."""
    match level:
        case Level.CITY:
            table = "city"
        case Level.EPCI:
            table = "epci"
        case Level.DEPARTMENT:
            table = "department"
        case Level.REGION:
            table = "region"
        case _:
            raise NotImplementedError("Unsupported level %d", level)
    return pd.read_sql_table(table, con=connection)


@task(task_run_name="pocs-for-target-{level:02d}")
def get_points_of_charge_for_targets(
    connection: Connection, level: Level, indexes: List[UUID]
) -> pd.DataFrame:
    """Fetch points of charge given input level and target index."""
    query_template = Template(
        """
        SELECT
            COUNT(DISTINCT PointDeCharge.id_pdc_itinerance) AS num_poc,
            $level_id AS level_id
        FROM PointDeCharge
        INNER JOIN Station ON PointDeCharge.station_id = Station.id
        INNER JOIN Localisation ON Station.localisation_id = Localisation.id
        INNER JOIN City ON Localisation.code_insee_commune = City.code
        $inner
        WHERE $level_id IN ($indexes)
        GROUP BY $level_id
    """
    )
    query_params: dict = {"indexes": ",".join(f"'{i}'" for i in map(str, indexes))}

    match level:
        case Level.CITY:
            query_params.update(
                {
                    "level_id": "City.id",
                    "inner": "",
                }
            )
        case Level.EPCI:
            query_params.update(
                {
                    "level_id": "EPCI.id",
                    "inner": "INNER JOIN EPCI ON City.epci_id = EPCI.id",
                }
            )
        case Level.DEPARTMENT:
            query_params.update(
                {
                    "level_id": "Department.id",
                    "inner": """
                    INNER JOIN Department ON City.department_id = Department.id
                    """,
                }
            )
        case Level.REGION:
            query_params.update(
                {
                    "level_id": "Region.id",
                    "inner": """
                    INNER JOIN Department ON City.department_id = Department.id
                    INNER JOIN Region ON Department.region_id = Region.id
                    """,
                }
            )
        case _:
            raise NotImplementedError("Unsupported level %d", level)
    return pd.read_sql_query(query_template.substitute(query_params), con=connection)


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i1-{period.value}-{level:02d}-{at:%y-%m-%d}",
)
def i1_for_level(
    level: Level,
    period: IndicatorPeriod,
    at: datetime,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
) -> pd.DataFrame:
    """Calculate i1 for a level."""
    engine = get_database_engine()
    with engine.connect() as connection:
        targets = get_targets_for_level(connection, level)
        ids = targets["id"].apply(UUID)  # type: ignore[arg-type]
        chunks = (
            np.array_split(ids, int(len(ids) / chunk_size))
            if len(ids) > chunk_size
            else [ids.to_numpy()]
        )
        futures = [
            get_points_of_charge_for_targets.submit(connection, level, chunk)  # type: ignore[call-overload]
            for chunk in chunks
        ]
        wait(futures)

    # Concatenate results
    results = pd.concat([future.result() for future in futures], ignore_index=True)

    # Serialize indicators
    merged = targets.merge(results, how="left", left_on="id", right_on="level_id")
    merged["num_poc"] = merged["num_poc"].fillna(0)

    # Build result DataFrame
    indicators = pd.DataFrame()
    indicators["target"] = merged["code"]
    indicators["value"] = merged["num_poc"]
    indicators["code"] = "i1"
    indicators["level"] = level
    indicators["period"] = period
    indicators["timestamp"] = at
    indicators[["category", "extras"]] = None

    return indicators


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="i1-{period.value}-00-{at:%y-%m-%d}",
)
def i1_national(period: IndicatorPeriod, at: datetime) -> pd.DataFrame:
    """Calculate i1 at the national level."""
    engine = get_database_engine()
    with engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM PointDeCharge"))
        count = result.one()[0]

    return pd.DataFrame.from_records(
        [
            Indicator(
                code="i1",
                level=Level.NATIONAL,
                period=period,
                value=count,
                timestamp=at,
            ).model_dump(),
        ]
    )


@flow(
    task_runner=ThreadPoolTaskRunner(max_workers=settings.THREAD_POOL_MAX_WORKERS),
    flow_run_name="meta-i1-{period.value}",
)
def calculate(
    period: IndicatorPeriod, create_artifact: bool = False, chunk_size: int = 1000
) -> List[Indicator]:
    """Run all i1 subflows."""
    now = pd.Timestamp.now()
    national = i1_national(period, now)
    regions = i1_for_level(Level.REGION, period, now, chunk_size=chunk_size)
    departments = i1_for_level(Level.DEPARTMENT, period, now, chunk_size=chunk_size)
    epcis = i1_for_level(Level.EPCI, period, now, chunk_size=chunk_size)
    cities = i1_for_level(Level.CITY, period, now, chunk_size=chunk_size)

    indicators = pd.concat(
        [national, regions, departments, epcis, cities], ignore_index=True
    )
    if create_artifact:
        create_markdown_artifact(
            key=runtime.flow_run.name,
            markdown=indicators.to_markdown(),
            description=f"i1 report at {now} (period: {period.value})",
        )

    return [Indicator(**record) for record in indicators.to_dict(orient="records")]  # type: ignore[misc]
