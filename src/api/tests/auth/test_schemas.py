"""Tests for qualicharge.auth.schemas module."""

import logging
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.types import UUID
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.models import UserCreate
from qualicharge.auth.schemas import (
    GroupOperationalUnit,
    PasswordCheckStatus,
    ScopesEnum,
    User,
    UserGroup,
)
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
    assert settings.PASSWORD_CONTEXT.identify(db_user.password)


def test_user_check_password(db_session):
    """Test user check_password method."""
    UserFactory.__session__ = db_session

    user = UserFactory.build()
    with pytest.raises(ValueError, match="Password required"):
        user.password = UserCreate.set_password(None)
    user.password = UserCreate.set_password("foo")

    # Check password
    assert settings.PASSWORD_CONTEXT.identify(user.password)
    # There is no old password to fall back to
    assert user.check_password("bar") is PasswordCheckStatus.INVALID
    assert user.check_password("foo") is PasswordCheckStatus.VALID


def test_user_check_password_with_old_password(db_session, caplog):
    """Test user check_password method using the old password."""
    UserFactory.__session__ = db_session

    caplog.set_level(logging.INFO)
    user = UserFactory.build()
    user.password = UserCreate.set_password("foo")
    user.old_password = UserCreate.set_password("bar")
    user.old_password_expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    # Check password
    assert settings.PASSWORD_CONTEXT.identify(user.password)
    assert settings.PASSWORD_CONTEXT.identify(user.old_password)

    # We felt back to the old password
    assert user.check_password("bar") is PasswordCheckStatus.OLD

    # We should have logged a message
    assert (
        "qualicharge.auth.schemas",
        logging.WARNING,
        f"Old password is still in use for user {user.username}",
    ) in caplog.record_tuples

    # The new password is ok
    assert user.check_password("foo") is PasswordCheckStatus.VALID


def test_user_check_password_with_expired_old_password(db_session):
    """Test user check_password method using the expired old password."""
    UserFactory.__session__ = db_session

    user = UserFactory.build()
    user.password = UserCreate.set_password("foo")
    user.old_password = UserCreate.set_password("bar")
    user.old_password_expires_at = datetime.now(timezone.utc) - timedelta(days=1)

    # The old password expired and cannot be used anymore
    assert user.check_password("bar") is PasswordCheckStatus.EXPIRED


def test_user_check_password_with_old_password_without_expiry(db_session, caplog):
    """Test user check_password method when old password has no expiry set."""
    UserFactory.__session__ = db_session

    caplog.set_level(logging.INFO)
    user = UserFactory.build()
    user.password = UserCreate.set_password("foo")
    user.old_password = UserCreate.set_password("bar")

    # An old password without expiry is considered expired
    assert user.check_password("bar") is PasswordCheckStatus.EXPIRED

    # No fallback warning should have been logged
    assert (
        "qualicharge.auth.schemas",
        logging.WARNING,
        f"Old password is still in use for user {user.username}",
    ) not in caplog.record_tuples


def test_user_check_password_with_old_password_and_unknown_candidate(db_session):
    """Test user check_password method when candidate matches neither password."""
    UserFactory.__session__ = db_session

    user = UserFactory.build()
    user.password = UserCreate.set_password("foo")
    user.old_password = UserCreate.set_password("bar")
    user.old_password_expires_at = datetime.now(timezone.utc) + timedelta(days=1)

    # The candidate matches neither the new nor the old password
    assert user.check_password("baz") is PasswordCheckStatus.INVALID


def test_user_clean_old_password(db_session):
    """Test user clean_old_password method."""
    UserFactory.__session__ = db_session

    user = UserFactory.build(
        old_password_expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    user.password = UserCreate.set_password("foo")
    user.old_password = UserCreate.set_password("bar")

    user.clean_old_password()

    assert user.old_password is None
    assert user.old_password_expires_at is None


def test_user_password_rotation_audits(db_session, versioning_manager):
    """Test that password hashes are excluded from the audit trail."""
    UserFactory.__session__ = db_session
    Activity = versioning_manager.activity_cls

    user = UserFactory.create_sync()

    def latest_user_activity() -> Activity:
        return db_session.exec(
            select(Activity)
            .where(
                Activity.table_name == "user",
                Activity.data["id"].astext.cast(UUID) == user.id,
            )
            .order_by(Activity.issued_at.desc())
        ).first()

    # The insert activity should not expose the password hash
    activity = latest_user_activity()
    assert activity.verb == "insert"
    assert "password" not in activity.changed_data
    assert "old_password" not in activity.changed_data

    # Rotate the user password
    user.password = UserCreate.set_password("new-password")
    user.old_password = UserCreate.set_password("old-password")
    user.old_password_expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # The update activity should not expose password hashes, but should
    # record the old password expiry timestamp
    activity = latest_user_activity()
    assert activity.verb == "update"
    assert "password" not in activity.changed_data
    assert "old_password" not in activity.changed_data
    assert "password" not in activity.old_data
    assert "old_password" not in activity.old_data
    assert (
        datetime.fromisoformat(activity.changed_data["old_password_expires_at"]).date()
        == user.old_password_expires_at.date()
    )

    # Clean the old password
    user.clean_old_password()
    db_session.add(user)
    db_session.commit()

    # Neither the update activity nor the audit trail should expose hashes
    activity = latest_user_activity()
    assert activity.verb == "update"
    assert "password" not in activity.changed_data
    assert "old_password" not in activity.changed_data
    # The old password expiry reset is tracked (without any hash)
    assert activity.changed_data["old_password_expires_at"] is None
