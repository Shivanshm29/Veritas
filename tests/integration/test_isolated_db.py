"""
Integration tests for SQLAlchemy session handling and transaction rollback against an isolated database.
"""

from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import pytest

OrmTestBase = declarative_base()


class DummyInvestigationRecord(OrmTestBase):
    __tablename__ = "dummy_investigations"
    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)


def test_isolated_database_crud():
    """Verifies table creation, insertion, and query in isolated memory DB."""
    engine = create_engine("sqlite:///:memory:")
    OrmTestBase.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    db = TestingSession()
    try:
        record = DummyInvestigationRecord(
            id="inv_test_001",
            title="Isolated DB Test",
            status="CREATED",
        )
        db.add(record)
        db.commit()

        queried = db.query(DummyInvestigationRecord).filter_by(id="inv_test_001").first()
        assert queried is not None
        assert queried.title == "Isolated DB Test"
    finally:
        db.close()


def test_isolated_database_rollback_on_error():
    """Verifies that an exception rolls back transaction leaving no dirty state."""
    engine = create_engine("sqlite:///:memory:")
    OrmTestBase.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    db = TestingSession()
    try:
        record = DummyInvestigationRecord(
            id="inv_test_rollback",
            title="Rollback Test",
            status="CREATED",
        )
        db.add(record)
        db.flush()

        # Simulate failure
        db.rollback()

        queried = db.query(DummyInvestigationRecord).filter_by(id="inv_test_rollback").first()
        assert queried is None
    finally:
        db.close()
