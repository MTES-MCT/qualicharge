"""QualiCharge prefect indicators tests: function up."""

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from indicators.extract import e4
from indicators.historicize import up
from indicators.infrastructure import i1, t1
from indicators.models import IndicatorPeriod, IndicatorTimeSpan, Level, PeriodDuration
from indicators.types import Environment

DATE_INIT = datetime.fromisoformat("2024-01-01T05:00:00Z")
SIZE = 8
DUREE = 3
TIMESPAN = IndicatorTimeSpan(start=DATE_INIT, period=IndicatorPeriod.MONTH)


def init_data(size: int, extras: bool = False) -> dict[str, Any]:
    """Initialize dataset."""
    data = {
        "value": list(range(size)),
        "target": [str(i).rjust(2, "0") for i in range(size)],
        "category": None,
        "code": ["i1"] * size,
        "level": ["01"] * size,
        "timestamp": [DATE_INIT] * size,
        "period": ["d"] * size,
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
            for i in range(size)
        ]
    return data


def init_dataframe(size: int, duree: int, extras: bool = False) -> pd.DataFrame:
    """Create DataFrame."""
    histo = pd.DataFrame(init_data(size, extras))
    data2 = init_data(size, extras)
    date_init2 = DATE_INIT
    for j in range(1, duree):
        date_init2 += PeriodDuration.DAY.value
        data2 |= {"timestamp": [date_init2] * size, "value": list(range(j, size + j))}
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
                    for i in range(size)
                ]
            }
        histo = pd.concat([histo, pd.DataFrame(data2)], ignore_index=True)
    return histo


def test_calculate():
    """Test 'calculate_historicization_up' function."""
    one_four = pd.Series([1, 2, 3, 4])
    five_eight = pd.Series([5, 6, 7, 8])
    nine_ten = pd.Series([9, 10])
    expected = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    df_expected = pd.DataFrame(
        {
            "size": [len(expected)],
            "min": [expected.min()],
            "mean": [float(expected.mean())],
            "sum": [float(expected.sum())],
            "max": [expected.max()],
            "std": [expected.std(ddof=0)],
            "var": [expected.var(ddof=0)],
            "last": [list(expected)[-1]],
            "from": ["d"],
            "code": ["code"],
            "level": ["level"],
            "target": ["target"],
            "category": ["category"],
        }
    )
    data = [one_four, five_eight, nine_ten]
    df_in = pd.DataFrame(
        {
            "size": [len(df) for df in data],
            "min": [df.min() for df in data],
            "mean": [float(df.mean()) for df in data],
            "sum": [float(df.sum()) for df in data],
            "max": [df.max() for df in data],
            "std": [df.std(ddof=0) for df in data],
            "var": [df.var(ddof=0) for df in data],
            "last": [list(df)[-1] for df in data],
            "from": ["d" for df in data],
            "code": ["code" for df in data],
            "level": ["level" for df in data],
            "target": ["target" for df in data],
            "category": ["category" for df in data],
        }
    )
    df_up = up.calculate_historicization_up(df_in, IndicatorPeriod.DAY)
    fields = ["last", "min", "max", "size", "mean", "sum", "from"]
    assert df_up.reset_index()[fields].equals(df_expected[fields])
    assert int(list(df_up.reset_index()["var"])[0] * 1000) == int(
        list(df_expected["var"])[0] * 1000
    )
    assert int(list(df_up.reset_index()["std"])[0] * 1000) == int(
        list(df_expected["std"])[0] * 1000
    )


def test_to_historicization_up():
    """Test 'to_historicization_up' function without extras."""
    histo = init_dataframe(SIZE, DUREE)
    mensuel = up.to_historicization_up(histo, IndicatorPeriod.DAY, TIMESPAN)
    df = pd.concat([mensuel, pd.json_normalize(mensuel["extras"], max_level=0)], axis=1)
    del df["extras"]
    df = pd.concat([df, pd.json_normalize(df["history"], max_level=0)], axis=1)
    del df["history"]

    assert df["mean"].equals(pd.Series(range(1, SIZE + 1), dtype="float"))
    assert df["min"].equals(pd.Series(range(SIZE), dtype="float"))
    assert df["max"].equals(pd.Series(range(2, SIZE + 2), dtype="float"))
    assert df["last"].equals(df["max"])
    assert df["size"].equals(pd.Series([3] * SIZE))
    assert (
        (df["var"] * 1000)
        .astype("int")
        .equals(pd.Series([2 / 3 * 1000] * SIZE).astype("int"))
    )
    assert (
        (df["std"] * 1000)
        .astype("int")
        .equals((df["var"].pow(0.5) * 1000).astype("int"))
    )
    assert df["value"].equals(df["mean"])


def test_to_historicization_up_extras():
    """Test 'to_historicization_up' function with extras."""
    extras = True
    histo = init_dataframe(SIZE, DUREE, extras)
    mensuel = up.to_historicization_up(histo, IndicatorPeriod.DAY, TIMESPAN)
    df = pd.concat([mensuel, pd.json_normalize(mensuel["extras"], max_level=0)], axis=1)
    del df["extras"]
    df = pd.concat([df, pd.json_normalize(df["history"], max_level=0)], axis=1)
    del df["history"]

    assert df["mean"].equals(pd.Series(range(1, SIZE + 1), dtype="float"))
    assert df["min"].equals(pd.Series(range(SIZE), dtype="float"))
    assert df["max"].equals(pd.Series(range(2, SIZE + 2), dtype="float"))
    assert df["last"].equals(df["max"])
    assert df["size"].equals(pd.Series([3] * SIZE))
    assert (
        (df["var"] * 1000)
        .astype("int")
        .equals(pd.Series([2 / 3 * 1000] * SIZE).astype("int"))
    )
    assert (
        (df["std"] * 1000)
        .astype("int")
        .equals((df["var"].pow(0.5) * 1000).astype("int"))
    )
    assert df["sum_val"].equals(pd.Series(range(3, (SIZE + 1) * DUREE, DUREE)))
    assert df["max_val"].equals(df["max"])
    assert df["min_val"].equals(df["min"])
    assert df["last_val"].equals(df["last"])
    assert df["liste"].equals(pd.Series([[DUREE, 1 + DUREE, 2 + DUREE]] * SIZE))

    assert df["value"].equals(df["mean"])


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
        start=TIMESPAN.start,
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
    e4.calculate(
        Environment.TEST,
        levels=[Level.NATIONAL, Level.REGION],
        start=TIMESPAN.start,
        period=IndicatorPeriod.DAY,
        create_artifact=False,
    )
    t1.calculate(
        Environment.TEST,
        levels=[Level.NATIONAL],
        start=TIMESPAN.start,
        period=IndicatorPeriod.DAY,
        persist=True,
    )
    up.calculate(
        Environment.TEST,
        IndicatorPeriod.MONTH,
        start=TIMESPAN.start,
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
