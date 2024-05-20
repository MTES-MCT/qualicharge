"""QualiCharge auth.utils module."""

from typing import Sequence, cast

from sqlalchemy import Column as SAColumn
from sqlalchemy.sql.roles import JoinTargetRole
from sqlmodel import Session as SMSession
from sqlmodel import select

from qualicharge.schemas.core import OperationalUnit

from .schemas import Group, User


def get_user_operational_units(user: User, session: SMSession) -> Sequence[str]:
    """Get user related operational unit codes."""
    return session.exec(
        select(OperationalUnit.code)
        .join(cast(JoinTargetRole, OperationalUnit.groups))
        .filter(cast(SAColumn, Group.id).in_(group.id for group in user.groups))
    ).all()
