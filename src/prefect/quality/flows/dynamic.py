"""Prefect flows: dynamic."""

from datetime import date, timedelta

import great_expectations as gx
from prefect import flow

from quality.expectations import dynamic
from quality.flows.quality_run import (
    API_DATA_SOURCE_NAME,
    QCReport,
    run_api_db_checkpoint,
    run_api_db_checkpoint_by_amenageur,
)


@flow(log_prints=True)
def run_api_db_validation(
    environment: str,
    from_now: dict,
    report_by_email: bool = False,
    new_now: date | None = None,
) -> gx.checkpoint.CheckpointResult:
    """Run API DB checkpoint."""
    date_end = date.today() if not new_now else new_now
    date_start = date_end - timedelta(**from_now)

    # Context
    context = gx.get_context(mode="ephemeral")

    # Data source
    data_source = context.data_sources.add_postgres(
        name=API_DATA_SOURCE_NAME.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )
    # Expectation suite
    suite = dynamic.get_suite(date_start, date_end)
    context.suites.add(suite)

    # Checkpoints
    result = run_api_db_checkpoint(
        context, data_source, suite, environment, report_by_email, "dynamic"
    )
    return result


@flow(log_prints=True)
def run_api_db_validation_by_amenageur(
    environment: str,
    from_now: dict,
    report_by_email: bool = False,
    new_now: date | None = None,
) -> QCReport:
    """Run API DB checkpoint by amenageur."""
    date_end = date.today() if not new_now else new_now
    date_start = date_end - timedelta(**from_now)

    # Context
    context = gx.get_context(mode="ephemeral")

    # Data source
    data_source = context.data_sources.add_postgres(
        name=API_DATA_SOURCE_NAME.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )

    # Expectation suite
    suite = dynamic.get_suite(date_start, date_end)
    context.suites.add(suite)

    # Checkpoints
    report = run_api_db_checkpoint_by_amenageur(
        context, data_source, suite, environment, report_by_email, "dynamic"
    )
    return report
