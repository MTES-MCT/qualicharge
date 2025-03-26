"""Fixtures for QualiCharge API database."""

from typing import AsyncGenerator

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from postgresql_audit.base import VersioningManager
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import configure_mappers, declarative_base
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from qualicharge.api.v1 import app as v1
from qualicharge.auth.schemas import Group, User
from qualicharge.conf import settings
from qualicharge.db import get_session
from qualicharge.fixtures.operational_units import operational_units
from qualicharge.schemas import core


@pytest.fixture(scope="session")
def versioning_manager():
    """postgresql_audit versioning_manager instance."""
    vm = VersioningManager()
    vm.init(declarative_base(metadata=SQLModel.metadata))
    yield vm
    vm.remove_listeners()


@pytest.fixture(scope="session")
async def db_engine(versioning_manager) -> AsyncGenerator[AsyncEngine, None]:
    """Test database engine fixture."""
    engine = create_async_engine(str(settings.TEST_DATABASE_URL), echo=False)

    configure_mappers()

    async with engine.begin() as connection:
        await connection.run_sync(versioning_manager.transaction_cls.__table__.create)
        await connection.run_sync(versioning_manager.activity_cls.__table__.create)
        await connection.run_sync(SQLModel.metadata.create_all)

        # add 'postgresql-audit' functions and operators
        for table in versioning_manager.table_listeners:
            for _trig, event in versioning_manager.table_listeners[table]:
                if isinstance(event, sa.schema.DDL):
                    await connection.execute(event)
                else:
                    event("dummy_table_argument", connection)

        versioned_model_classes = [
            User,
            Group,
            core.Amenageur,
            core.Operateur,
            core.Enseigne,
            core.Localisation,
            core.Station,
            core.PointDeCharge,
            core.Session,
        ]
        for cls in versioned_model_classes:
            await connection.execute(
                versioning_manager.build_audit_table_query(
                    table=cls.__table__,
                    exclude_columns=cls.__versioned__.get("exclude"),
                )
            )

    # Pretend to have all migrations applied
    alembic_cfg = Config(settings.ALEMBIC_CFG_PATH)
    command.stamp(alembic_cfg, "head")

    yield engine
    SQLModel.metadata.drop_all(engine)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Test session fixture."""
    # Setup
    #
    # Connect to the database and create a non-ORM transaction. Our connection
    # is bound to the test session.
    connection = await db_engine.connect()
    transaction = await connection.begin()
    async with AsyncSession(bind=connection) as session:
        yield session

    # Teardown
    #
    # Rollback everything that happened with the Session above (including
    # explicit commits).
    await transaction.rollback()
    await connection.close()


@pytest.fixture(autouse=True)
async def override_db_test_session(db_session):
    """Use test database along with a test session by default."""

    async def get_session_override():
        return db_session

    v1.dependency_overrides[get_session] = get_session_override

    yield


@pytest.fixture(autouse=True, scope="session")
async def load_operational_units(db_engine):
    """Load operational units fixture."""
    with AsyncSession(db_engine) as session:
        session.add_all(operational_units)
        await session.commit()
    yield
