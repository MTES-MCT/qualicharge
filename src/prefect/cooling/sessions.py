"""Prefect flows: cooling statuses."""

import os
from datetime import date
from string import Template

from dateutil.relativedelta import relativedelta
from prefect import flow
from prefect.states import Failed

from cooling import IfExistStrategy, extract_data_older_than
from indicators.types import Environment

SESSIONS_FOR_A_DAY_QUERY_TEMPLATE = Template("""
    SELECT
        PointDeCharge.id_pdc_itinerance,
        Session.*
    FROM
        Session
    INNER JOIN PointDeCharge ON Session.point_de_charge_id = PointDeCharge.id
    WHERE
        start::DATE = '$date'
    """)
SESSION_COUNT_FOR_A_DAY_QUERY_TEMPLATE = Template("""
    SELECT
        COUNT(*)
    FROM
        Session
    WHERE
        start::DATE = '$date'
    """)
SESSION_DAYS_TO_EXTRACT_QUERY_TEMPLATE = Template("""
    SELECT
      DISTINCT start::DATE AS event_date
    FROM
      Session
    WHERE
      start < '$older_than'
    GROUP BY
      event_date
    ORDER BY
      event_date
    """)


@flow(log_prints=True)
def extract_old_sessions(
    from_now: dict,
    environment: Environment,
    if_exists: IfExistStrategy = IfExistStrategy.FAIL,
    chunk_size: int = 5000,
):
    """Extract sessions older than now - from_now to daily archives."""
    s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", None)
    if s3_endpoint_url is None:
        return Failed(message="S3_ENDPOINT_URL environment variable not set.")
    bucket = "qualicharge-sessions"
    older_than = date.today() - relativedelta(**from_now)
    return extract_data_older_than(
        older_than,
        environment,
        bucket,
        s3_endpoint_url,
        SESSION_DAYS_TO_EXTRACT_QUERY_TEMPLATE,
        SESSIONS_FOR_A_DAY_QUERY_TEMPLATE,
        SESSION_COUNT_FOR_A_DAY_QUERY_TEMPLATE,
        if_exists=if_exists,
        chunk_size=chunk_size,
    )
