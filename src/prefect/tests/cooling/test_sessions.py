"""QualiCharge prefect cooling tests: sessions."""

import os
from datetime import date

import pandas as pd
import pytest
from freezegun import freeze_time
from prefect.client.schemas.objects import StateType

import cooling
from cooling import IfExistStrategy
from cooling.sessions import cool_sessions_for_period, daily_cool_sessions
from indicators.types import Environment


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_cool_sessions_for_period_flow(clean_s3fs):
    """Test the `cool_sessions_for_period` flow."""
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 29),
        to_date=date(2024, 12, 1),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )

    # We expect an archive to have been generated for each period day
    expected_states = 3
    assert len(results) == expected_states
    assert all((r.type == StateType.COMPLETED for r in results))
    expected_paths = (
        "qualicharge-sessions/2024/11/29/test.parquet",
        "qualicharge-sessions/2024/11/30/test.parquet",
        "qualicharge-sessions/2024/12/1/test.parquet",
    )
    for result, expected_path in zip(results, expected_paths, strict=True):
        assert (
            result.message == f"qualicharge-sessions archive '{expected_path}' created"
        )

    for expected_path, n_sessions in zip(expected_paths, (0, 19, 1777), strict=True):
        # Assert parquet file exists and can be opened
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
        assert len(df) == n_sessions


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_cool_sessions_for_period_flow_for_a_single_day(clean_s3fs):
    """Test the `cool_sessions_for_period` flow."""
    results = cool_sessions_for_period(
        from_date=date(2024, 12, 2),
        to_date=date(2024, 12, 2),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )

    # We expect a single archive to have been generated
    expected_states = 1
    assert len(results) == expected_states
    result = results[0]
    assert result.type == StateType.COMPLETED
    expected_path = "qualicharge-sessions/2024/12/2/test.parquet"
    assert result.message == f"qualicharge-sessions archive '{expected_path}' created"

    # Assert parquet file exists and can be opened
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    n_sessions = 1321
    df = pd.read_parquet(
        f"s3://{expected_path}",
        engine="pyarrow",
        dtype_backend="pyarrow",
        storage_options={
            "endpoint_url": s3_endpoint_url,
        },
    )
    # Check parquet file content
    assert len(df) == n_sessions


def test_cool_sessions_for_period_flow_fails_without_s3_env_set(monkeypatch):
    """Test `cool_sessions_for_period` flow fails when S3_ENDPOINT_URL is not set."""
    monkeypatch.delenv("S3_ENDPOINT_URL", raising=False)
    with pytest.raises(
        ValueError, match="S3_ENDPOINT_URL environment variable not set."
    ):
        cool_sessions_for_period(
            from_date=date(2024, 12, 2),
            to_date=date(2024, 12, 2),
            environment=Environment.TEST,
            if_exists=IfExistStrategy.IGNORE,
        )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_cool_sessions_for_period_flow_check_fails(clean_s3fs, monkeypatch):
    """Test the `cool_sessions_for_period` flow when archive check fails."""

    # What if check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )

    result = results[0]
    expected_path = "qualicharge-sessions/2024/11/30/test.parquet"
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-sessions archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_extract_old_sessions_flow_archive_exists(clean_s3fs):
    """Test the `extract_old_sessions` flow when target archive exists."""
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    result = results[0]
    expected_path = "qualicharge-sessions/2024/11/30/test.parquet"

    # We expect a single session older than 6 months
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == f"qualicharge-sessions archive '{expected_path}' created"

    # Test ignore strategy
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == (
        f"qualicharge-sessions archive '{expected_path}' already exists. "
        "Task will be considered as completed."
    )

    # Test fail strategy
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.FAIL,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-sessions archive '{expected_path}' already exists!"
    )

    # Test overwrite strategy
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.OVERWRITE,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == f"qualicharge-sessions archive '{expected_path}' created"

    # Test append strategy
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.APPEND,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-sessions archive '{expected_path}' already exists and "
        "concatenation for S3 has not been implemented yet."
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_cool_sessions_for_period_flow_archive_exists_check(clean_s3fs, monkeypatch):
    """Test the `cool_sessions_for_period` flow when target archive exists.

    Test the IfExistStrategy.CHECK scenario.
    """
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    result = results[0]
    expected_path = "qualicharge-sessions/2024/11/30/test.parquet"

    # We expect a single session older than 6 months
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == f"qualicharge-sessions archive '{expected_path}' created"

    # Test the CHECK strategy
    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.CHECK,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == (
        f"qualicharge-sessions archive '{expected_path}' already exists "
        "and has been checked. It contains 19 rows."
    )

    # What happens when check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    results = cool_sessions_for_period(
        from_date=date(2024, 11, 30),
        to_date=date(2024, 11, 30),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.CHECK,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-sessions archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-sessions"], indirect=["clean_s3fs"]
)
def test_daily_cool_sessions_flow_archive_exists_check(clean_s3fs):
    """Test the `daily_cool_sessions` flow."""
    with freeze_time("2025-01-22"):
        result = daily_cool_sessions(
            environment=Environment.TEST,
        )

    # We expect an archive to have been generated for 2025-01-01
    assert result.type == StateType.COMPLETED
    expected_path = "qualicharge-sessions/2025/1/1/test.parquet"
    assert result.message == f"qualicharge-sessions archive '{expected_path}' created"

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
    n_sessions = 2624
    assert len(df) == n_sessions
