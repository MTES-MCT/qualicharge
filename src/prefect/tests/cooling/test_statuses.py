"""QualiCharge prefect cooling tests: statuses."""

import os
from datetime import date

import pandas as pd
import pytest
from freezegun import freeze_time
from prefect.client.schemas.objects import StateType

import cooling
from cooling import IfExistStrategy
from cooling.statuses import cool_statuses_for_period, daily_cool_statuses
from indicators.types import Environment


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_cool_statuses_for_period_flow(clean_s3fs):
    """Test the `cool_statuses_for_period` flow."""
    results = cool_statuses_for_period(
        from_date=date(2024, 7, 13),
        to_date=date(2024, 7, 15),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )

    # We expect an archive to have been generated for each period day
    expected_states = 3
    assert len(results) == expected_states
    assert all((r.type == StateType.COMPLETED for r in results))
    expected_paths = (
        "qualicharge-statuses/2024/7/13/test.parquet",
        "qualicharge-statuses/2024/7/14/test.parquet",
        "qualicharge-statuses/2024/7/15/test.parquet",
    )
    for result, expected_path in zip(results, expected_paths, strict=True):
        assert (
            result.message == f"qualicharge-statuses archive '{expected_path}' created"
        )

    for expected_path, n_statuses in zip(expected_paths, (3, 1, 13), strict=True):
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
        assert len(df) == n_statuses


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_cool_statuses_for_period_flow_check_fails(clean_s3fs, monkeypatch):
    """Test the `cool_statuses_for_period` flow when archive check fails."""

    # What if check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )

    result = results[0]
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-statuses archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_cool_statuses_for_period_flow_archive_exists(clean_s3fs):
    """Test the `cool_statuses_for_period` flow when target archive exists."""
    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"
    result = results[0]

    # We expect a single status older than a year
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == f"qualicharge-statuses archive '{expected_path}' created"

    # Test ignore strategy
    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == (
        f"qualicharge-statuses archive '{expected_path}' already exists. "
        "Task will be considered as completed."
    )

    # Test fail strategy
    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.FAIL,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-statuses archive '{expected_path}' already exists!"
    )

    # Test overwrite strategy
    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.OVERWRITE,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == f"qualicharge-statuses archive '{expected_path}' created"

    # Test append strategy
    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.APPEND,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-statuses archive '{expected_path}' already exists and "
        "concatenation for S3 has not been implemented yet."
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_cool_statuses_for_period_flow_archive_exists_check(clean_s3fs, monkeypatch):
    """Test the `cool_statuses_for_period` flow when target archive exists."""
    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.IGNORE,
    )
    result = results[0]
    expected_path = "qualicharge-statuses/2024/6/6/test.parquet"

    # We expect a single status older than a year
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == f"qualicharge-statuses archive '{expected_path}' created"

    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.CHECK,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.COMPLETED
    assert result.message == (
        f"qualicharge-statuses archive '{expected_path}' already exists "
        "and has been checked. It contains 2 rows."
    )

    # What happens when check fails?
    def fake_check(*args):
        return False, 1, 2

    monkeypatch.setattr(cooling, "_check_archive", fake_check)

    results = cool_statuses_for_period(
        from_date=date(2024, 6, 6),
        to_date=date(2024, 6, 6),
        environment=Environment.TEST,
        if_exists=IfExistStrategy.CHECK,
    )
    result = results[0]
    assert len(results) == 1
    assert result.type == StateType.FAILED
    assert result.message == (
        f"qualicharge-statuses archive '{expected_path}' and database content"
        f" have diverged (1 vs 2 expected rows)"
    )


@pytest.mark.parametrize(
    "clean_s3fs", ["qualicharge-statuses"], indirect=["clean_s3fs"]
)
def test_daily_cool_statuses_flow_archive_exists_check(clean_s3fs):
    """Test the `daily_cool_statuses` flow."""
    with freeze_time("2024-11-27"):
        result = daily_cool_statuses(
            environment=Environment.TEST,
        )

    # We expect an archive to have been generated for 2024-11-19
    assert result.type == StateType.COMPLETED
    expected_path = "qualicharge-statuses/2024/11/19/test.parquet"
    assert result.message == f"qualicharge-statuses archive '{expected_path}' created"

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
    n_sessions = 105
    assert len(df) == n_sessions
