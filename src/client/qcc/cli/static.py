"""QualiCharge API client CLI: static."""

import json
from typing import Optional

import click
import typer
from rich import print
from typing_extensions import Annotated

from ..client import QCC
from .api import async_run_api_query
from .codes import QCCExitCodes
from .utils import parse_input_json_lines, parse_json_parameter

app = typer.Typer(name="static", no_args_is_help=True)


@app.command()
def list(ctx: typer.Context):
    """Get all statique entries."""
    client: QCC = ctx.obj

    async def statiques():
        async for statique in client.static.list():
            typer.echo(json.dumps(statique))

    async_run_api_query(statiques)


@app.command()
def create(
    ctx: typer.Context,
    statique: Optional[str] = None,
    interactive: Annotated[
        bool, typer.Option(help="Read statique from standard input (JSON string)")
    ] = True,
):
    """Create a new Statique.

    You can submit your statique entry to create as a JSON string argument for
    the `--statique` option. Without `--statique` option (but with `--interactive`)
    the command will read and parse the standard input as a JSON string.

    Note that when using the `--interactive` option (active by default), the command
    expects your JSON string on a single row.
    """
    client: QCC = ctx.obj
    data = parse_json_parameter("statique", statique, interactive)  # type: ignore[arg-type]
    created = async_run_api_query(client.static.create, data)
    print("[green]Created statique successfully.[/green]")
    print(created)


@app.command()
def read(ctx: typer.Context, id_pdc_itinerance: str):
    """Read a statique entry."""
    client: QCC = ctx.obj

    read = async_run_api_query(client.static.read, id_pdc_itinerance)
    typer.echo(json.dumps(read))


@app.command()
def update(
    ctx: typer.Context,
    statique: Optional[str] = None,
    interactive: Annotated[
        bool, typer.Option(help="Read statique from standard input (JSON string)")
    ] = True,
):
    """Update an existing Statique.

    You can submit your statique entry to update as a JSON string argument for
    the `--statique` option. Without `--statique` option (but with `--interactive`)
    the command will read and parse the standard input as a JSON string.

    Note that when using the `--interactive` option (active by default), the command
    expects your JSON string on a single row.
    """
    client: QCC = ctx.obj
    data = parse_json_parameter("statique", statique, interactive)  # type: ignore[arg-type]

    if "id_pdc_itinerance" not in data:
        print("[red]Statique object requires an `id_pdc_itinerance` field[/red]")
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION)

    updated = async_run_api_query(client.static.update, data["id_pdc_itinerance"], data)

    print("[green]Updated statique successfully.[/green]")
    print(updated)


@app.command()
def bulk(
    ctx: typer.Context,
    chunk_size: int = 10,
    ignore_errors: bool = False,
):
    """Bulk create new Statique entries.

    Statiques entries will be read from the standard input (one JSON per line).
    """
    client: QCC = ctx.obj

    n_created = async_run_api_query(
        client.static.bulk,
        parse_input_json_lines(click.get_text_stream("stdin"), ignore_errors),
        chunk_size,
        ignore_errors,
    )

    print(f"[green]Created {n_created} statiques successfully.[/green]")


if __name__ == "__main__":
    app()
