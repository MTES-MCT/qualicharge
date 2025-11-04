"""Prefect flows: dynamic."""

from datetime import date, timedelta

import great_expectations as gx
from prefect import flow

from indicators.models import IndicatorPeriod
from quality.expectations import dynamic
from quality.expectations.parameters import SESSION_PARAMS, STATUS_PARAMS
from quality.flows.quality_run import (
    API_DATA_SOURCE_NAME,
    QCReport,
    run_api_db_checkpoint,
    run_api_db_checkpoint_by_amenageur,
)


@flow(log_prints=True)
def run_api_db_validation(  # noqa: PLR0913
    environment: str,
    report_by_email: bool = False,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    from_now: dict | None = None,
    new_now: date | None = None,
    check_session: bool = True,
    check_status: bool = True,
) -> gx.checkpoint.CheckpointResult:
    """Run API DB checkpoint."""
    # datation
    delta_from_now = timedelta() if not from_now else timedelta(**from_now)
    date_now = date.today() if not new_now else new_now

    date_end = date_now - delta_from_now
    date_start = date_end - period.duration
    interval = f"Interval: {date_start} to {date_end}"

    # perimeter
    session_p = SESSION_PARAMS if check_session else []
    status_p = STATUS_PARAMS if check_status else []
    parameters = session_p + status_p

    # Context
    context = gx.get_context(mode="ephemeral")

    # Data source
    data_source = context.data_sources.add_postgres(
        name=API_DATA_SOURCE_NAME.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )
    # Expectation suite
    suite = dynamic.get_suite(date_start, date_end, parameters)
    context.suites.add(suite)

    # Checkpoints
    result = run_api_db_checkpoint(
        context, data_source, suite, environment, report_by_email, "dynamic", interval
    )
    return result


@flow(log_prints=True)
def run_api_db_validation_by_amenageur(  # noqa: PLR0913
    environment: str,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    from_now: dict | None = None,
    report_by_email: bool = False,
    new_now: date | None = None,
    create_artifact: bool = False,
    persist: bool = False,
    check_session: bool = True,
    check_status: bool = True,
) -> QCReport:
    """Run API DB checkpoint by amenageur."""
    # datation
    delta_from_now = timedelta() if not from_now else timedelta(**from_now)
    date_now = date.today() if not new_now else new_now

    date_end = date_now - delta_from_now
    date_start = date_end - period.duration
    interval = f"Interval: {date_start} to {date_end}"

    # perimeter
    session_p = SESSION_PARAMS if check_session else []
    status_p = STATUS_PARAMS if check_status else []
    parameters = session_p + status_p

    # Context
    context = gx.get_context(mode="ephemeral")

    # Data source
    data_source = context.data_sources.add_postgres(
        name=API_DATA_SOURCE_NAME.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )

    # Expectation suite
    suite = dynamic.get_suite(date_start, date_end, parameters)
    context.suites.add(suite)

    # Checkpoints
    report = run_api_db_checkpoint_by_amenageur(
        context,
        data_source,
        suite,
        environment,
        period,
        date_start,
        report_by_email,
        "dynamic",
        interval,
        create_artifact=create_artifact,
        persist=persist,
    )
    return report
