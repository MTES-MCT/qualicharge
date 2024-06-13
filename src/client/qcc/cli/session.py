"""QualiCharge API client CLI: statuc."""

from typing import Annotated, Optional

import click
import typer
from rich import print

from ..client import QCC
from .api import async_run_api_query
from .utils import parse_input_json_lines, parse_json_parameter

app = typer.Typer(name="session", no_args_is_help=True)


@app.command()
def create(
    ctx: typer.Context,
    session: Optional[str] = None,
    interactive: Annotated[
        bool, typer.Option(help="Read session from standard input (JSON string)")
    ] = True,
):
    """Create a charging point session.

    You can submit your session entry to create as a JSON string argument for
    the `--status` option. Without `--status` option (but with `--interactive`)
    the command will read and parse the standard input as a JSON string.

    Note that when using the `--interactive` option (active by default), the command
    expects your JSON string on a single row.
    """
    client: QCC = ctx.obj
    data = parse_json_parameter("session", session, interactive)  # type: ignore[arg-type]
    created = async_run_api_query(client.session.create, data)
    print("[green]Created session successfully.[/green]")
    print(created)


@app.command()
def bulk(
    ctx: typer.Context,
    chunk_size: int = 10,
    ignore_errors: bool = False,
):
    """Bulk create new sessions.

    Sessions will be read from the standard input (one JSON per line).
    """
    client: QCC = ctx.obj

    n_created = async_run_api_query(
        client.session.bulk,
        parse_input_json_lines(click.get_text_stream("stdin"), ignore_errors),
        chunk_size,
        ignore_errors,
    )

    print(f"[green]Created {n_created} sessions successfully.[/green]")
