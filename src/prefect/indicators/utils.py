"""QualiCharge prefect indicators: utils.

Common indicators functions and constants.
"""

from string import Template

import pandas as pd  # type: ignore
from prefect import task
from prefect.artifacts import create_markdown_artifact
from sqlalchemy.orm import Session

from .db import get_api_db_engine, save_indicators
from .models import IndicatorTimeSpan, Level, PeriodDuration
from .types import Environment

POWER_RANGE_CTE = {
    "power_range": """
    puissance(category, p_cat) AS (
        VALUES
            (numrange(0.0, 7.4), 1),
            (numrange(7.4, 22.0), 2),
            (numrange(22.0, 50.0), 3),
            (numrange(50, 150.0), 4),
            (numrange(150, 350.0), 5),
            (numrange(350, NULL), 6)
    )"""
}


def get_timespan_filter_query_params(timespan: IndicatorTimeSpan, session: bool = True):
    """Get timespan query parameters."""
    date_end = timespan.start + PeriodDuration[timespan.period.name].value
    sql_start = f"'{timespan.start.isoformat(sep=" ")}'"
    sql_end = f"'{date_end.isoformat(sep=" ")}'"
    interval_session = "start >= timestamp $start AND start < timestamp $end"
    interval_status = "horodatage >= timestamp $start AND horodatage < timestamp $end"
    interval = interval_session if session else interval_status
    return {
        "timespan": Template(interval).substitute({"start": sql_start, "end": sql_end})
    }


def get_num_for_level_query_params(level: Level):
    """Get level_id and join_extras query parameters."""
    match level:
        case Level.CITY:
            return {"level_id": "City.id", "join_extras": ""}
        case Level.EPCI:
            return {
                "level_id": "EPCI.id",
                "join_extras": "INNER JOIN EPCI ON City.epci_id = EPCI.id",
            }
        case Level.DEPARTMENT:
            return {
                "level_id": "Department.id",
                "join_extras": """
                    INNER JOIN Department ON City.department_id = Department.id
                    """,
            }
        case Level.REGION:
            return {
                "level_id": "Region.id",
                "join_extras": """
                    INNER JOIN Department ON City.department_id = Department.id
                    INNER JOIN Region ON Department.region_id = Region.id
                    """,
            }
        case _:
            raise NotImplementedError("Unsupported level %d", level)


@task(task_run_name="targets-for-level-{level:02d}")
def get_targets_for_level(level: Level, environment: Environment) -> pd.DataFrame:
    """Get registered targets for level from QualiCharge database."""
    if level == Level.NATIONAL:
        raise NotImplementedError("Unsupported level %d", level)
    with Session(get_api_db_engine(environment)) as session:
        return pd.read_sql_table(level.name.lower(), con=session.connection())


def export_indicators(  # noqa: PLR0913
    indicators: pd.DataFrame,
    environment: Environment,
    flow_name: str,
    description: str,
    create_artifact: bool,
    persist: bool,
):
    """Export indicators."""
    if persist and environment:
        save_indicators(environment, indicators)

    if create_artifact:
        create_markdown_artifact(
            key=flow_name, markdown=indicators.to_markdown(), description=description
        )
