"""
Integration tests verifying Claim extraction with database persistence and query filtering.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from contracts.schemas.models import ClaimCategory, ClaimModalityOrigin, ClaimStatus
from backend.app.db.base import Base
from backend.app.db.models.claim import ClaimRecord
import backend.app.db.models  # noqa: F401
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.session import engine, SessionLocal
from backend.app.services.nlp.extractor import ClaimExtractionService


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_claim_pipeline_persists_to_db(db_session: Session):
    service = ClaimExtractionService()
    text = "The Ministry of Finance announced an emergency stimulus package of $2 billion on October 20, 2026."

    inv_id = "inv_12345678-1234-4234-8234-123456789abc"
    batch = service.extract_claims(text, investigation_id=inv_id)
    assert batch.total_claims == 1
    claim = batch.claims[0]

    repo = ClaimRepository(db_session)
    record = ClaimRecord(
        id=claim.id,
        investigation_id=claim.investigation_id,
        source_asset_id=claim.source_asset_id,
        claim_text=claim.claim_text,
        modality_origin=claim.modality_origin.value if hasattr(claim.modality_origin, "value") else str(claim.modality_origin),
        extraction_confidence=claim.extraction_confidence,
        source_timecode_start_ms=claim.source_timecode_start_ms,
        source_timecode_end_ms=claim.source_timecode_end_ms,
        source_char_start=claim.source_char_start,
        source_char_end=claim.source_char_end,
        speaker_tag=claim.speaker_tag,
        claim_entities=claim.claim_entities,
        category=(claim.category.value if hasattr(claim.category, "value") else str(claim.category)) if claim.category else None,
        status=claim.status.value if hasattr(claim.status, "value") else str(claim.status),
        language=claim.language,
        extraction_method=claim.extraction_method,
        created_at=claim.created_at,
    )
    repo.create(record)

    # Query back by ID
    persisted = repo.get_by_id(claim.id)
    assert persisted is not None
    assert persisted.id == claim.id
    assert persisted.investigation_id == inv_id
    assert persisted.claim_text == claim.claim_text
    assert persisted.source_char_start is not None
    assert persisted.source_char_end is not None

    # Verify to_schema
    schema_claim = persisted.to_schema()
    assert schema_claim.id == claim.id

    # Query by investigation
    inv_claims = repo.list_by_investigation(inv_id)
    assert any(c.id == claim.id for c in inv_claims)

    # Delete
    deleted = repo.delete(claim.id)
    assert deleted is True
    assert repo.get_by_id(claim.id) is None
