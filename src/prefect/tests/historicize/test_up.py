"""QualiCharge prefect indicators tests: function up."""

from datetime import date, datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from indicators.historicize import up
from indicators.infrastructure import i1
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level, PeriodDuration
from indicators.types import Environment

DATE_INIT = datetime.fromisoformat("2024-01-01T05:00:00Z")
SIZE = 8
DUREE = 3
TIMESPAN = IndicatorTimeSpan(start=DATE_INIT, period=IndicatorPeriod.MONTH)


def init_data(extras: bool = False) -> dict[str, Any]:
    """Initialize dataset."""
    data = {
        "value": list(range(SIZE)),
        "target": [str(i).rjust(2, "0") for i in range(SIZE)],
        "category": None,
        "code": ["ixx"] * SIZE,
        "level": ["01"] * SIZE,
        "timestamp": [DATE_INIT] * SIZE,
        "period": ["d"] * SIZE,
    }
    if extras:
        data["extras"] = [
            {
                "liste": [1, 2, 3],
                "sum_val": i,
                "max_val": float(i),
                "min_val": float(i),
                "last_val": float(i),
            }
            for i in range(SIZE)
        ]
    return data


def init_dataframe(extras: bool = False) -> pd.DataFrame:
    """Create DataFrame."""
    histo = pd.DataFrame(init_data(extras))
    data2 = init_data(extras)
    date_init2 = DATE_INIT
    for j in range(1, DUREE):
        date_init2 += PeriodDuration.DAY.value
        data2 |= {"timestamp": [date_init2] * SIZE, "value": list(range(j, SIZE + j))}
        if extras:
            data2 |= {
                "extras": [
                    {
                        "liste": [1 + j, 2 + j, 3 + j],
                        "sum_val": i + j,
                        "max_val": float(i + j),
                        "min_val": float(i + j),
                        "last_val": float(i + j),
                    }
                    for i in range(SIZE)
                ]
            }
        histo = pd.concat([histo, pd.DataFrame(data2)], ignore_index=True)
    return histo


def test_to_df_histo_up():
    """Test 'to_df_histo_up' function without extras."""
    histo = init_dataframe()
    mensuel = up.to_df_histo_up(histo, TIMESPAN)
    df = pd.concat([mensuel, pd.json_normalize(mensuel["extras"])], axis=1)
    del df["extras"]

    assert df["value"].equals(pd.Series(range(1, SIZE + 1), dtype="float"))
    assert df["mini"].equals(pd.Series(range(SIZE), dtype="float"))
    assert df["maxi"].equals(pd.Series(range(2, SIZE + 2), dtype="float"))
    assert df["last"].equals(df["maxi"])
    assert df["quantity"].equals(pd.Series([3] * SIZE))


def test_to_df_histo_up_extras():
    """Test 'to_df_histo_up' function with extras."""
    extras = True
    histo = init_dataframe(extras)
    mensuel = up.to_df_histo_up(histo, TIMESPAN)
    df = pd.concat([mensuel, pd.json_normalize(mensuel["extras"])], axis=1)
    del df["extras"]

    assert df["value"].equals(pd.Series(range(1, SIZE + 1), dtype="float"))
    assert df["mini"].equals(pd.Series(range(SIZE), dtype="float"))
    assert df["maxi"].equals(pd.Series(range(2, SIZE + 2), dtype="float"))
    assert df["last"].equals(df["maxi"])
    assert df["quantity"].equals(pd.Series([3] * SIZE))
    assert df["quantity"].equals(pd.Series([3] * SIZE))
    assert df["sum_val"].equals(pd.Series(range(3, (SIZE + 1) * DUREE, DUREE)))
    assert df["max_val"].equals(df["maxi"])
    assert df["min_val"].equals(df["mini"])
    assert df["last_val"].equals(df["last"])
    assert df["liste"].equals(pd.Series([[DUREE, 1 + DUREE, 2 + DUREE]] * SIZE))


def test_start_period():
    """Test the 'set_start_period' function."""
    tst = date(2024, 1, 10)
    assert up.set_start_period(tst, -1, IndicatorPeriod.MONTH) == datetime(2023, 12, 1)
    assert up.set_start_period(tst, -1, IndicatorPeriod.QUARTER) == datetime(
        2023, 10, 1
    )
    assert up.set_start_period(tst, -1, IndicatorPeriod.WEEK) == datetime(2024, 1, 3)
    assert up.set_start_period(tst, -2, IndicatorPeriod.WEEK) == datetime(2023, 12, 27)
    assert up.set_start_period(tst, 0, IndicatorPeriod.DAY) == datetime(2024, 1, 10)


def test_flow_up_calculate(db_connection):
    """Test the `calculate` flow."""
    indicators = i1.calculate(
        Environment.TEST,
        levels=[Level.NATIONAL, Level.REGION],
        start=TIMESPAN.start,
        period=IndicatorPeriod.DAY,
        create_artifact=True,
        persist=True,
    )
    histo_up = up.calculate(
        Environment.TEST,
        IndicatorPeriod.MONTH,
        start=TIMESPAN.start.date(),
        offset=0,
        period=IndicatorPeriod.DAY,
        persist=False,
    )
    assert len(histo_up) == len(indicators)
    assert histo_up["period"][0] == IndicatorPeriod.MONTH


def test_flow_calculate_persistence(indicators_db_engine):
    """Test the `calculate` flow."""
    indicators = i1.calculate(
        Environment.TEST,
        levels=[Level.NATIONAL, Level.REGION],
        start=TIMESPAN.start,
        period=IndicatorPeriod.DAY,
        create_artifact=True,
        persist=True,
    )
    up.calculate(
        Environment.TEST,
        IndicatorPeriod.MONTH,
        start=TIMESPAN.start.date(),
        offset=0,
        period=IndicatorPeriod.DAY,
        persist=True,
    )
    with indicators_db_engine.connect() as connection:
        query = """
        select count(*) from test
        where code = 'i1' and period = 'm'and timestamp::date = '2024-01-01'
        """
        result = connection.execute(text(query))
        assert result.one()[0] == len(indicators)
