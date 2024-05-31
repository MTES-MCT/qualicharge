"""Tests for QualiCharge CLI."""

from sqlalchemy import func
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import Group, GroupOperationalUnit, User, UserGroup
from qualicharge.cli import app
from qualicharge.schemas.core import OperationalUnit


def test_list_groups(runner, db_session):
    """Test the `list-groups` command."""
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
    result = runner.invoke(app, ["list-groups"], obj=db_session)
    assert result.exit_code == 0

    # Check output
    assert name_one in result.stdout
    assert name_two in result.stdout
    assert ",".join(sorted(u.username for u in users_one)) in result.stdout
    assert ",".join(sorted(u.username for u in users_two)) in result.stdout
    assert ",".join(ou.code for ou in operational_units_one) in result.stdout
    assert ",".join(ou.code for ou in operational_units_two) in result.stdout


def test_create_group(runner, db_session):
    """Test the `create-group` command."""
    GroupFactory.__session__ = db_session

    # Check that no group exists
    assert db_session.exec(select(func.count(Group.id))).one() == 0

    # Proceed
    result = runner.invoke(
        app,
        [
            "create-group",
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
    """Test the `update-group` command."""
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
            "update-group",
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


def test_delete_group(runner, db_session):
    """Test the `delete-group` command."""
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
    result = runner.invoke(app, ["delete-group", name, "--force"], obj=db_session)
    assert result.exit_code == 0

    # Check that group and its relationships have been deleted
    assert db_session.exec(select(func.count(Group.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0
    assert db_session.exec(select(func.count(GroupOperationalUnit.group_id))).one() == 0


def test_list_users(runner, db_session):
    """Test the `list-users` command."""
    UserFactory.__session__ = db_session

    # Check that no user exists
    assert db_session.exec(select(func.count(User.id))).one() == 0

    # Create users
    n_users = 3
    UserFactory.create_batch_sync(n_users)

    # Proceed
    result = runner.invoke(app, ["list-users"], obj=db_session)
    assert result.exit_code == 0

    # Expected number of rows
    assert len(result.stdout.split("\n")) == 6 + n_users


def test_create_user_with_no_group(runner, db_session):
    """Test the `create-user` command when no group exists."""
    # Check that no user or group exists
    assert db_session.exec(select(func.count(User.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0
    assert db_session.exec(select(func.count(Group.id))).one() == 0

    # Proceed
    user = UserFactory.build()
    result = runner.invoke(
        app,
        [
            "create-user",
            "--username",
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
    """Test the `create-user` command."""
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
            "create-user",
            "--username",
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
    """Test the `update-user` command."""
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
            "update-user",
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
    """Test the `delete-user` command."""
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
        app, ["delete-user", user.username, "--force"], obj=db_session
    )
    assert result.exit_code == 0

    # Check that user no longer exists
    assert db_session.exec(select(func.count(User.id))).one() == 0
    assert db_session.exec(select(func.count(UserGroup.group_id))).one() == 0
