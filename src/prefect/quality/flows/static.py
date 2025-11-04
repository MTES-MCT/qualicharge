"""Prefect flows: static."""

from datetime import date

import great_expectations as gx
from prefect import flow

from indicators.models import IndicatorPeriod
from quality.expectations import static
from quality.flows.quality_run import (
    API_DATA_SOURCE_NAME,
    QCReport,
    run_api_db_checkpoint,
    run_api_db_checkpoint_by_amenageur,
)


@flow(log_prints=True)
def run_api_db_validation(
    environment: str,
    report_by_email: bool = False,
) -> gx.checkpoint.CheckpointResult:
    """Run API DB checkpoint."""
    # Context
    context = gx.get_context(mode="ephemeral")

    # Data source
    data_source = context.data_sources.add_postgres(
        name=API_DATA_SOURCE_NAME.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )
    # Expectation suite
    suite = static.get_suite()
    context.suites.add(suite)

    # Checkpoints
    result = run_api_db_checkpoint(
        context, data_source, suite, environment, report_by_email, "static"
    )
    return result


@flow(log_prints=True)
def run_api_db_validation_by_amenageur(
    environment: str,
    period: IndicatorPeriod = IndicatorPeriod.DAY,
    report_by_email: bool = False,
    create_artifact: bool = False,
    persist: bool = False,
) -> QCReport:
    """Run API DB checkpoint by amenageur."""
    # Context
    context = gx.get_context(mode="ephemeral")

    # Data source
    data_source = context.data_sources.add_postgres(
        name=API_DATA_SOURCE_NAME.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )

    # Expectation suite
    suite = static.get_suite()
    context.suites.add(suite)

    # Checkpoints
    report = run_api_db_checkpoint_by_amenageur(
        context,
        data_source,
        suite,
        environment,
        period,
        date.today(),
        report_by_email,
        "static",
        create_artifact=create_artifact,
        persist=persist,
    )
    return report
