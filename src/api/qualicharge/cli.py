"""QualiCharge CLI."""

import logging
from pathlib import Path
from typing import Optional, Sequence, cast

import pandas as pd
import questionary
import typer
from psycopg import Error as PGError
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from sqlalchemy import Column as SAColumn
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from sqlmodel import Session as SMSession
from sqlmodel import select

from .auth.models import UserCreate
from .auth.schemas import Group, ScopesEnum, User
from .conf import settings
from .db import get_session
from .exceptions import IntegrityError as QCIntegrityError
from .fixtures.operational_units import prefixes
from .schemas.core import OperationalUnit
from .schemas.sql import StatiqueImporter

logging.basicConfig(
    level=logging.INFO, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
app = typer.Typer(name="qualicharge", no_args_is_help=True)
console = Console()


@app.command()
def list_groups(ctx: typer.Context):
    """List API groups."""
    session: SMSession = ctx.obj

    groups = session.exec(select(Group)).all()

    table = Table(title="QualiCharge API groups")
    table.add_column("Name", justify="right", style="cyan", no_wrap=True)
    table.add_column("Users", style="magenta")
    table.add_column("Operational Units", justify="right", style="green")

    for group in groups:
        table.add_row(
            group.name,
            ",".join(sorted(user.username for user in group.users)),
            ",".join(ou.code for ou in group.operational_units),
        )
    console.print(table)


@app.command()
def create_group(
    ctx: typer.Context,
    name: str,
    operational_units: Optional[list[str]] = None,
    force: bool = False,
):
    """Create an API group."""
    session: SMSession = ctx.obj

    selected_operational_units = []
    if operational_units is None:
        if not force:
            selected_operational_units = questionary.checkbox(
                "Select group operational unit(s)", choices=prefixes
            ).ask()
    else:
        selected_operational_units = operational_units

    # Get database operational_units
    db_operational_units: Sequence[OperationalUnit] = []
    if len(selected_operational_units):
        db_operational_units = session.exec(
            select(OperationalUnit).filter(
                cast(SAColumn, OperationalUnit.code).in_(selected_operational_units)
            )
        ).all()

    group = Group(name=name, operational_units=db_operational_units)

    if not force:
        print(group)
        print(db_operational_units)
        typer.confirm("Create above group with selected operational units?", abort=True)

    session.add(group)
    session.commit()

    print(f"[bold green]Group {name} created.[/bold green]")


@app.command()
def update_group(
    ctx: typer.Context,
    group_name: str,
    name: Optional[str] = None,
    operational_units: Optional[list[str]] = None,
    force: bool = False,
):
    """Update an API group."""
    session: SMSession = ctx.obj

    # Check group exists in database
    db_group = session.exec(select(Group).where(Group.name == group_name)).one_or_none()
    if db_group is None:
        print(f"[bold red]Group {name} does not exist![/bold red]")
        raise typer.Exit()

    # Copy original group to update
    # (for diff generation while asking for changes confirmation)
    old_group = db_group.model_copy(deep=True)
    old_operational_units = [ou.code for ou in db_group.operational_units]

    # Get updates
    if name:
        db_group.name = name

    if operational_units:
        db_group.operational_units = list(
            session.exec(
                select(OperationalUnit).filter(
                    cast(SAColumn, OperationalUnit.code).in_(operational_units)
                )
            ).all()
        )

    if not force:
        table = Table("Status", "ID", "Name", "Operational units")
        table.add_row(
            "old",
            str(old_group.id),
            old_group.name,
            ",".join(old_operational_units),
            style="red",
        )
        table.add_row(
            "new",
            str(db_group.id),
            db_group.name,
            ",".join(ou.code for ou in db_group.operational_units),
            style="green",
        )
        console.print(table)
        typer.confirm("Update above group with selected operational units?", abort=True)

    session.add(db_group)
    session.commit()

    print(f"[bold green]Group {db_group.name} updated.[/bold green]")


@app.command()
def delete_group(ctx: typer.Context, name: str, force: bool = False):
    """Delete an API group."""
    session: SMSession = ctx.obj

    # Check group exists in database
    db_group = session.exec(select(Group).where(Group.name == name)).one_or_none()
    if db_group is None:
        print(f"[bold red]Group {name} does not exist![/bold red]")
        raise typer.Exit()

    # Ask for confirmation deletion
    if not force:
        print(db_group)
        typer.confirm(
            f"Are you sure you want to delete above {name} group?", abort=True
        )

    # Delete the group
    session.delete(db_group)
    session.commit()

    print(f"[bold yellow]Group {name} deleted.[/bold yellow]")


@app.command()
def list_users(ctx: typer.Context):
    """List API users."""
    session: SMSession = ctx.obj

    users = session.exec(
        select(User).order_by(
            cast(SAColumn, User.last_name), cast(SAColumn, User.first_name)
        )
    ).all()

    fields = [
        "last_name",
        "first_name",
        "username",
        "email",
        "is_active",
        "is_superuser",
        "is_staff",
    ]
    table = Table(*fields, title="QualiCharge API users")

    for user in users:
        style = ""
        if user.is_superuser:
            style += " magenta"
        if user.is_staff:
            style += " bold"
        if not user.is_active:
            style += " italic"
        table.add_row(*[str(getattr(user, field)) for field in fields], style=style)

    console.print(table)


@app.command()
def read_user(ctx: typer.Context, username: str, json: bool = False):
    """Read detailled user informations."""
    session: SMSession = ctx.obj

    db_user = session.exec(select(User).where(User.username == username)).one_or_none()

    if db_user is None:
        print(f"[bold red]User {username} does not exist![/bold red]")
        raise typer.Exit(1)

    out = str(db_user)
    if json:
        out = db_user.model_dump_json(indent=2)
    print(out)


@app.command()
def create_user(  # noqa: PLR0913
    ctx: typer.Context,
    username: str,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    password: Optional[str] = None,
    scopes: Optional[list[str]] = None,
    groups: Optional[list[str]] = None,
    is_active: bool = True,
    is_superuser: bool = False,
    is_staff: bool = False,
    force: bool = False,
):
    """Create an API user."""
    session: SMSession = ctx.obj

    if email is None and not force:
        email = questionary.text("Email:").ask()
    if first_name is None and not force:
        first_name = questionary.text("First name:").ask()
    if last_name is None and not force:
        last_name = questionary.text("Last name:").ask()
    if password is None and not force:
        password1 = questionary.password("Password:").ask()
        questionary.password(
            "Confirm password:", validate=lambda value: value == password1
        ).ask()
        password = password1
    user_scopes = []
    if scopes is None:
        if not force:
            user_scopes = questionary.checkbox(
                "Select user scope(s)", choices=list(ScopesEnum)
            ).ask()
    else:
        user_scopes = scopes
    selected_group_names = []
    if groups is None:
        if not force:
            group_names = session.exec(select(Group.name)).all()
            if len(group_names):
                selected_group_names = questionary.checkbox(
                    "Select user group(s)", choices=group_names
                ).ask()
    else:
        selected_group_names = groups
    user_groups = session.exec(
        select(Group).filter(cast(SAColumn, Group.name).in_(selected_group_names))
    ).all()

    user = UserCreate(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        is_staff=is_staff,
        is_superuser=is_superuser,
        is_active=is_active,
        scopes=user_scopes,
        groups=[group.name for group in user_groups],
    )

    if not force:
        print(user)
        typer.confirm("Create above user?", abort=True)

    session.add(User(**user.model_dump(exclude={"groups"}), groups=user_groups))
    session.commit()

    print(f"[bold green]User {username} created.[/bold green]")


@app.command()
def update_user(  # noqa: PLR0912, PLR0913, PLR0915
    ctx: typer.Context,
    user_name: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    scopes: Optional[list[str]] = None,
    groups: Optional[list[str]] = None,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    is_staff: Optional[bool] = None,
    set_password: bool = False,
    force: bool = False,
):
    """Update an API user."""
    session: SMSession = ctx.obj

    # Check user exists in database
    db_user = session.exec(select(User).where(User.username == user_name)).one_or_none()
    if db_user is None:
        print(f"[bold red]User {user_name} does not exist![/bold red]")
        raise typer.Exit()

    # Copy original user to update
    # (for diff generation while asking for changes confirmation)
    old_user = db_user.model_copy(deep=True)
    old_groups = [group.name for group in db_user.groups]

    # Get updates
    if username:
        db_user.username = username
    if email:
        db_user.email = email
    if first_name:
        db_user.first_name = first_name
    if last_name:
        db_user.last_name = last_name
    if set_password:
        if force:
            print("[bold red]Cannot set password in force mode![/bold red]")
            raise typer.Exit()
        password = questionary.password("Password:").ask()
        questionary.password(
            "Confirm password:", validate=lambda value: value == password
        ).ask()
        db_user.password = settings.PASSWORD_CONTEXT.hash(password)
    if scopes:
        db_user.scopes = [ScopesEnum(scope) for scope in scopes if scope in ScopesEnum]
    if groups:
        db_user.groups = list(
            session.exec(
                select(Group).filter(cast(SAColumn, Group.name).in_(groups))
            ).all()
        )
    if is_active is not None:
        db_user.is_active = is_active
    if is_superuser is not None:
        db_user.is_superuser = is_superuser
    if is_staff is not None:
        db_user.is_staff = is_staff

    if not force:
        table = Table(title="User changes")
        table.add_column("Field", style="bold")
        table.add_column("Old", style="red")
        table.add_column("New", style="green")

        fields = [
            "last_name",
            "first_name",
            "username",
            "email",
            "is_active",
            "is_superuser",
            "is_staff",
            "password",
        ]
        for field in fields:
            old = getattr(old_user, field)
            new = getattr(db_user, field)
            if old != new:
                table.add_row(field, str(old), str(new))
        # Scopes
        old = ", ".join(sorted(old_user.scopes))
        new = ", ".join(sorted(db_user.scopes))
        if old != new:
            table.add_row("scopes", old, new)
        # Groups
        old = ", ".join(sorted(old_groups))
        new = ", ".join(sorted(group.name for group in db_user.groups))
        if old != new:
            table.add_row("groups", old, new)

        console.print(table)
        typer.confirm("Apply changes to selected user?", abort=True)

    session.add(db_user)
    session.commit()

    print(f"[bold green]User {db_user.username} updated.[/bold green]")


@app.command()
def delete_user(ctx: typer.Context, username: str, force: bool = False):
    """Delete an API user."""
    session: SMSession = ctx.obj

    # Check user exists in database
    db_user = session.exec(select(User).where(User.username == username)).one_or_none()
    if db_user is None:
        print(f"[bold red]User {username} does not exist![/bold red]")
        raise typer.Exit()

    # Ask for confirmation deletion
    if not force:
        print(db_user)
        typer.confirm(
            f"Are you sure you want to delete above {username} user?", abort=True
        )

    session.delete(db_user)
    session.commit()

    print(f"[bold yellow]User {username} deleted.[/bold yellow]")


@app.command()
def import_static(ctx: typer.Context, input_file: Path):
    """Import Statique file (parquet format)."""
    session: SMSession = ctx.obj

    # Load dataset
    console.log(f"Reading input file: {input_file}")
    static = pd.read_parquet(input_file)
    console.log(f"Read {len(static.index)} rows")
    importer = StatiqueImporter(static, session.connection())

    console.log("Save to configured database")
    try:
        importer.save()
    except (ProgrammingError, IntegrityError, OperationalError, PGError) as err:
        session.rollback()
        raise QCIntegrityError("Input file importation failed. Rolling back.") from err
    session.commit()
    console.log("Saved (or updated) all entries successfully.")


@app.callback()
def main(ctx: typer.Context):
    """Attach database session to the context object."""
    # Do not attach a new session if it has already been set
    # (e.g. using the CLI test runner)
    if ctx.obj is None:
        ctx.obj = next(get_session())
