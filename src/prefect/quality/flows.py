"""Prefect flow: run checkpoints."""

import great_expectations as gx
from checkpoints.full import get_full_checkpoint


def add_data_source(context, environment: str):
    """Add API data instance as a data source."""
    context.data_sources.add_postgres(
        name=environment,
        connection_string=f"${{QUALICHARGE_API_DATABASE_URLS__{environment}}}",
    )


def add_data_asset(context, environment: str, table: str, name: str):
    """Get data asset for an environment."""
    data_source = context.data_sources.get(environment)
    return data_source.add_table_asset(table_name=table, name=name)


def check_api_db_instance_quality():
    """Check API database instance quality."""
    context = gx.get_context(mode="ephemeral")

    environment = "development"
    add_data_source(context, environment)

    table = "PointDeCharge"
    asset = "pdc"
    pdc = add_data_asset(context, environment, table, asset)
    batch = pdc.add_batch_definition_whole_table(name="FULL_TABLE")
    checkpoint = get_full_checkpoint(context, batch)
    checkpoint.run()


if __name__ == "__main__":
    check_api_db_instance_quality()
