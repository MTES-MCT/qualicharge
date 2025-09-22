"""QualiCharge prefect tiruert tests: run."""

from datetime import date, datetime

import pandas as pd

from indicators.types import Environment
from tiruert.run import (
    enea,
    eneu,
    enex,
    filter_sessions,
    flag_duplicates,
    get_operational_units_for_period,
    get_sessions,
    negs,
    odus,
    tiruert_for_period,
    tiruert_for_period_and_operational_unit,
)


def test_task_get_operational_units_for_period():
    """Test the `get_operational_units_for_period` task."""
    ou = get_operational_units_for_period(
        Environment.TEST, date(2024, 12, 27), date(2024, 12, 28)
    )
    expected = 20
    assert len(ou) == expected


def test_task_get_sessions():
    """Test the `get_sessions` task."""
    sessions = get_sessions(
        Environment.TEST, date(2024, 12, 27), date(2024, 12, 28), "FRPD1"
    )
    expected = 851
    assert len(sessions) == expected


def test_negs():
    """Test the `negs` rows filter."""
    # To < From
    df = pd.DataFrame(
        data={
            "from": [datetime(2024, 12, 25, 20, 12, 34)],
            "to": [datetime(2024, 12, 25, 20, 48, 38)],
        }
    )
    assert not negs(df.loc[0])

    # From > To
    df = pd.DataFrame(
        data={
            "from": [datetime(2024, 12, 25, 20, 12, 42)],
            "to": [datetime(2024, 12, 25, 20, 12, 34)],
        }
    )
    assert negs(df.loc[0])


def test_eneu():
    """Test the `eneu` rows filter."""
    df = pd.DataFrame(data={"energy": [802.0, 300.0, 1001.0, 400.0, 1200.0]})
    expected = 2
    assert len(df[df.apply(eneu, axis=1)]) == expected


def test_enea():
    """Test the `enea` rows filter."""
    df = pd.DataFrame(
        data={
            "from": [
                datetime(2024, 12, 25, 20, 12, 42),
                datetime(2024, 12, 25, 20, 12, 42),
            ],
            "to": [
                datetime(2024, 12, 25, 21, 18, 23),
                datetime(2024, 12, 25, 21, 18, 23),
            ],
            "max_power": [250.0, 11.0],
            "energy": [28.9, 30.0],
        }
    )
    assert len(df[df.apply(enea, axis=1)]) == 1


def test_odus():
    """Test the `odus` rows filter."""
    # To < From
    df = pd.DataFrame(
        data={
            "from": [datetime(2024, 12, 25, 20, 12, 34)],
            "to": [datetime(2024, 12, 25, 20, 48, 38)],
            "energy": [20.0],
        }
    )
    assert not odus(df.loc[0])

    # From > To
    df = pd.DataFrame(
        data={
            "from": [datetime(2024, 12, 25, 20, 12, 42)],
            "to": [datetime(2024, 12, 25, 20, 12, 34)],
            "energy": [20.0],
        }
    )
    assert odus(df.loc[0])

    # From > To and energy < 1
    df = pd.DataFrame(
        data={
            "from": [datetime(2024, 12, 25, 20, 12, 42)],
            "to": [datetime(2024, 12, 25, 20, 12, 34)],
            "energy": [0.2],
        }
    )
    assert not odus(df.loc[0])


def test_enex():
    """Test the `enex` rows filter."""
    df = pd.DataFrame(
        data={
            "from": [
                datetime(2024, 12, 25, 20, 12, 42),
                datetime(2024, 12, 25, 20, 12, 42),
            ],
            "to": [
                datetime(2024, 12, 25, 21, 18, 23),
                datetime(2024, 12, 25, 21, 18, 23),
            ],
            "max_power": [250.0, 11.0],
            "energy": [28.9, 1200.0],
        }
    )
    assert len(df[df.apply(enex, axis=1)]) == 1


def test_flag_duplicates():
    """Test the `flag_duplicates` rows filter."""
    df = pd.DataFrame(
        data={
            "from": [
                datetime(2024, 12, 25, 20, 12, 42),
                datetime(2024, 12, 25, 20, 12, 42),
                datetime(2024, 12, 26, 20, 12, 42),
                datetime(2024, 12, 25, 20, 34, 42),
            ],
            "to": [
                datetime(2024, 12, 25, 21, 18, 23),
                datetime(2024, 12, 25, 21, 18, 23),
                datetime(2024, 12, 26, 21, 18, 23),
                datetime(2024, 12, 25, 21, 25, 23),
            ],
            "id_pdc_itinerance": [
                "FRXXXEYYY1",
                "FRXXXEYYY1",
                "FRXXXEYYY2",
                "FRXXXEYYY1",
            ],
        }
    )
    flagged = flag_duplicates(df)
    assert len(df[flagged["duplicate"]]) == 1
    assert len(df[flagged["overlap"]]) == 1


def test_task_filter_sessions():
    """Test the `get_sessions` task."""
    sessions = get_sessions(
        Environment.TEST, date(2024, 12, 27), date(2024, 12, 28), "FRPD1"
    )
    filtered, to_ignore = filter_sessions(sessions)
    expected = 500
    assert len(filtered) == expected
    expected = 351
    assert len(to_ignore) == expected
    assert all(to_ignore["enea"])


def test_flow_tiruert_for_period_and_operational_unit():
    """Test the `tiruert_for_period_and_operational_unit` flow."""
    tiruert_for_period_and_operational_unit(
        Environment.TEST, date(2024, 12, 27), date(2024, 12, 28), "FRPD1"
    )
    # TODO
    # Assert saved tiruert is as expected


def test_flow_tiruert_for_period():
    """Test the `tiruert_for_period_and_operational_unit` flow."""
    tiruert_for_period(Environment.TEST, date(2024, 12, 27), date(2024, 12, 28))
    # TODO
    # Assert saved tiruert is as expected
