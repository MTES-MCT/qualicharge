"""QualiCharge prefect tiruert tests: run."""

import datetime
import os

import pandas as pd
import pytest
from prefect.exceptions import ParameterTypeError
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import text

import tiruert.run
from indicators.types import Environment
from tiruert.run import (
    AMENAGEUR_WITH_SESSIONS_TEMPLATE,
    Siren,
    daily_tiruert,
    enea,
    eneu,
    enex,
    filter_sessions,
    flag_duplicates,
    get_amenageurs_for_period,
    get_sessions,
    negs,
    odus,
    tiruert_for_day,
    tiruert_for_day_and_amenageur,
    tiruert_for_day_and_amenageur_over_period,
    tiruert_for_day_over_period,
)


@pytest.mark.parametrize(
    "value",
    [
        "",  # too short
        "1",
        "1234567890",  # too long
    ],
)
def test_siren_ckeck_invalid_length(value):
    """Test the `Siren` type validation."""
    siren = TypeAdapter(Siren)
    with pytest.raises(ValidationError, match="1 validation error"):
        siren.validate_python(value)


@pytest.mark.parametrize(
    "value",
    [
        "abcdefghi",  # not a number
        "1234e6789",
        "000000000",  # blacklist
        "123456789",  # invalid
    ],
)
def test_siren_ckeck_invalid(value):
    """Test the `Siren` type validation."""
    siren = TypeAdapter(Siren)
    with pytest.raises(ValidationError, match=f"{value} is not a valid SIREN number"):
        siren.validate_python(value)


@pytest.mark.parametrize(
    "value",
    [
        "732829320",
        "842718512",
        "844192443",
    ],
)
def test_siren_ckeck_valid(value):
    """Test the `Siren` custom type."""
    siren = TypeAdapter(Siren)
    assert siren.validate_python(value) == value


def test_task_get_amenageurs_for_period():
    """Test the `get_amenageurs_for_period` task."""
    amenageurs = get_amenageurs_for_period(
        Environment.TEST, datetime.date(2024, 12, 27), datetime.date(2024, 12, 28)
    )
    expected = 24
    assert len(amenageurs) == expected


def test_task_get_sessions():
    """Test the `get_sessions` task."""
    sessions = get_sessions(
        Environment.TEST,
        datetime.date(2024, 12, 27),
        datetime.date(2024, 12, 28),
        "891118473",
    )
    expected = 851
    assert len(sessions) == expected


def test_negs():
    """Test the `negs` rows filter."""
    # To < From
    df = pd.DataFrame(
        data={
            "from": [datetime.datetime(2024, 12, 25, 20, 12, 34)],
            "to": [datetime.datetime(2024, 12, 25, 20, 48, 38)],
        }
    )
    assert not negs(df.loc[0])

    # From > To
    df = pd.DataFrame(
        data={
            "from": [datetime.datetime(2024, 12, 25, 20, 12, 42)],
            "to": [datetime.datetime(2024, 12, 25, 20, 12, 34)],
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
                datetime.datetime(2024, 12, 25, 20, 12, 42),
                datetime.datetime(2024, 12, 25, 20, 12, 42),
            ],
            "to": [
                datetime.datetime(2024, 12, 25, 21, 18, 23),
                datetime.datetime(2024, 12, 25, 21, 18, 23),
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
            "from": [datetime.datetime(2024, 12, 25, 20, 12, 34)],
            "to": [datetime.datetime(2024, 12, 25, 20, 48, 38)],
            "energy": [20.0],
        }
    )
    assert not odus(df.loc[0])

    # From > To
    df = pd.DataFrame(
        data={
            "from": [datetime.datetime(2024, 12, 25, 20, 12, 42)],
            "to": [datetime.datetime(2024, 12, 25, 20, 12, 34)],
            "energy": [20.0],
        }
    )
    assert odus(df.loc[0])

    # From > To and energy < 1
    df = pd.DataFrame(
        data={
            "from": [datetime.datetime(2024, 12, 25, 20, 12, 42)],
            "to": [datetime.datetime(2024, 12, 25, 20, 12, 34)],
            "energy": [0.2],
        }
    )
    assert not odus(df.loc[0])


def test_enex():
    """Test the `enex` rows filter."""
    df = pd.DataFrame(
        data={
            "from": [
                datetime.datetime(2024, 12, 25, 20, 12, 42),
                datetime.datetime(2024, 12, 25, 20, 12, 42),
            ],
            "to": [
                datetime.datetime(2024, 12, 25, 21, 18, 23),
                datetime.datetime(2024, 12, 25, 21, 18, 23),
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
                datetime.datetime(2024, 12, 25, 20, 12, 42),
                datetime.datetime(2024, 12, 25, 20, 12, 42),
                datetime.datetime(2024, 12, 26, 20, 12, 42),
                datetime.datetime(2024, 12, 25, 20, 34, 42),
            ],
            "to": [
                datetime.datetime(2024, 12, 25, 21, 18, 23),
                datetime.datetime(2024, 12, 25, 21, 18, 23),
                datetime.datetime(2024, 12, 26, 21, 18, 23),
                datetime.datetime(2024, 12, 25, 21, 25, 23),
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
        Environment.TEST,
        datetime.date(2024, 12, 27),
        datetime.date(2024, 12, 28),
        "891118473",
    )
    filtered, to_ignore = filter_sessions(sessions)
    expected = 500
    assert len(filtered) == expected
    expected = 351
    assert len(to_ignore) == expected
    assert all(to_ignore["enea"])


def test_flow_tiruert_for_day_and_amenageur_with_invalid_siren():
    """Test the `tiruert_for_day_and_amenageur` flow with an invalid siren."""
    with pytest.raises(ParameterTypeError, match="Flow run received invalid parameter"):
        tiruert_for_day_and_amenageur(
            Environment.TEST, datetime.date(2024, 12, 27), "123456789"
        )


def test_flow_tiruert_for_day_and_amenageur(indicators_db_engine):
    """Test the `tiruert_for_day_and_amenageur` flow."""
    tiruert_for_day_and_amenageur(
        Environment.TEST, datetime.date(2024, 12, 27), "891118473"
    )

    # Assert saved tiruert is as expected
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT COUNT(*) FROM test WHERE code = 'tirue' "
                "AND target = '891118473'"
            )
        )
        # We should have saved only a single for for 891118473 over this period
        assert result.one()[0] == 1

        result = connection.execute(
            text("SELECT * FROM test WHERE code = 'tirue' AND target = '891118473'")
        )
        indicator = result.one()
        assert indicator.target == "891118473"
        # expected total for a day
        expected = 15.850909
        assert indicator.value == pytest.approx(expected)
        assert indicator.code == "tirue"
        expected = 6
        assert indicator.level == expected
        assert indicator.period == "d"
        assert indicator.category is None
        # expected stations
        expected = 268
        assert len(indicator.extras) == expected

    # Check we saved ignored sessions
    expected_path = "qualicharge-sessions/2024/12/27/ignored-891118473.parquet"
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    df = pd.read_parquet(
        f"s3://{expected_path}",
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={
            "endpoint_url": s3_endpoint_url,
        },
    )
    # Check parquet file content
    n_sessions = 351
    assert len(df) == n_sessions


def test_flow_tiruert_for_day(db_connection, indicators_db_engine):
    """Test the `tiruert_for_day_and_amenageur` flow."""
    day = datetime.date(2024, 12, 27)
    tiruert_for_day(Environment.TEST, day)

    # Get the number of operational units with sessions on that day
    result = db_connection.execute(
        text(
            AMENAGEUR_WITH_SESSIONS_TEMPLATE.substitute(
                {"from_date": day, "to_date": day + datetime.timedelta(days=1)}
            )
        )
    )
    n_amenageurs = len(result.all())

    # Assert saved tiruert is as expected
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM test WHERE code = 'tirue'")
        )
    # We should have saved as many indicators as distinct operational units
    # where sessions occured on that day
    assert result.one()[0] == n_amenageurs


def test_flow_tiruert_for_day_with_invalid_siren(
    db_connection, indicators_db_engine, monkeypatch
):
    """Test the `tiruert_for_day_and_amenageur` flow with invalid SIREN."""
    monkeypatch.setattr(
        tiruert.run,
        "get_amenageurs_for_period",
        lambda *_: {"siren": ["123456789", "891118473"]},
    )
    day = datetime.date(2024, 12, 27)
    tiruert_for_day(Environment.TEST, day)

    # Assert saved tiruert is as expected
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM test WHERE code = 'tirue'")
        )
    # We should have saved a single indicator as invalid SIREN should have been ignored
    n_amenageurs = 1
    assert result.one()[0] == n_amenageurs


def test__get_daily_tiruert_day():
    """Test the `_get_daily_tiruert_day` utility."""
    assert (
        tiruert.run._get_daily_tiruert_day()
        == (datetime.datetime.today() - datetime.timedelta(days=21)).date()
    )


def test_flow_daily_tiruert(db_connection, indicators_db_engine, monkeypatch):
    """Test the `daily_tiruert` flow."""
    target = datetime.datetime(2024, 12, 27) - datetime.timedelta(days=21)

    monkeypatch.setattr(tiruert.run, "_get_daily_tiruert_day", lambda: target.date())

    daily_tiruert(Environment.TEST)

    # Get the number of operational units with sessions on that day
    result = db_connection.execute(
        text(
            AMENAGEUR_WITH_SESSIONS_TEMPLATE.substitute(
                {
                    "from_date": target.date(),
                    "to_date": (target + datetime.timedelta(days=1)).date(),
                }
            )
        )
    )
    n_amenageurs = len(result.all())

    # Assert saved tiruert is as expected
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM test WHERE code = 'tirue'")
        )
    # We should have saved as many indicators as distinct operational units
    # where sessions occured on that day
    assert result.one()[0] == n_amenageurs

    # Assert we've calculated the TIRUERT for target - 21 days
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT COUNT(*) FROM test "
                "WHERE "
                "code = 'tirue' AND "
                "timestamp::date = '2024-12-6'"
            )
        )
    assert result.one()[0] == n_amenageurs


def test_flow_tiruert_for_day_over_period(indicators_db_engine):
    """Test the `tiruert_for_day_over_period` flow."""
    from_date = datetime.date(2024, 12, 1)
    to_date = datetime.date(2024, 12, 10)
    tiruert_for_day_over_period(Environment.TEST, from_date, to_date)

    # Assert saved tiruert is as expected
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT COUNT(*), timestamp::date as day FROM test "
                "WHERE code = 'tirue' "
                "GROUP BY day"
            )
        )
    # We should have saved as many indicators as days
    expected = 10
    assert len(result.all()) == expected


def test_flow_tiruert_for_day_and_amenageur_over_period(indicators_db_engine):
    """Test the `tiruert_for_day_and_amenageur_over_period` flow."""
    from_date = datetime.date(2024, 12, 1)
    to_date = datetime.date(2024, 12, 31)
    siren = "891118473"
    tiruert_for_day_and_amenageur_over_period(
        Environment.TEST, from_date, to_date, siren
    )

    # Assert saved tiruert is as expected
    with indicators_db_engine.connect() as connection:
        result = connection.execute(
            text("SELECT COUNT(*) FROM test WHERE code = 'tirue'")
        )
    # We should have saved as many indicators as days
    expected = 31
    assert result.one()[0] == expected


def test_flow_tiruert_for_day_and_amenageur_over_period_with_invalid_siren():
    """Test the `tiruert_for_day_and_amenageur_over_period` flow w/ an invalid SIREN."""
    with pytest.raises(ParameterTypeError, match="Flow run received invalid parameter"):
        tiruert_for_day_and_amenageur_over_period(
            Environment.TEST,
            datetime.date(2024, 12, 1),
            datetime.date(2024, 12, 31),
            "123456789",
        )
