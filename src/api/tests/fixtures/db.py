"""Fixtures for QualiCharge API database."""

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from postgresql_audit.base import VersioningManager
from sqlalchemy.orm import configure_mappers, declarative_base
from sqlmodel import Session, SQLModel, create_engine

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
def db_engine(versioning_manager):
    """Test database engine fixture."""
    engine = create_engine(str(settings.TEST_DATABASE_URL), echo=False)

    configure_mappers()

    with engine.begin() as connection:
        versioning_manager.transaction_cls.__table__.create(connection)
        versioning_manager.activity_cls.__table__.create(connection)
        SQLModel.metadata.create_all(connection)

        # add 'postgresql-audit' functions and operators
        for table in versioning_manager.table_listeners:
            for _trig, event in versioning_manager.table_listeners[table]:
                if isinstance(event, sa.schema.DDL):
                    connection.execute(event)
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
            connection.execute(
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
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Test session fixture."""
    # Setup
    #
    # Connect to the database and create a non-ORM transaction. Our connection
    # is bound to the test session.
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    # Teardown
    #
    # Rollback everything that happened with the Session above (including
    # explicit commits).
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def override_db_test_session(db_session):
    """Use test database along with a test session by default."""

    def get_session_override():
        return db_session

    v1.dependency_overrides[get_session] = get_session_override

    yield


@pytest.fixture(autouse=True, scope="session")
def load_operational_units(db_engine):
    """Load operational units fixture."""
    with Session(db_engine) as session:
        session.add_all(operational_units)
        session.commit()
    yield
