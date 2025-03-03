"""Prefect flow: run checkpoints."""

import os

import great_expectations as gx
from prefect import flow, task
from prefect.artifacts import create_markdown_artifact
from prefect.cache_policies import NONE
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from checkpoints.static import get_static_checkpoint
from expectations.static import set_expectation_suite as set_static_expectation_suite

api_data_source_name = "api-{environment}"


def set_data_source(context, environment: str):
    """Add API data instance as a data source."""
    context.data_sources.add_postgres(
        name=api_data_source_name.format(environment=environment),
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )


def get_data_asset(
    context,
    environment: str,
    name: str,
    table: str | None = None,
    query: str | None = None,
):
    """Get data asset for an environment."""
    data_source = context.data_sources.get(
        api_data_source_name.format(environment=environment)
    )
    if table:
        return data_source.add_table_asset(name=name, table_name=table)
    elif query:
        return data_source.add_query_asset(name=name, query=query)
    raise Exception


def get_api_db_checkpoint(environment="development", report_by_email: bool = False):
    """Check API database instance quality."""
    context = gx.get_context(mode="ephemeral")

    table = "statique"
    asset = f"static-{environment}"
    name = f"static-{environment}"
    set_data_source(context, environment)
    set_static_expectation_suite(context)
    static = get_data_asset(context, environment, asset, table=table)
    batch = static.add_batch_definition_whole_table(name="FULL_TABLE")
    checkpoint = get_static_checkpoint(
        context, batch, name=name, report_by_email=report_by_email
    )
    return checkpoint


@task(cache_policy=NONE)
def run_api_db_checkpoint_for_amenageur(
    context,
    amenageur: str,
    environment: str = "development",
    report_by_email: bool = False,
):
    """Get API database instance checkpoint for an amenageur."""
    asset = f"static-{environment}-{amenageur}"
    name = f"static-{environment}-{amenageur}"

    query = f"SELECT * FROM STATIQUE where nom_amenageur = '{amenageur}'"
    static = get_data_asset(context, environment, asset, query=query)
    batch = static.add_batch_definition_whole_table(name="FULL_TABLE")
    checkpoint = get_static_checkpoint(
        context, batch, name=name, report_by_email=report_by_email
    )
    return checkpoint.run()


@flow(log_prints=True)
def run_api_db_validation(environment, report_by_email: bool = False):
    """Run API DB checkpoint."""
    checkpoint = get_api_db_checkpoint(environment, report_by_email=report_by_email)
    result = checkpoint.run()
    create_markdown_artifact(
        "\n".join(
            (
                f"# Checkpoint validation: {checkpoint.name}",
                "```json",
                f"{result.describe()}",
                "```",
            )
        ),
        description=f"GX validation for API DB instance: {environment}",
        key=f"api-db-static-{environment}",
    )


@flow(log_prints=True)
def run_api_db_validation_by_amenageur(environment: str, report_by_email: bool = False):
    """Run API DB checkpoint by amenageur."""
    context = gx.get_context(mode="ephemeral")
    set_data_source(context, environment)
    set_static_expectation_suite(context)
    md = [
        "# Checkpoint validation by amenageur",
        "| Amenageur | Statique |",
        "| -- | -- |",
    ]

    db_connection_url = os.getenv(f"QUALICHARGE_API_DATABASE_URLS__{environment}")
    db_engine = create_engine(db_connection_url)
    with Session(db_engine) as session:
        amenageurs = [
            res[0]
            for res in session.execute(
                text(
                    "SELECT nom_amenageur "
                    "FROM Statique "
                    "WHERE nom_amenageur <> ''"
                    "GROUP BY nom_amenageur "
                    "ORDER BY nom_amenageur"
                )
            ).all()
        ]
    for amenageur in amenageurs:
        result = run_api_db_checkpoint_for_amenageur(
            context, amenageur, environment, report_by_email=report_by_email
        )
        md.append(f"| {amenageur} | " + ("✅" if result.success else "😡") + " |")

    create_markdown_artifact(
        "\n".join(md),
        description=f"GX validation by `Amenageur` for API DB instance: {environment}",
        key=f"api-db-static-amenageurs-{environment}",
    )


# FIXME
# Used to ease development, should be removed
if __name__ == "__main__":
    # run_api_db_validation("development")
    run_api_db_validation_by_amenageur("development")
