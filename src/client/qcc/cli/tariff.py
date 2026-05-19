"""QualiCharge API client CLI: tariff."""

import json
from datetime import datetime
from typing import Annotated, List, Optional

import typer
from rich import print

from ..client import QCC
from .api import async_run_api_query
from .utils import parse_json_parameter

app = typer.Typer(name="tariff", no_args_is_help=True)


@app.command()
def list(
    ctx: typer.Context,
    from_: Annotated[Optional[datetime], typer.Option("--from")] = None,
    to: Optional[datetime] = None,
    pdc: Optional[List[str]] = None,
    current: Optional[bool] = None,
):
    """List tariffs."""
    client: QCC = ctx.obj

    async def tariffs():
        async for tariff in client.tariff.list(
            from_=from_,
            to=to,
            pdc=pdc,
            current=current,
        ):
            typer.echo(json.dumps(tariff))

    async_run_api_query(tariffs)


@app.command()
def create(
    ctx: typer.Context,
    tariff: Optional[str] = None,
    interactive: Annotated[
        bool, typer.Option(help="Read tariff from standard input (JSON string)")
    ] = True,
):
    """Create a tariff."""
    client: QCC = ctx.obj
    data = parse_json_parameter("tariff", tariff, interactive)  # type: ignore[arg-type]
    created = async_run_api_query(client.tariff.create, data)
    print("[green]Created tariff successfully.[/green]")
    print(created)


@app.command()
def read(ctx: typer.Context, id_: str):
    """Read a tariff by its QualiCharge UUID."""
    client: QCC = ctx.obj

    read = async_run_api_query(client.tariff.read, id_)
    typer.echo(json.dumps(read))


@app.command()
def applicable(
    ctx: typer.Context,
    id_pdc_itinerance: str,
    at: Optional[datetime] = None,
):
    """Read applicable tariff for a charge point."""
    client: QCC = ctx.obj

    tariff = async_run_api_query(client.tariff.applicable, id_pdc_itinerance, at)
    typer.echo(json.dumps(tariff))


@app.command()
def apply(ctx: typer.Context, id_pdc_itinerance: str, tariff_id: str):
    """Apply a tariff to a charge point."""
    client: QCC = ctx.obj

    tariff = async_run_api_query(client.tariff.apply, id_pdc_itinerance, tariff_id)
    typer.echo(json.dumps(tariff))
