"""
Integration tests for Evidence Retrieval pipeline and database persistence (Phase 3).
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session

from backend.app.db.base import Base
import backend.app.db.models  # noqa: F401
from backend.app.db.models.claim import ClaimRecord
from backend.app.db.models.evidence_item import EvidenceItemRecord
from backend.app.db.models.source_document import SourceDocumentRecord
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.repositories.evidence_item import EvidenceItemRepository
from backend.app.db.repositories.source_document import SourceDocumentRepository
from backend.app.db.session import engine, SessionLocal
from backend.app.services.retrieval.service import EvidenceRetrievalService
from contracts.schemas.models import (
    Claim,
    ClaimCategory,
    ClaimModalityOrigin,
    ClaimStatus,
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


def test_evidence_retrieval_and_db_persistence(db_session: Session):
    claim_id = "clm_12345678-1234-4234-8234-123456789abc"
    inv_id = "inv_12345678-1234-4234-8234-123456789abc"

    # 1. Setup claim record in DB
    claim_repo = ClaimRepository(db_session)
    claim_record = ClaimRecord(
        id=claim_id,
        investigation_id=inv_id,
        claim_text="The Federal Reserve raised interest rates by 0.5% in September 2026.",
        modality_origin="USER_PROMPT",
        extraction_confidence=0.95,
        status="EXTRACTED",
        category="FINANCIAL",
        created_at=datetime.now(timezone.utc),
    )
    claim_repo.create(claim_record)

    claim_model = Claim(
        id=claim_id,
        investigation_id=inv_id,
        claim_text=claim_record.claim_text,
        modality_origin=ClaimModalityOrigin.USER_PROMPT,
        extraction_confidence=0.95,
        status=ClaimStatus.EXTRACTED,
        category=ClaimCategory.FINANCIAL,
        created_at=claim_record.created_at,
    )

    # 2. Run retrieval service
    service = EvidenceRetrievalService()
    batch = service.retrieve_for_claim(claim_model, max_results=5)

    assert batch.total_sources > 0
    assert batch.total_evidence_items > 0
    assert len(batch.source_documents) > 0
    assert len(batch.evidence_items) > 0

    # 3. Persist Source Documents and Evidence Items
    source_repo = SourceDocumentRepository(db_session)
    evidence_repo = EvidenceItemRepository(db_session)

    persisted_source_ids = []
    for doc in batch.source_documents:
        record = SourceDocumentRecord(
            id=doc.id,
            url=str(doc.url),
            domain=doc.domain,
            title=doc.title,
            author=doc.author,
            publisher=doc.publisher,
            published_date=doc.published_date,
            content_snippet=doc.content_snippet,
            content_sha256=doc.content_sha256,
            source_reliability_score=doc.source_reliability_score,
            is_simulated=doc.is_simulated,
            retrieval_timestamp=doc.retrieval_timestamp,
        )
        source_repo.create(record)
        persisted_source_ids.append(doc.id)

    persisted_evidence_ids = []
    for item in batch.evidence_items:
        rec = EvidenceItemRecord(
            id=item.id,
            claim_id=item.claim_id,
            source_document_id=item.source_document_id,
            evidence_text=item.evidence_text,
            relevance_score=item.relevance_score,
            stance=item.stance.value if hasattr(item.stance, "value") else str(item.stance),
            paragraph_index=item.paragraph_index,
            page_number=item.page_number,
            retrieval_method=item.retrieval_method.value if hasattr(item.retrieval_method, "value") else str(item.retrieval_method),
            created_at=item.created_at,
        )
        evidence_repo.create(rec)
        persisted_evidence_ids.append(item.id)

    # 4. Verify querying Source Documents
    first_doc_id = persisted_source_ids[0]
    fetched_doc = source_repo.get_by_id(first_doc_id)
    assert fetched_doc is not None
    assert fetched_doc.id == first_doc_id
    assert fetched_doc.content_sha256 is not None
    assert len(fetched_doc.content_sha256) == 64

    # Query by SHA256
    fetched_by_hash = source_repo.get_by_hash(fetched_doc.content_sha256)
    assert fetched_by_hash is not None
    assert fetched_by_hash.id == first_doc_id

    # List by domain
    domain_docs = source_repo.list_by_domain(fetched_doc.domain)
    assert len(domain_docs) >= 1

    # 5. Verify querying Evidence Items
    claim_items = evidence_repo.list_by_claim(claim_id)
    assert len(claim_items) == len(persisted_evidence_ids)

    # Filter by relevance
    high_rel_items = evidence_repo.list_by_claim(claim_id, min_relevance=0.4)
    for item in high_rel_items:
        assert item.relevance_score >= 0.4

    # List by source document
    doc_items = evidence_repo.list_by_source_document(first_doc_id)
    assert len(doc_items) >= 1
    assert all(i.source_document_id == first_doc_id for i in doc_items)

    # 6. Verify Deletion
    deleted = evidence_repo.delete(persisted_evidence_ids[0])
    assert deleted is True
    assert evidence_repo.get_by_id(persisted_evidence_ids[0]) is None


def test_atomic_persistence_rollback_on_evidence_failure(db_session: Session):
    source_repo = SourceDocumentRepository(db_session)
    evidence_repo = EvidenceItemRepository(db_session)

    doc_id = "doc_99999999-9999-4999-8999-999999999999"
    evi_id = "evi_99999999-9999-4999-8999-999999999999"

    doc_record = SourceDocumentRecord(
        id=doc_id,
        url="https://example.gov/doc",
        domain="example.gov",
        title="Test Document for Rollback",
        content_snippet="Test content snippet for transactional atomicity.",
        content_sha256="a" * 64,
        retrieval_timestamp=datetime.now(timezone.utc),
        is_simulated=True,
    )

    # Staged batch insertion simulation: source document valid, but evidence item invalid
    try:
        source_repo.create_batch([doc_record], commit=False)

        # Force a failure during evidence insertion (evidence_text violates NOT NULL constraint)
        bad_evi = EvidenceItemRecord(
            id=evi_id,
            claim_id="clm_12345678-1234-4234-8234-123456789abc",
            source_document_id=doc_id,
            evidence_text=None,
            relevance_score=0.9,
        )
        evidence_repo.create_batch([bad_evi], commit=False)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Verify atomic rollback: the source document must NOT exist in the database
    persisted_doc = source_repo.get_by_id(doc_id)
    assert persisted_doc is None, "Source document was partially committed despite evidence insertion failure!"
