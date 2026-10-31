"""
Integration tests for Evidence Verification pipeline and database persistence (Phase 4).
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from backend.app.db.base import Base
import backend.app.db.models  # noqa: F401
from backend.app.db.models.claim import ClaimRecord
from backend.app.db.models.claim_assessment import ClaimAssessmentRecord
from backend.app.db.models.evidence_item import EvidenceItemRecord
from backend.app.db.models.source_document import SourceDocumentRecord
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.repositories.claim_assessment import ClaimAssessmentRepository
from backend.app.db.repositories.evidence_item import EvidenceItemRepository
from backend.app.db.repositories.source_document import SourceDocumentRepository
from backend.app.db.session import engine, SessionLocal
from backend.app.services.verification.service import VerificationService
from contracts.schemas.models import (
    ClaimAssessment,
    ClaimStatus,
    ClaimVerdict,
    EvidenceStance,
)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_verification_pipeline_db_lifecycle(db_session: Session):
    inv_id = f"inv_{uuid4()}"
    claim_id = f"clm_{uuid4()}"
    doc_id = f"doc_{uuid4()}"
    evi_id = f"evi_{uuid4()}"

    # 1. Setup claim record
    claim_repo = ClaimRepository(db_session)
    claim_record = ClaimRecord(
        id=claim_id,
        investigation_id=inv_id,
        claim_text="The central bank authorized emergency liquidity funding of fifty billion euros.",
        modality_origin="USER_PROMPT",
        extraction_confidence=0.95,
        status=ClaimStatus.EXTRACTED.value,
        created_at=datetime.now(timezone.utc),
    )
    claim_repo.create(claim_record)

    # 2. Setup source document and evidence item in DB
    doc_repo = SourceDocumentRepository(db_session)
    doc_record = SourceDocumentRecord(
        id=doc_id,
        title="Central Bank Policy Bulletin",
        url="https://ecb.europa.eu/bulletin/2026",
        domain="ecb.europa.eu",
        retrieval_timestamp=datetime.now(timezone.utc),
        content_snippet="Central bank confirmed emergency liquidity facility.",
        content_sha256="0" * 64,
        source_reliability_score=0.95,
        is_simulated=True,
    )
    doc_repo.create(doc_record)

    evi_repo = EvidenceItemRepository(db_session)
    evi_record = EvidenceItemRecord(
        id=evi_id,
        claim_id=claim_id,
        source_document_id=doc_id,
        evidence_text="The central bank officially confirmed authorization of an emergency liquidity facility of fifty billion euros.",
        stance=EvidenceStance.SUPPORTS.value,
        relevance_score=0.95,
        created_at=datetime.now(timezone.utc),
    )
    evi_repo.create(evi_record)

    # 3. Run Verification Service
    verifier = VerificationService()
    assessment: ClaimAssessment = verifier.verify_claim_by_id(
        claim_id=claim_id,
        db=db_session,
        persist=True,
    )

    assert assessment.verdict == ClaimVerdict.SUPPORTED
    assert assessment.confidence_score >= 0.70
    assert evi_id in assessment.cited_evidence_ids

    # 4. Verify DB persistence and claim status update
    asm_repo = ClaimAssessmentRepository(db_session)
    persisted_asm = asm_repo.get_by_id(assessment.id)
    assert persisted_asm is not None
    assert persisted_asm.verdict == ClaimVerdict.SUPPORTED.value
    assert persisted_asm.claim_id == claim_id

    # Verify claim status was updated to VERIFIED
    updated_claim = claim_repo.get_by_id(claim_id)
    assert updated_claim.status == ClaimStatus.VERIFIED.value


def test_verification_db_missing_evidence_unverifiable(db_session: Session):
    inv_id = f"inv_{uuid4()}"
    claim_id = f"clm_{uuid4()}"

    # Setup claim with no evidence
    claim_repo = ClaimRepository(db_session)
    claim_record = ClaimRecord(
        id=claim_id,
        investigation_id=inv_id,
        claim_text="An undiscovered Roman amphora was unearthed in rural Antarctica.",
        modality_origin="USER_PROMPT",
        extraction_confidence=0.95,
        status=ClaimStatus.EXTRACTED.value,
        created_at=datetime.now(timezone.utc),
    )
    claim_repo.create(claim_record)

    verifier = VerificationService()
    assessment = verifier.verify_claim_by_id(
        claim_id=claim_id,
        db=db_session,
        persist=True,
    )

    # Must be INSUFFICIENT_EVIDENCE under missing evidence rule
    assert assessment.verdict == ClaimVerdict.INSUFFICIENT_EVIDENCE
    assert assessment.confidence_score <= 0.35

    # Claim status should transition to UNVERIFIABLE
    updated_claim = claim_repo.get_by_id(claim_id)
    assert updated_claim.status == ClaimStatus.UNVERIFIABLE.value
