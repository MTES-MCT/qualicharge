"""Tests for qualicharge.auth.utils schemas module."""

from random import sample
from typing import cast

from sqlalchemy import Column as SAColumn
from sqlmodel import select

from qualicharge.auth.factories import GroupFactory, UserFactory
from qualicharge.auth.schemas import GroupOperationalUnit, UserGroup
from qualicharge.auth.utils import get_user_operational_units
from qualicharge.fixtures.operational_units import data as operational_unit_data
from qualicharge.schemas.core import OperationalUnit


def test_user_get_operational_units(db_session):
    """Test the User get_operational_units utility."""
    UserFactory.__session__ = db_session
    GroupFactory.__session__ = db_session

    # Create user, groups and link them (with operational units)
    user = UserFactory.create_sync()
    n_groups = 8
    groups = GroupFactory.create_batch_sync(n_groups)
    user_n_groups = 2
    user_groups = sample(groups, user_n_groups)
    operational_unit_codes = [
        operational_unit.code
        for operational_unit in sample(operational_unit_data, n_groups)
    ]
    operational_units = db_session.exec(
        select(OperationalUnit).where(
            cast(SAColumn, OperationalUnit.code).in_(operational_unit_codes)
        )
    )
    db_session.add_all(
        UserGroup(user_id=user.id, group_id=group.id) for group in user_groups
    )
    db_session.add_all(
        GroupOperationalUnit(group_id=group.id, operational_unit_id=operational_unit.id)
        for group, operational_unit in zip(groups, operational_units, strict=True)
    )

    # Get operational unit codes
    user_operational_unit_codes = get_user_operational_units(user, db_session)
    assert len(user_operational_unit_codes) == user_n_groups
    assert set(user_operational_unit_codes) == {
        operational_unit.code
        for group in user.groups
        for operational_unit in group.operational_units
    }
