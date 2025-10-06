"""Prefect flows: quality static and dynamic."""

import os
import re
import unicodedata
from datetime import date, timedelta
from typing import Generator, List, Type

import great_expectations as gx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from prefect import flow
from prefect.artifacts import create_markdown_artifact
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

API_DATA_SOURCE_NAME: str = "api-{environment}"


class QCExpectationResult(BaseModel):
    """QualiCharge simplified expectation result."""

    code: str
    success: bool


class QCExpectationsSuiteResult(BaseModel):
    """QualiCharge simplified expectation suite result."""

    amenageur: str
    success: bool
    suite: List[QCExpectationResult] = []


class QCReport(BaseModel):
    """QualiCharge expectations report."""

    name: str
    results: List[QCExpectationsSuiteResult] = []


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


def get_db_amenageurs(environment: str) -> Generator[str, None, None]:
    """Get amenageurs from database."""
    connection_url = os.getenv(f"QUALICHARGE_API_DATABASE_URLS__{environment}")
    if not connection_url:
        raise LookupError("Undefined API database environment variable")
    db_engine = create_engine(connection_url)
    with Session(db_engine) as session:
        for res in session.execute(
            text(
                "SELECT nom_amenageur "
                "FROM Statique "
                "WHERE nom_amenageur <> ''"
                "GROUP BY nom_amenageur "
                "ORDER BY nom_amenageur"
            )
        ).all():
            yield res[0]


def run_api_db_checkpoint(  # noqa: PLR0913
    context: gx.data_context.EphemeralDataContext,
    data_source: gx.datasource.fluent.PostgresDatasource,
    suite: gx.ExpectationSuite,
    environment: str,
    report_by_email: bool,
    quality_type: str,
    comment: str = "",
) -> gx.checkpoint.CheckpointResult:
    """Run API DB checkpoint."""
    # Data asset
    data_asset = data_source.add_table_asset(
        name=f"{quality_type}-{environment}", table_name="statique"
    )

    # Batch
    batch = data_asset.add_batch_definition_whole_table(name="FULL_TABLE")

    # Validation
    validation = gx.ValidationDefinition(
        data=batch, suite=suite, name=f"{quality_type}-{environment}"
    )
    validation = context.validation_definitions.add(validation)

    # Checkpoint actions
    action_list = []
    if report_by_email:
        action_list.append(
            gx.checkpoint.EmailAction(
                notify_on="all",
                name=f"{quality_type} expectations report",
                receiver_emails="${GX_RECEIVER_EMAILS}",
                smtp_address="${GX_BREVO_SMTP_ADDRESS}",
                smtp_port="${GX_BREVO_SMTP_PORT}",
                sender_login="${GX_BREVO_SENDER_LOGIN}",
                sender_alias="QualiCharge Bot <contact@qualicharge.beta.gouv.fr>",
                sender_password="${GX_BREVO_PASSWORD}",  # noqa: S106
                use_tls=True,
            )
        )

    checkpoint = gx.Checkpoint(
        name=f"{quality_type}-{environment}",
        validation_definitions=[validation],
        actions=action_list,  # type: ignore[arg-type]
        result_format={"result_format": "COMPLETE"},
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
        description=f"GX validation for API DB instance: {environment}. {comment}",
        key=f"api-db-{quality_type}-{environment}",
    )
    return result


def run_api_db_checkpoint_by_amenageur(  # noqa: PLR0913
    context: gx.data_context.EphemeralDataContext,
    data_source: gx.datasource.fluent.PostgresDatasource,
    suite: gx.ExpectationSuite,
    environment: str,
    report_by_email: bool,
    quality_type: str,
    comment: str = "",
) -> QCReport:
    """Run API DB checkpoint."""
    # QualiCharge markdown report
    report = QCReport(name=f"{quality_type}-{environment}")

    # Run checkpoint for every amenageur
    for amenageur in get_db_amenageurs(environment):
        slug = slugify(amenageur)
        name = f"{quality_type}-{environment}-{slug}"

        try:
            data_source.get_asset(name)
            print(f"Found duplicate for amenageur: {amenageur} ({slug=})")
            continue
        except LookupError:
            pass

        # Data asset
        query = str(
            text(r"SELECT * FROM STATIQUE where nom_amenageur = :amenageur")
            .bindparams(amenageur=amenageur)
            .compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )

        data_asset = data_source.add_query_asset(name=name, query=query)

        # Batch
        batch = data_asset.add_batch_definition_whole_table(name=name)

        # Validation
        validation = gx.ValidationDefinition(data=batch, suite=suite, name=name)
        validation = context.validation_definitions.add(validation)

        # Checkpoint actions
        action_list = []
        if report_by_email:
            action_list.append(
                gx.checkpoint.EmailAction(
                    notify_on="all",
                    name=f"{quality_type} expectations report",
                    receiver_emails="${GX_RECEIVER_EMAILS}",
                    smtp_address="${GX_BREVO_SMTP_ADDRESS}",
                    smtp_port="${GX_BREVO_SMTP_PORT}",
                    sender_login="${GX_BREVO_SENDER_LOGIN}",
                    sender_alias="QualiCharge Bot <contact@qualicharge.beta.gouv.fr>",
                    sender_password="${GX_BREVO_PASSWORD}",  # noqa: S106
                    use_tls=True,
                )
            )

        checkpoint = gx.Checkpoint(
            name=name,
            validation_definitions=[validation],
            actions=action_list,  # type: ignore[arg-type]
            result_format={"result_format": "COMPLETE"},
        )
        result = checkpoint.run()
        if result is None:
            continue

        qc_results = QCExpectationsSuiteResult(
            amenageur=amenageur, success=result.success
        )
        for _, v in result.run_results.items():
            for r in v.results:
                qc_results.suite.append(
                    QCExpectationResult(
                        code=r.expectation_config.meta.get("code"),  # type: ignore[union-attr]
                        success=r.success,
                    )
                )
        report.results.append(qc_results)

    # Generate report
    jinja_env = Environment(
        loader=FileSystemLoader("quality/templates"), autoescape=select_autoescape()
    )
    template = jinja_env.get_template("quality-by-amenageur.md.j2")
    create_markdown_artifact(
        template.render(report=report),
        description=(
            f"# GX validation by `Amenageur` for API DB instance: {environment}. {comment}"  # noqa: E501
        ),
        key=f"api-db-{quality_type}-amenageurs-{environment}",
    )
    return report
