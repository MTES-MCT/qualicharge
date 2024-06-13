"""QualiCharge API client CLI: utils."""

import json
from typing import Generator, TextIO

import click
import typer
from rich import print

from .codes import QCCExitCodes


def parse_json_parameter(name: str, parameter: str, interactive: bool) -> dict:
    """Read and JSON parse parameter from option or stdin."""
    # Get parameter value from stdin if empty
    if not parameter and interactive:
        parameter = click.get_text_stream("stdin").readline()

    if parameter is None:
        print(
            (
                f"[red]A {name} object is required "
                "either from stdin or as an option[/red]"
            )
        )
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION)

    # Parse parameter as JSON
    try:
        data = json.loads(parameter)
    except json.JSONDecodeError as err:
        print("[red]Invalid JSON input string[/red]")
        raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION) from err
    return data


def parse_input_json_lines(
    lines: TextIO, ignore_errors: bool
) -> Generator[dict, None, None]:
    """Read and JSON parse stdin line by line."""
    for line in lines:
        try:
            data = json.loads(line)
        except json.JSONDecodeError as err:
            if ignore_errors:
                print(f"[orange]Ignored invalid line:[/orange]\n{line}")
                continue
            print("[red]Invalid JSON input string[/red]")
            raise typer.Exit(QCCExitCodes.PARAMETER_EXCEPTION) from err
        yield data
