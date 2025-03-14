"""QualiCharge API client CLI: status."""

import json
from datetime import datetime
from typing import Annotated, Optional

import typer

from ..client import QCC
from .api import async_run_api_query

app = typer.Typer(name="manage", no_args_is_help=True)


@app.command()
def stations(
    ctx: typer.Context,
    siren: str,
    after: Annotated[Optional[datetime], typer.Option("--after")] = None,
):
    """List charging points last known status."""
    client: QCC = ctx.obj

    async def stations():
        async for station in client.manage.read_stations(siren=siren, after=after):
            typer.echo(json.dumps(station))

    async_run_api_query(stations)
