"""Prefect flows: cooling statuses."""

from datetime import date
from string import Template
from typing import List

from prefect import flow
from prefect.client.schemas.objects import State

from cooling import (
    IfExistStrategy,
    extract_data_for_day,
    extract_data_for_period,
    get_daily_cooling_day,
    get_s3_endpoint_url,
)
from indicators.types import Environment

STATUSES_FOR_A_DAY_QUERY_TEMPLATE = Template("""
    SELECT
        PointDeCharge.id_pdc_itinerance,
        Status.*
    FROM
        Status
    INNER JOIN PointDeCharge ON Status.point_de_charge_id = PointDeCharge.id
    WHERE
        horodatage::DATE = '$date'
    """)
STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE = Template("""
    SELECT
        COUNT(*)
    FROM
        Status
    WHERE
        horodatage::DATE = '$date'
    """)
BUCKET_NAME = "qualicharge-statuses"
COOL_AFTER_DAYS: int = 8


@flow(
    flow_run_name="extract-statuses-{environment}-from-{from_date:%x}-to-{to_date:%x}"
)
def cool_statuses_for_period(
    from_date: date,
    to_date: date,
    environment: Environment,
    if_exists: IfExistStrategy = IfExistStrategy.FAIL,
    chunk_size: int = 5000,
) -> List[State]:
    """Extract statuses to daily archives for a period.

    Note that dates from the period interval are both included.
    """
    return extract_data_for_period(
        from_date,
        to_date,
        environment,
        BUCKET_NAME,
        get_s3_endpoint_url(),
        STATUSES_FOR_A_DAY_QUERY_TEMPLATE,
        STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE,
        if_exists=if_exists,
        chunk_size=chunk_size,
    )


@flow
def daily_cool_statuses(
    environment: Environment = Environment.PRODUCTION,
    if_exists: IfExistStrategy = IfExistStrategy.FAIL,
    days: int = COOL_AFTER_DAYS,
    chunk_size: int = 5000,
) -> State:
    """Cool statuses for (today - `days`) day."""
    return extract_data_for_day(
        get_daily_cooling_day(days),
        environment,
        BUCKET_NAME,
        get_s3_endpoint_url(),
        STATUSES_FOR_A_DAY_QUERY_TEMPLATE,
        STATUS_COUNT_FOR_A_DAY_QUERY_TEMPLATE,
        if_exists=if_exists,
        chunk_size=chunk_size,
    )
