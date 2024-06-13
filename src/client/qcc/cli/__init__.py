"""QualiCharge API client CLI, aka `qcc`."""

from typing import Optional

import typer
from typing_extensions import Annotated

from ..client import QCC
from ..conf import settings
from . import auth, session, static, status

app = typer.Typer(name="qcc", no_args_is_help=True)
app.add_typer(auth.app)
app.add_typer(static.app)
app.add_typer(status.app)
app.add_typer(session.app)


@app.callback()
def main(
    ctx: typer.Context,
    username: Annotated[
        Optional[str],
        typer.Option(
            help="Can be set using the QCC_API_LOGIN_USERNAME environment variable"
        ),
    ] = None,
    password: Annotated[
        Optional[str],
        typer.Option(
            help="Can be set using the QCC_API_LOGIN_PASSWORD environment variable"
        ),
    ] = None,
    api_root_url: Annotated[
        Optional[str],
        typer.Option(help="Can be set using the QCC_API_ROOT_URL environment variable"),
    ] = None,
):
    """QualiCharge API client."""
    if not username:
        username = settings.API_LOGIN_USERNAME
    if not password:
        password = settings.API_LOGIN_PASSWORD
    if not api_root_url:
        api_root_url = str(settings.API_ROOT_URL)

    # Do not attach a new instance if it has already been set
    # (e.g. using the CLI test runner)
    if ctx.obj is None:
        ctx.obj = QCC(
            username=username,  # type: ignore[arg-type]
            password=password,  # type: ignore[arg-type]
            api_root_url=api_root_url,
        )
