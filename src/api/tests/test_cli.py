"""Tests for QualiCharge CLI."""

from io import StringIO
from typing import cast

import pandas as pd
from pydantic_core import from_json
from sqlalchemy import Column as SAColumn
from sqlalchemy import func
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import Group, GroupOperationalUnit, User, UserGroup
from qualicharge.cli import app
from qualicharge.factories.static import StatiqueFactory
from qualicharge.schemas.core import (
    Amenageur,
    Enseigne,
    Localisation,
    Operateur,
    OperationalUnit,
    PointDeCharge,
    Station,
    StatiqueMV,
)
from qualicharge.schemas.utils import save_statiques


def test_list_groups(runner, db_session):
    """Test the `groups list` command."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    # Check that no group exists
    assert db_session.exec(select(func.count(Group.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0

    operational_units = db_session.exec(select(OperationalUnit)).all()
    operational_units_one = operational_units[:3]
    operational_units_two = operational_units[3:5]

    n_users_by_group = 2
    users_one = UserFactory.create_batch_sync(n_users_by_group)
    users_two = UserFactory.create_batch_sync(n_users_by_group)

    name_one = "ACME"
    GroupFactory.create_sync(
        name=name_one, operational_units=operational_units_one, users=users_one
    )
    name_two = "Wayne Corp. LTD"
    GroupFactory.create_sync(
        name=name_two, operational_units=operational_units_two, users=users_two
    )

    # Proceed
    result = runner.invoke(app, ["groups", "list"], obj=db_session)
    assert result.exit_code == 0

    # Check output
    assert name_one in result.stdout
    assert name_two in result.stdout
    assert ",".join(sorted(u.username for u in users_one)) in result.stdout
    assert ",".join(sorted(u.username for u in users_two)) in result.stdout
    assert ",".join(ou.code for ou in operational_units_one) in result.stdout
    assert ",".join(ou.code for ou in operational_units_two) in result.stdout


def test_create_group(runner, db_session):
    """Test the `groups create` command."""
    GroupFactory.__session__ = db_session

    # Check that no group exists
    assert db_session.exec(select(func.count(Group.id))).one() == 0

    # Proceed
    result = runner.invoke(
        app,
        [
            "groups",
            "create",
            "ACME",
            "--operational-units",
            "FRS63",
            "--operational-units",
            "FR147",
            "--force",
        ],
        obj=db_session,
    )
    assert result.exit_code == 0

    groups = db_session.exec(select(Group)).all()
    assert len(groups) == 1
    assert groups[0].name == "ACME"
    assert {ou.code for ou in groups[0].operational_units} == {"FRS63", "FR147"}


def test_update_group(runner, db_session):
    """Test the `groups update` command."""
    GroupFactory.__session__ = db_session

    # Create group to update
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FRS63")
    ).one()
    group = GroupFactory.create_sync(operational_units=[operational_unit])

    # Check that only one group exists
    assert db_session.exec(select(func.count(Group.id))).one() == 1
    assert db_session.exec(select(func.count(GroupOperationalUnit.group_id))).one() == 1

    # Proceed
    name = "ACME"
    result = runner.invoke(
        app,
        [
            "groups",
            "update",
            group.name,
            "--name",
            name,
            "--operational-units",
            "FR0NX",
            "--operational-units",
            "FR147",
            "--force",
        ],
        obj=db_session,
    )
    assert result.exit_code == 0

    # Test changes
    db_session.refresh(group)
    assert group.name == name
    assert {ou.code for ou in group.operational_units} == {"FR0NX", "FR147"}

    # Test group add
    result = runner.invoke(
        app,
        [
            "groups",
            "update",
            name,
            "-u",
            "FRALL",
            "-u",
            "FRTSL",
            "-af",
        ],
        obj=db_session,
    )
    assert result.exit_code == 0

    # Test changes
    db_session.refresh(group)
    assert group.name == name
    assert {ou.code for ou in group.operational_units} == {
        "FR0NX",
        "FR147",
        "FRALL",
        "FRTSL",
    }

    # Test group delete
    result = runner.invoke(
        app,
        [
            "groups",
            "update",
            name,
            "-u",
            "FRALL",
            "-u",
            "FRTSL",
            "-rf",
        ],
        obj=db_session,
    )
    assert result.exit_code == 0

    # Test changes
    db_session.refresh(group)
    assert group.name == name
    assert {ou.code for ou in group.operational_units} == {
        "FR0NX",
        "FR147",
    }


def test_delete_group(runner, db_session):
    """Test the `groups delete` command."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    # Check that no group exists
    assert db_session.exec(select(func.count(Group.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0
    assert db_session.exec(select(func.count(GroupOperationalUnit.group_id))).one() == 0

    operational_units = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == "FRS63")
    ).all()
    n_users = 3
    users = UserFactory.create_batch_sync(n_users)

    name = "ACME"
    GroupFactory.create_sync(
        name=name, operational_units=operational_units, users=users
    )

    # Only one group should exist
    db_group = db_session.exec(select(Group)).one()
    assert db_group.name == name
    assert len(db_group.users) == n_users
    assert len(db_group.operational_units) == 1
    # ... with its m2m relationships
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == n_users
    assert db_session.exec(select(func.count(GroupOperationalUnit.group_id))).one() == 1

    # Proceed
    result = runner.invoke(app, ["groups", "delete", name, "--force"], obj=db_session)
    assert result.exit_code == 0

    # Check that group and its relationships have been deleted
    assert db_session.exec(select(func.count(Group.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0
    assert db_session.exec(select(func.count(GroupOperationalUnit.group_id))).one() == 0


def test_list_users(runner, db_session):
    """Test the `users list` command."""
    UserFactory.__session__ = db_session

    # Check that no user exists
    assert db_session.exec(select(func.count(User.id))).one() == 0

    # Create users
    n_users = 3
    UserFactory.create_batch_sync(n_users)

    # Proceed
    result = runner.invoke(app, ["users", "list"], obj=db_session)
    assert result.exit_code == 0

    # Expected number of rows
    assert len(result.stdout.split("\n")) == 6 + n_users


def test_read_user(runner, db_session):
    """Test the `users read` command."""
    UserFactory.__session__ = db_session

    db_user = UserFactory.create_sync()

    # Unknown user
    result = runner.invoke(app, ["users", "read", "foo"], obj=db_session)
    assert result.exit_code == 1
    assert "User foo does not exist!" in result.stdout

    # Proceed
    result = runner.invoke(app, ["users", "read", db_user.username], obj=db_session)
    assert result.exit_code == 0

    # Expected data
    assert db_user.first_name in result.stdout
    assert db_user.last_name in result.stdout
    assert db_user.email in result.stdout
    assert db_user.username in result.stdout
    assert str(db_user.id) in result.stdout


def test_read_user_json_flag(runner, db_session):
    """Test the `users read --json` command."""
    UserFactory.__session__ = db_session

    db_user = UserFactory.create_sync()

    # Proceed
    result = runner.invoke(
        app, ["users", "read", "--json", db_user.username], obj=db_session
    )
    assert result.exit_code == 0

    # Parse output as a JSON string
    output_user = User(**from_json(result.output))

    # Expected output
    assert output_user.first_name == db_user.first_name
    assert output_user.last_name == db_user.last_name
    assert output_user.email == db_user.email
    assert output_user.username == db_user.username
    assert output_user.id == str(db_user.id)


def test_create_user_with_no_group(runner, db_session):
    """Test the `users create` command when no group exists."""
    # Check that no user or group exists
    assert db_session.exec(select(func.count(User.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0
    assert db_session.exec(select(func.count(Group.id))).one() == 0

    # Proceed
    user = UserFactory.build()
    result = runner.invoke(
        app,
        [
            "users",
            "create",
            user.username,
            "--email",
            user.email,
            "--first-name",
            user.first_name,
            "--last-name",
            user.last_name,
            "--password",
            "supersecret",
            "--scopes",
            "all:read",
            "--scopes",
            "all:create",
            "--is-active",
            "--no-is-superuser",
            "--is-staff",
        ],
        obj=db_session,
        input="y\n",
    )
    assert result.exit_code == 0
    assert db_session.exec(select(func.count(User.id))).one() == 1

    # Check created user
    db_user = db_session.exec(select(User).where(User.username == user.username)).one()
    assert db_user.email == user.email
    assert db_user.first_name == user.first_name
    assert db_user.last_name == user.last_name
    assert db_user.password != "supersecret"  # noqa: S105
    assert set(db_user.scopes) == {"all:read", "all:create"}
    assert db_user.is_active is True
    assert db_user.is_superuser is False
    assert db_user.is_staff is True
    assert db_user.groups == []


def test_create_user(runner, db_session):
    """Test the `users create` command."""
    GroupFactory.__session__ = db_session

    n_groups = 2
    groups = GroupFactory.create_batch_sync(n_groups)

    # Check that no user exists
    assert db_session.exec(select(func.count(User.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0

    # Proceed
    user = UserFactory.build()
    result = runner.invoke(
        app,
        [
            "users",
            "create",
            user.username,
            "--email",
            user.email,
            "--first-name",
            user.first_name,
            "--last-name",
            user.last_name,
            "--password",
            "supersecret",
            "--scopes",
            "all:read",
            "--scopes",
            "all:create",
            "--is-active",
            "--no-is-superuser",
            "--is-staff",
            "--force",
            "--groups",
            groups[0].name,
            "--groups",
            groups[1].name,
        ],
        obj=db_session,
    )
    assert result.exit_code == 0
    assert db_session.exec(select(func.count(User.id))).one() == 1
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == n_groups

    # Check created user
    db_user = db_session.exec(select(User).where(User.username == user.username)).one()
    assert db_user.email == user.email
    assert db_user.first_name == user.first_name
    assert db_user.last_name == user.last_name
    assert db_user.password != "supersecret"  # noqa: S105
    assert set(db_user.scopes) == {"all:read", "all:create"}
    assert db_user.is_active is True
    assert db_user.is_superuser is False
    assert db_user.is_staff is True
    assert {group.name for group in db_user.groups} == {group.name for group in groups}


def test_update_user(runner, db_session):
    """Test the `users update` command."""
    GroupFactory.__session__ = db_session
    UserFactory.__session__ = db_session

    # Create user and related groups
    n_groups = 2
    groups = GroupFactory.create_batch_sync(n_groups)
    user = UserFactory.create_sync(
        is_active=False,
        is_superuser=True,
        is_staff=False,
        groups=groups,
    )

    # Updates
    new_group = GroupFactory.create_sync()
    new_user = UserFactory.build(
        is_active=True,
        is_superuser=False,
        is_staff=True,
        groups=[new_group],
        scopes=["all:read", "all:create"],
    )

    # Proceed
    result = runner.invoke(
        app,
        [
            "users",
            "update",
            user.username,
            "--username",
            new_user.username,
            "--email",
            new_user.email,
            "--first-name",
            new_user.first_name,
            "--last-name",
            new_user.last_name,
            "--scopes",
            "all:read",
            "--scopes",
            "all:create",
            "--is-active",
            "--no-is-superuser",
            "--is-staff",
            "--force",
            "--groups",
            new_group.name,
        ],
        obj=db_session,
    )
    assert result.exit_code == 0

    db_session.refresh(user)

    fields = [
        "username",
        "email",
        "last_name",
        "first_name",
        "is_active",
        "is_superuser",
        "is_staff",
        "scopes",
    ]
    for field in fields:
        assert getattr(user, field) == getattr(new_user, field)
    assert user.groups == new_user.groups


def test_delete_user(runner, db_session):
    """Test the `users delete` command."""
    GroupFactory.__session__ = db_session
    UserFactory.__session__ = db_session

    # Create user and related groups
    n_groups = 2
    groups = GroupFactory.create_batch_sync(n_groups)
    user = UserFactory.create_sync(groups=groups)
    assert db_session.exec(select(func.count(User.id))).one() == 1
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == n_groups

    # Proceed
    result = runner.invoke(
        app, ["users", "delete", user.username, "--force"], obj=db_session
    )
    assert result.exit_code == 0

    # Check that user no longer exists
    assert db_session.exec(select(func.count(User.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0


def test_ou_list(runner, db_session):
    """Test the `ou list` command."""
    GroupFactory.__session__ = db_session

    operational_units = db_session.exec(select(OperationalUnit)).all()

    # No filters applied, we display all operational units
    result = runner.invoke(app, ["ou", "list"], obj=db_session)
    for ou in operational_units:
        assert ou.code in result.stdout

    # Apply an operational unit code filter
    result = runner.invoke(app, ["ou", "list", "-p", "FRTS%"], obj=db_session)
    rows = 8
    assert len(result.stdout.split("\n")) == rows
    for expected in ("FRTSL", "FRTSC"):
        assert expected in result.stdout

    # Exact match filter
    result = runner.invoke(app, ["ou", "list", "-p", "FRTSL"], obj=db_session)
    rows = 7
    assert len(result.stdout.split("\n")) == rows
    assert "FRTSL" in result.stdout

    # No match filter
    result = runner.invoke(app, ["ou", "list", "-p", "FOO"], obj=db_session)
    rows = 6
    assert len(result.stdout.split("\n")) == rows

    # Create a group and associate this group with an operational unit
    ou_one = db_session.exec(
        select(OperationalUnit).where(
            cast(SAColumn, OperationalUnit.code).like("FRTSL")
        )
    ).all()
    name_one = "ACME"
    GroupFactory.create_sync(name=name_one, operational_units=ou_one)

    # Exact match filter (with associated group)
    result = runner.invoke(app, ["ou", "list", "-p", "FRTSL"], obj=db_session)
    rows = 7
    assert len(result.stdout.split("\n")) == rows
    assert "FRTSL" in result.stdout
    assert "ACME" in result.stdout

    # Create a second group and associate this group with an operational unit
    name_two = "Foo"
    GroupFactory.create_sync(name=name_two, operational_units=ou_one)

    # Exact match filter (with associated groups)
    result = runner.invoke(app, ["ou", "list", "-p", "FRTSL"], obj=db_session)
    rows = 7
    assert len(result.stdout.split("\n")) == rows
    assert "FRTSL" in result.stdout
    assert "ACME,Foo" in result.stdout

    # Linked operational units filter
    result = runner.invoke(app, ["ou", "list", "-l"], obj=db_session)
    rows = 7
    assert len(result.stdout.split("\n")) == rows
    assert "FRTSL" in result.stdout
    assert "ACME,Foo" in result.stdout

    # No filters applied, we still display all operational units
    result = runner.invoke(app, ["ou", "list", "-L"], obj=db_session)
    for ou in operational_units:
        assert ou.code in result.stdout

    # Create a third group and associate this group with another operational unit
    ou_two = db_session.exec(
        select(OperationalUnit).where(
            cast(SAColumn, OperationalUnit.code).like("FRFAS")
        )
    ).all()
    name_three = "Bar"
    GroupFactory.create_sync(name=name_three, operational_units=ou_two)

    # Linked operational units filter
    result = runner.invoke(app, ["ou", "list", "-l"], obj=db_session)
    rows = 8
    assert len(result.stdout.split("\n")) == rows
    assert "FRTSL" in result.stdout
    assert "ACME,Foo" in result.stdout
    assert "FRFAS" in result.stdout
    assert "Bar" in result.stdout


def test_import_static(runner, db_session):
    """Test the `statics import` command."""
    # Create statique data to import
    size = 5
    statiques = StatiqueFactory.batch(size=size)
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )

    # No database records exist yet
    assert db_session.exec(select(func.count(Amenageur.id))).one() == 0
    assert db_session.exec(select(func.count(Enseigne.id))).one() == 0
    assert db_session.exec(select(func.count(Localisation.id))).one() == 0
    assert db_session.exec(select(func.count(Operateur.id))).one() == 0
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 0
    assert db_session.exec(select(func.count(Station.id))).one() == 0

    # Write parquet file to import
    file_path = "test.parquet"
    with runner.isolated_filesystem():
        df.to_parquet(file_path)
        result = runner.invoke(app, ["statics", "import", file_path], obj=db_session)
    assert result.exit_code == 0

    # Assert we've created expected records
    assert db_session.exec(select(func.count(Amenageur.id))).one() == size
    assert db_session.exec(select(func.count(Enseigne.id))).one() == size
    assert db_session.exec(select(func.count(Localisation.id))).one() == size
    assert db_session.exec(select(func.count(Operateur.id))).one() == size
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == size
    assert db_session.exec(select(func.count(Station.id))).one() == size


def test_import_static_with_integrity_exception(runner, db_session):
    """Test the `statics import` command with integrity exception."""
    # Create statique data to import
    statiques = StatiqueFactory.batch(size=5)
    statiques[1].id_pdc_itinerance = "FRS63E0001"
    statiques[3].id_pdc_itinerance = "FRS63E0001"
    df = pd.read_json(
        StringIO(f"{'\n'.join([s.model_dump_json() for s in statiques])}"),
        lines=True,
        dtype_backend="pyarrow",
    )

    # No database records exist yet
    assert db_session.exec(select(func.count(Amenageur.id))).one() == 0
    assert db_session.exec(select(func.count(Enseigne.id))).one() == 0
    assert db_session.exec(select(func.count(Localisation.id))).one() == 0
    assert db_session.exec(select(func.count(Operateur.id))).one() == 0
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 0
    assert db_session.exec(select(func.count(Station.id))).one() == 0

    # Write parquet file to import
    file_path = "test.parquet"
    with runner.isolated_filesystem():
        df.to_parquet(file_path)
        result = runner.invoke(app, ["statics", "import", file_path], obj=db_session)
    assert result.exit_code == 1
    assert "Input file importation failed. Rolling back." in str(result.exception)

    # Assert we've not created any record
    assert db_session.exec(select(func.count(Amenageur.id))).one() == 0
    assert db_session.exec(select(func.count(Enseigne.id))).one() == 0
    assert db_session.exec(select(func.count(Localisation.id))).one() == 0
    assert db_session.exec(select(func.count(Operateur.id))).one() == 0
    assert db_session.exec(select(func.count(PointDeCharge.id))).one() == 0
    assert db_session.exec(select(func.count(Station.id))).one() == 0


def test_refresh_static(runner, db_session):
    """Test the `statics refresh` command."""
    # Create points of charge
    n_pdc = 4
    save_statiques(db_session, StatiqueFactory.batch(n_pdc))
    assert db_session.exec(select(func.count(StatiqueMV.pdc_id))).one() == 0

    # Proceed
    result = runner.invoke(
        app, ["statics", "refresh", "--concurrently"], obj=db_session
    )
    assert result.exit_code == 0
    assert db_session.exec(select(func.count(StatiqueMV.pdc_id))).one() == n_pdc
