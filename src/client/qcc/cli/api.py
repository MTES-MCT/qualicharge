"""QualiCharge API client CLI: api."""

from typing import Any

import typer
from anyio import run
from rich import print

from ..exceptions import APIRequestError
from .codes import QCCExitCodes


def async_run_api_query(*args) -> Any:
    """An anyio.run wrapper to handle APIRequestError."""
    try:
        return_value = run(*args)
    except APIRequestError as err:
        print("[red]An error occurred while querying the API! More details follow.")
        print(err.args[0])
        raise typer.Exit(QCCExitCodes.API_EXCEPTION) from err
    return return_value
