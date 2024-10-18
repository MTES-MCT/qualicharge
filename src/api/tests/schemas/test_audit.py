"""QualiCharge auditable schemas tests."""

from sqlalchemy import func
from sqlmodel import select

from qualicharge.auth.factories import UserFactory
from qualicharge.factories.static import OperateurFactory
from qualicharge.schemas.audit import Audit
from qualicharge.schemas.core import Operateur


def test_auditable_schema_changes(db_session):
    """Test an updated schema instance creates a new Audit entry."""
    OperateurFactory.__session__ = db_session
    UserFactory.__session__ = db_session

    user = UserFactory.create_sync()

    # Check initial database state
    assert db_session.exec(select(func.count(Operateur.id))).one() == 0
    assert db_session.exec(select(func.count(Audit.id))).one() == 0

    # Persist an operateur without creator or updator
    operateur = OperateurFactory.create_sync(
        nom_operateur="Doe inc.",
        contact_operateur="john@doe.com",
        telephone_operateur="+33144276350",
    )

    # Check database state
    assert db_session.exec(select(func.count(Operateur.id))).one() == 1
    assert db_session.exec(select(func.count(Audit.id))).one() == 0

    # Update operateur without updator
    operateur.contact_operateur = "jane@doe.com"
    operateur.telephone_operateur = "+33144276351"
    db_session.add(operateur)

    # Check database state
    assert db_session.exec(select(func.count(Operateur.id))).one() == 1
    assert db_session.exec(select(func.count(Audit.id))).one() == 0

    # Now update operateur with an updator
    operateur.updated_by_id = user.id
    operateur.contact_operateur = "janine@doe.com"
    operateur.telephone_operateur = "+33144276352"
    db_session.add(operateur)

    # Check database state
    assert db_session.exec(select(func.count(Operateur.id))).one() == 1
    assert db_session.exec(select(func.count(Audit.id))).one() == 1
    audit = db_session.exec(select(Audit)).first()
    assert audit.table == "operateur"
    assert audit.author_id == user.id
    assert audit.target_id == operateur.id
    assert audit.updated_at == operateur.updated_at
    assert audit.changes == {
        "updated_by_id": ["None", str(user.id)],
        "contact_operateur": ["jane@doe.com", "janine@doe.com"],
        "telephone_operateur": ["tel:+33-1-44-27-63-51", "tel:+33-1-44-27-63-52"],
    }

    # Perform new updates
    operateur.contact_operateur = "janot@doe.com"
    operateur.telephone_operateur = "+33144276353"
    db_session.add(operateur)

    # Check database state
    expected_audits = 2
    assert db_session.exec(select(func.count(Operateur.id))).one() == 1
    assert db_session.exec(select(func.count(Audit.id))).one() == expected_audits
    audit = db_session.exec(select(Audit).order_by(Audit.updated_at.desc())).first()
    assert audit.table == "operateur"
    assert audit.author_id == user.id
    assert audit.target_id == operateur.id
    assert audit.updated_at == operateur.updated_at
    assert audit.changes == {
        "contact_operateur": ["janine@doe.com", "janot@doe.com"],
        "telephone_operateur": ["tel:+33-1-44-27-63-52", "tel:+33-1-44-27-63-53"],
    }


def test_auditable_schema_audits_dynamic_fk(db_session):
    """Test auditable schema dynamic audits foreign key."""
    OperateurFactory.__session__ = db_session
    UserFactory.__session__ = db_session

    user = UserFactory.create_sync()
    operateur = OperateurFactory.create_sync(
        nom_operateur="Doe inc.",
        contact_operateur="john@doe.com",
        telephone_operateur="+33144276350",
        updated_by_id=user.id,
    )

    assert len(operateur.audits) == 0

    # Update operateur
    operateur.contact_operateur = "janine@doe.com"
    operateur.telephone_operateur = "+33144276352"
    db_session.add(operateur)
    db_session.commit()
    db_session.refresh(operateur)

    # Test audits dymanic generic FK
    assert len(operateur.audits) == 1
    assert operateur.audits[0].table == "operateur"
    assert operateur.audits[0].author_id == user.id
    assert operateur.audits[0].target_id == operateur.id
    assert operateur.audits[0].updated_at == operateur.updated_at
    assert operateur.audits[0].changes == {
        "contact_operateur": ["john@doe.com", "janine@doe.com"],
        "telephone_operateur": ["tel:+33-1-44-27-63-50", "tel:+33-1-44-27-63-52"],
    }

    # Update operateur once again
    operateur.contact_operateur = "janot@doe.com"
    operateur.telephone_operateur = "+33144276353"
    db_session.add(operateur)
    db_session.commit()
    db_session.refresh(operateur)

    # Test audits dymanic generic FK
    expected_audits = 2
    assert len(operateur.audits) == expected_audits
    assert operateur.audits[1].table == "operateur"
    assert operateur.audits[1].author_id == user.id
    assert operateur.audits[1].target_id == operateur.id
    assert operateur.audits[1].updated_at == operateur.updated_at
    assert operateur.audits[1].changes == {
        "contact_operateur": ["janine@doe.com", "janot@doe.com"],
        "telephone_operateur": ["tel:+33-1-44-27-63-52", "tel:+33-1-44-27-63-53"],
    }
