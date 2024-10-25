"""QualiCharge prefect indicators: utils.

Common indicators functions and constants.
"""

import pandas as pd  # type: ignore
from prefect import task
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine

from .conf import settings
from .models import Level

POWER_RANGE_CTE = """
    puissance(category, p_cat) AS (
        VALUES
            (numrange(0, 15.0), 1),
            (numrange(15.0, 26.0), 2),
            (numrange(26, 65.0), 3),
            (numrange(65, 175.0), 4),
            (numrange(175, 360.0), 5),
            (numrange(360, NULL), 6)
    )"""


def get_num_for_level_query_params(level):
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


@task
def get_database_engine() -> Engine:
    """Get QualiCharge API database engine."""
    return create_engine(str(settings.DATABASE_URL))


@task(task_run_name="targets-for-level-{level:02d}")
def get_targets_for_level(connection: Connection, level: Level) -> pd.DataFrame:
    """Get registered targets for level from QualiCharge database."""
    if level == Level.NATIONAL:
        raise NotImplementedError("Unsupported level %d", level)
    return pd.read_sql_table(level.name.lower(), con=connection)
