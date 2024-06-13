"""QualiCharge API client CLI: status."""

import json
from datetime import datetime
from typing import Annotated, List, Optional

import click
import typer
from rich import print

from ..client import QCC
from .api import async_run_api_query
from .utils import parse_input_json_lines, parse_json_parameter

app = typer.Typer(name="status", no_args_is_help=True)


@app.command()
def list(
    ctx: typer.Context,
    from_: Annotated[Optional[datetime], typer.Option("--from")] = None,
    pdc: Optional[List[str]] = None,
    station: Optional[List[str]] = None,
):
    """List charging points last known status."""
    client: QCC = ctx.obj

    async def statuses():
        async for status in client.status.list(from_=from_, pdc=pdc, station=station):
            typer.echo(json.dumps(status))

    async_run_api_query(statuses)


@app.command()
def create(
    ctx: typer.Context,
    status: Optional[str] = None,
    interactive: Annotated[
        bool, typer.Option(help="Read status from standard input (JSON string)")
    ] = True,
):
    """Create a charging point status.

    You can submit your status entry to create as a JSON string argument for
    the `--status` option. Without `--status` option (but with `--interactive`)
    the command will read and parse the standard input as a JSON string.

    Note that when using the `--interactive` option (active by default), the command
    expects your JSON string on a single row.
    """
    client: QCC = ctx.obj
    data = parse_json_parameter("status", status, interactive)  # type: ignore[arg-type]
    created = async_run_api_query(client.status.create, data)
    print("[green]Created status successfully.[/green]")
    print(created)


@app.command()
def read(ctx: typer.Context, id_pdc_itinerance: str):
    """Get charging point status."""
    client: QCC = ctx.obj

    read = async_run_api_query(client.status.read, id_pdc_itinerance)
    typer.echo(json.dumps(read))


@app.command()
def history(
    ctx: typer.Context,
    id_pdc_itinerance: str,
    from_: Annotated[Optional[datetime], typer.Option("--from")] = None,
):
    """Get charging point history."""
    client: QCC = ctx.obj

    async def statuses():
        async for status in client.status.history(id_pdc_itinerance, from_=from_):
            typer.echo(json.dumps(status))

    async_run_api_query(statuses)


@app.command()
def bulk(
    ctx: typer.Context,
    chunk_size: int = 10,
    ignore_errors: bool = False,
):
    """Bulk create new statuses.

    Statuses will be read from the standard input (one JSON per line).
    """
    client: QCC = ctx.obj

    n_created = async_run_api_query(
        client.status.bulk,
        parse_input_json_lines(click.get_text_stream("stdin"), ignore_errors),
        chunk_size,
        ignore_errors,
    )

    print(f"[green]Created {n_created} statuses successfully.[/green]")
