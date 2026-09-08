"""QualiCharge prefect indicators tests: function state."""

from datetime import date

from sqlalchemy import text

from cooling import IfExistStrategy
from cooling.sessions import cool_sessions_for_period
from cooling.statuses import cool_statuses_for_period
from indicators.extract import e1, e2_e3_e6, e5, utils
from indicators.models import IndicatorPeriod, Level
from indicators.types import Environment

MIN_POWER = 50
SAMPLES = 288  # 5 min
DATE = date(2024, 12, 28)
ID_POC = "id_pdc_itinerance"
LEN_SESSIONS = 4835
LEN_STATUSES = 14386
LEN_SAMPLED_STATE_POC = 506304
LEN_STATE_POC = 1731
LEN_STATE_STATION = 1275
LEN_STATE_POOL = 219


def test_read_s3_data() -> None:
    """Test read_s3_data function."""
    cool_sessions_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    sessions = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-sessions",
    )
    assert not sessions.empty


def test_filter_statuses_sessions() -> None:
    """Test filter_statuses_sessions function."""
    e5_df = e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=DATE + IndicatorPeriod.DAY.duration,
        period=IndicatorPeriod.DAY,
        persist=True,
    )
    cool_sessions_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    sessions = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-sessions",
    )
    cool_statuses_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    statuses = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-statuses",
    )
    # statics = e2_e3_e6.read_statics(DATE, Environment.TEST, MIN_POWER)
    statics = utils.get_poc_station_for_day(DATE, Environment.TEST)
    statics = statics[statics["puissance_nominale"] >= MIN_POWER]

    statuses, sessions = e2_e3_e6.filter_statuses_sessions(sessions, statuses, statics)
    assert not e5_df.empty
    assert not statics.empty
    assert not statuses.empty
    assert not sessions.empty
    assert set(sessions[ID_POC].unique()).issubset(set(statics[ID_POC].unique()))
    assert set(statuses[ID_POC].unique()).issubset(set(sessions[ID_POC].unique()))


def test_get_sampled_state_poc() -> None:
    """Test get_sampled_state_poc function."""
    cool_sessions_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    sessions = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-sessions",
    )
    assert len(sessions) == LEN_SESSIONS
    cool_statuses_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    statuses = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-statuses",
    )
    assert len(statuses) == LEN_STATUSES
    statics = utils.get_poc_station_for_day(DATE, Environment.TEST)
    statics = statics[statics["puissance_nominale"] >= MIN_POWER]
    statuses, sessions = e2_e3_e6.filter_statuses_sessions(sessions, statuses, statics)
    e2_e3_e6_sampled_state_poc = e2_e3_e6.get_sampled_state_poc(
        DATE,
        SAMPLES,
        sessions,
        statuses,
    )
    assert not e2_e3_e6_sampled_state_poc.empty
    assert len(e2_e3_e6_sampled_state_poc) == LEN_SAMPLED_STATE_POC


def test_flow_e2_e3_e6(indicators_db_engine):
    """Test the `e2_e3_e6` flow."""
    cool_sessions_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    sessions = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-sessions",
    )
    cool_statuses_for_period(
        DATE,
        DATE,
        Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    statuses = e2_e3_e6.read_s3_data(
        DATE,
        Environment.TEST,
        "qualicharge-statuses",
    )
    e5.e5(
        Environment.TEST,
        [Level.NATIONAL],
        start=DATE + IndicatorPeriod.DAY.duration,
        period=IndicatorPeriod.DAY,
        persist=True,
    )
    e1.e1(
        Environment.TEST,
        start=DATE,
        persist=True,
        offset=0,
    )
    statics = utils.get_poc_station_for_day(DATE, Environment.TEST)
    statics = statics[statics["puissance_nominale"] >= MIN_POWER]
    statuses, sessions = e2_e3_e6.filter_statuses_sessions(sessions, statuses, statics)

    indicators_e2, indicators_e3, indicators_e6 = e2_e3_e6.e2_e3_e6(
        Environment.TEST,
        MIN_POWER,
        start=DATE,
        offset=0,
        create_artifact=False,
    )
    assert list(indicators_e2["value"])[0] == LEN_STATE_POC
    assert list(indicators_e3["value"])[0] == LEN_STATE_STATION
    assert list(indicators_e6["value"])[0] == LEN_STATE_POOL

    indicators_chunk_light_e2, indicators_chunk_light_e3, indicators_chunk_light_e6 = (
        e2_e3_e6.e2_e3_e6(
            Environment.TEST,
            MIN_POWER,
            start=DATE,
            offset=0,
            chunk_size=200,
            create_artifact=False,
        )
    )
    assert list(indicators_chunk_light_e2["value"])[0] == LEN_STATE_POC
    assert list(indicators_chunk_light_e3["value"])[0] == LEN_STATE_STATION
    assert list(indicators_chunk_light_e6["value"])[0] == LEN_STATE_POOL

    indicators_persistent_e2, indicators_persistent_e3, indicators_persistent_e6 = (
        e2_e3_e6.e2_e3_e6(
            Environment.TEST,
            MIN_POWER,
            start=DATE,
            offset=0,
            create_artifact=False,
            persist=True,
        )
    )
    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'e2'"))
        assert result.one()[0] == len(indicators_persistent_e2)
    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'e3'"))
        assert result.one()[0] == len(indicators_persistent_e3)
    with indicators_db_engine.connect() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM test WHERE code = 'e6'"))
        assert result.one()[0] == len(indicators_persistent_e6)
