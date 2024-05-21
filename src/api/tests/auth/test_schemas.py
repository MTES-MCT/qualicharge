"""Tests for qualicharge.auth.schemas module."""

from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import GroupOperationalUnit, ScopesEnum, User, UserGroup
from qualicharge.schemas.core import OperationalUnit


def test_create_user_group_operational_units(db_session):
    """Test the user to operational unit relationship."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    # Create users and groups
    user_one, user_two = UserFactory.create_batch_sync(2)
    group_one, group_two = GroupFactory.create_batch_sync(2)
    db_session.add(UserGroup(user_id=user_one.id, group_id=group_one.id))
    db_session.add(UserGroup(user_id=user_two.id, group_id=group_two.id))

    assert group_one.users == [
        user_one,
    ]
    assert group_two.users == [
        user_two,
    ]

    # Link group to an operational unit
    code = "FRS63"
    operational_unit = db_session.exec(
        select(OperationalUnit).where(OperationalUnit.code == code)
    ).one()
    db_session.add(
        GroupOperationalUnit(
            group_id=group_one.id, operational_unit_id=operational_unit.id
        )
    )

    assert user_one.groups[0].operational_units[0].id == operational_unit.id


def test_create_user_scopes(db_session):
    """Test user scope creation."""
    UserFactory.__session__ = db_session

    user = UserFactory.create_sync(
        scopes=[
            ScopesEnum.STATIC_CREATE,
            ScopesEnum.STATIC_READ,
        ]
    )
    db_user = db_session.exec(select(User).where(User.email == user.email)).one()

    assert db_user.scopes == [
        ScopesEnum.STATIC_CREATE,
        ScopesEnum.STATIC_READ,
    ]
    assert user == db_user
