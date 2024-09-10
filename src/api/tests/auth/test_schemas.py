"""Tests for qualicharge.auth.schemas module."""

import pytest
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.models import UserCreate
from qualicharge.auth.schemas import GroupOperationalUnit, ScopesEnum, User, UserGroup
from qualicharge.conf import settings
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


def test_user_operational_units_property(db_session):
    """Test the `User.operational_units` property."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    # Create a user and three groups
    user = UserFactory.create_sync()
    groups = GroupFactory.create_batch_sync(3)
    for group in groups:
        db_session.add(UserGroup(user_id=user.id, group_id=group.id))

    # Link groups to operational units
    codes = ["FRS63", "FRA31", "FRAIR"]
    for code, group in zip(codes, groups, strict=True):
        operational_unit = db_session.exec(
            select(OperationalUnit).where(OperationalUnit.code == code)
        ).one()
        db_session.add(
            GroupOperationalUnit(
                group_id=group.id, operational_unit_id=operational_unit.id
            )
        )

    assert {
        operational_unit.code for operational_unit in user.operational_units
    } == set(codes)


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


def test_user_set_password(db_session):
    """Test user set_password setter."""
    # By default no password has been set
    user = UserCreate(
        username="johndoe",
        email="john@doe.com",
        is_active=True,
        is_staff=True,
        is_superuser=True,
        password="foo",  # noqa: S106
    )
    assert user.password is not None
    # Make sure that its a hash password with a supported algorithm
    assert settings.PASSWORD_CONTEXT.identify(user.password)

    # Create a database user from this user instance
    db_user = User(**user.model_dump())

    # Save user to database
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    assert settings.PASSWORD_CONTEXT.identify(db_user.password)


def test_user_check_password(db_session):
    """Test user check_password validator."""
    UserFactory.__session__ = db_session

    user = UserFactory.build()
    with pytest.raises(ValueError, match="Password required"):
        user.password = UserCreate.set_password(None)
    user.password = UserCreate.set_password("foo")

    # Save user to database
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Check password
    assert settings.PASSWORD_CONTEXT.identify(user.password)
    assert user.check_password("bar") is False
    assert user.check_password("foo")
