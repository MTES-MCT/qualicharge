"""QualiCharge prefect indicators tests: function up."""

from datetime import datetime
from typing import Any

import pandas as pd

from indicators.models import IndicatorPeriod, IndicatorTimeSpan, PeriodDuration
from indicators.up import to_df_histo_up

DATE_INIT = datetime.fromisoformat("2024-01-01")
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
                "liste": ["a", "b", "c"],
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
    mensuel = to_df_histo_up(histo, TIMESPAN)
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
    mensuel = to_df_histo_up(histo, TIMESPAN)
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
