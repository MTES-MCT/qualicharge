"""QualiCharge API client CLI: static."""

import json
from typing import Any, Generator, Optional

import click
import typer
from anyio import run
from rich import print
from typing_extensions import Annotated

from ..client import QCC
from ..exceptions import APIRequestError
from .codes import QCCExitCodes

app = typer.Typer(name="static", no_args_is_help=True)


def async_run_api_query(*args) -> Any:
    """An anyio.run wrapper to handle APIRequestError."""
    try:
        return_value = run(*args)
    except APIRequestError as err:
        print("[red]An error occurred while querying the API! More details follow.")
        print(err.args[0])
        raise typer.Exit(QCCExitCodes.API_EXCEPTION) from err
    return return_value


@app.command()
def list(ctx: typer.Context):
    """Get all static entries."""
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
    if not statique and interactive:
        statique = click.get_text_stream("stdin").readline()

    if statique is None:
        print(
            "[red]A statique object is required either from stdin or as an option[/red]"
        )
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION)

    try:
        data = json.loads(statique)
    except json.JSONDecodeError as err:
        print("[red]Invalid JSON input string[/red]")
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION) from err

    created = async_run_api_query(client.static.create, data)

    print("[green]Created statique successfully.[/green]")
    print(created)


@app.command()
def read(ctx: typer.Context, id_pdc_itinerance: str):
    """Get all static entries."""
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
    if not statique and interactive:
        statique = click.get_text_stream("stdin").readline()

    if statique is None:
        print(
            "[red]A statique object is required either from stdin or as an option[/red]"
        )
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION)

    try:
        data = json.loads(statique)
    except json.JSONDecodeError as err:
        print("[red]Invalid JSON input string[/red]")
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION) from err

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

    def parse_input_json_lines(lines) -> Generator[dict, None, None]:
        """Read and JSON parse stdin line by line."""
        for statique in lines:
            try:
                data = json.loads(statique)
            except json.JSONDecodeError as err:
                if ignore_errors:
                    print(f"[orange]Ignored invalid line:[/orange]\n{statique}")
                    continue
                print("[red]Invalid JSON input string[/red]")
                raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION) from err
            yield data

    n_created = async_run_api_query(
        client.static.bulk,
        parse_input_json_lines(click.get_text_stream("stdin")),
        chunk_size,
        ignore_errors,
    )

    print(f"[green]Created {n_created} statiques successfully.[/green]")


if __name__ == "__main__":
    app()
