"""Prefect flow: run checkpoints."""

import great_expectations as gx
from checkpoints.static import get_static_checkpoint

api_data_source_name = "api-{environment}"


def set_data_source(context, environment: str):
    """Add API data instance as a data source."""
    context.data_sources.add_postgres(
        name=api_data_source_name.format(environment),
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
    data_source = context.data_sources.get(api_data_source_name.format(environment))
    if table:
        return data_source.add_table_asset(name=name, table_name=table)
    elif query:
        return data_source.add_query_asset(name=name, query=query)
    raise Exception


def check_api_db_instance_quality():
    """Check API database instance quality."""
    context = gx.get_context(mode="ephemeral")

    environment = "development"
    table = "statique"
    asset = "static"
    set_data_source(context, environment)
    static = get_data_asset(context, environment, asset, table=table)
    batch = static.add_batch_definition_whole_table(name="FULL_TABLE")
    checkpoint = get_static_checkpoint(context, batch)
    checkpoint.run()


if __name__ == "__main__":
    check_api_db_instance_quality()
