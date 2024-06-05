"""QualiCharge API client CLI: auth."""

import typer
from anyio import run
from rich import print

from ..client import QCC

app = typer.Typer(name="auth", no_args_is_help=True)


@app.command()
def whoami(ctx: typer.Context):
    """Get details about your API account."""
    client: QCC = ctx.obj
    user = run(client.auth.whoami)
    print(user)


if __name__ == "__main__":
    app()
