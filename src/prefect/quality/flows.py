"""Prefect flow: run checkpoints."""

import os
import re
import unicodedata

import great_expectations as gx
from indicators import db
from prefect import flow, task
from prefect.artifacts import create_markdown_artifact
from prefect.cache_policies import NONE
from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import Session

from checkpoints.static import get_static_checkpoint
from expectations.static import set_expectation_suite as set_static_expectation_suite

api_data_source_name = "api-{environment}"


def slugify(value, allow_unicode=False):
    """Slugify a string.

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.

    Taken from Django code base:
    https://github.com/django/django/blob/main/django/utils/text.py
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


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
    assets = [a.name for a in data_source.assets]
    if name in assets:
        return None
    elif table:
        return data_source.add_table_asset(name=name, table_name=table)
    elif query:
        return data_source.add_query_asset(name=name, query=query)
    raise Exception


def get_api_db_checkpoint(
    environment="development",
    report_by_email: bool = False,
    update_data_docs: bool = False,
):
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
        context,
        batch,
        name=name,
        report_by_email=report_by_email,
        update_data_docs=update_data_docs,
    )
    return checkpoint


@task(cache_policy=NONE)
def run_api_db_checkpoint_for_amenageur(
    context,
    amenageur: str,
    environment: str = "development",
    report_by_email: bool = False,
    update_data_docs: bool = False,
):
    """Get API database instance checkpoint for an amenageur."""
    asset = f"static-{environment}-{slugify(amenageur)}"
    name = f"static-{environment}-{slugify(amenageur)}"

    query = f"SELECT * FROM STATIQUE where nom_amenageur = '{amenageur}'"
    static = get_data_asset(context, environment, asset, query=query)
    # Duplicate
    if not static:
        return
    batch = static.add_batch_definition_whole_table(name="FULL_TABLE")
    checkpoint = get_static_checkpoint(
        context,
        batch,
        name=name,
        report_by_email=report_by_email,
        update_data_docs=update_data_docs,
    )
    return checkpoint.run()


@flow(log_prints=True)
def run_api_db_validation(
    environment, report_by_email: bool = False, update_data_docs: bool = False
):
    """Run API DB checkpoint."""
    checkpoint = get_api_db_checkpoint(
        environment, report_by_email=report_by_email, update_data_docs=update_data_docs
    )
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
def run_api_db_validation_by_amenageur(
    environment: str, report_by_email: bool = False, update_data_docs: bool = False
):
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
            context,
            amenageur,
            environment,
            report_by_email=report_by_email,
            update_data_docs=update_data_docs,
        )
    #     md.append(f"| {amenageur} | " + ("✅" if result.success else "😡") + " |")
    #
    # create_markdown_artifact(
    #     "\n".join(md),
    #     description=f"GX validation by `Amenageur` for API DB instance: {environment}",
    #     key=f"api-db-static-amenageurs-{environment}",
    # )


# FIXME
# Used to ease development, should be removed
if __name__ == "__main__":
    run_api_db_validation("development")
    # run_api_db_validation_by_amenageur("development")
