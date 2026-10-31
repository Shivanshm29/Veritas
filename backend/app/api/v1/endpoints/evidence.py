"""
Source Intelligence & Evidence Retrieval API endpoints for Veritas Phase 3.

Provides endpoints for querying external and archived sources, extracting relevant
evidentiary passages, scoring source reliability, and linking evidence items to claims.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.core.errors import (
    EmptyTextError,
    InvalidIdentifierError,
    ResourceNotFoundError,
)
from backend.app.core.logging import logger
from backend.app.db.models.evidence_item import EvidenceItemRecord
from backend.app.db.models.source_document import SourceDocumentRecord
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.repositories.evidence_item import EvidenceItemRepository
from backend.app.db.repositories.source_document import SourceDocumentRepository
from backend.app.db.session import get_db
from backend.app.schemas.evidence import (
    EvidenceRetrievalRequest,
    EvidenceRetrievalResponse,
)
from backend.app.services.retrieval.service import get_retrieval_service
from contracts.schemas.models import (
    EntityPrefix,
    EvidenceItem,
    SourceDocument,
    validate_prefixed_id,
)

router = APIRouter(prefix="/evidence", tags=["Evidence Retrieval"])


@router.post(
    "/retrieve",
    response_model=EvidenceRetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve source documents and evidence items",
    description="Queries indexed and simulated sources, extracts relevant passages, evaluates source credibility, and deduplicates coverage.",
)
async def retrieve_evidence(
    payload: EvidenceRetrievalRequest,
    db: Session = Depends(get_db),
) -> EvidenceRetrievalResponse:
    service = get_retrieval_service()

    target_query = payload.query_text
    claim_id = payload.claim_id

    # If claim_id is provided, validate identifier format
    if claim_id:
        try:
            validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
        except ValueError:
            raise InvalidIdentifierError(identifier=claim_id, expected_format="clm_<uuid4>")

        # If query_text is omitted, load claim from database
        if not target_query:
            claim_repo = ClaimRepository(db)
            claim_record = claim_repo.get_by_id(claim_id)
            if not claim_record:
                raise ResourceNotFoundError("Claim", claim_id)
            target_query = claim_record.claim_text
            if not payload.entities and claim_record.claim_entities:
                payload.entities = claim_record.claim_entities

    if not target_query or not target_query.strip():
        raise EmptyTextError("Retrieval requires either query_text or a valid claim_id.")

    batch = service.retrieve_for_text(
        query_text=target_query,
        claim_id=claim_id,
        entities=payload.entities,
        language=payload.language,
        max_results=payload.max_results,
        domain_filters=payload.domain_filters,
    )

    # Optional database persistence
    if payload.persist and batch.source_documents:
        doc_repo = SourceDocumentRepository(db)
        evi_repo = EvidenceItemRepository(db)

        doc_records = [
            SourceDocumentRecord(
                id=doc.id,
                title=doc.title,
                url=doc.url,
                domain=doc.domain,
                author=doc.author,
                publisher=doc.publisher,
                published_date=doc.published_date,
                retrieval_timestamp=doc.retrieval_timestamp,
                content_snippet=doc.content_snippet,
                content_sha256=doc.content_sha256,
                source_reliability_score=doc.source_reliability_score,
                full_text_storage_uri=doc.full_text_storage_uri,
                is_simulated=doc.is_simulated,
            )
            for doc in batch.source_documents
        ]

        evi_records = [
            EvidenceItemRecord(
                id=evi.id,
                claim_id=evi.claim_id,
                source_document_id=evi.source_document_id,
                evidence_text=evi.evidence_text,
                stance=evi.stance.value if hasattr(evi.stance, "value") else str(evi.stance),
                relevance_score=evi.relevance_score,
                page_number=evi.page_number,
                paragraph_index=evi.paragraph_index,
                retrieval_method=evi.retrieval_method.value if evi.retrieval_method and hasattr(evi.retrieval_method, "value") else (str(evi.retrieval_method) if evi.retrieval_method else None),
                created_at=evi.created_at,
            )
            for evi in batch.evidence_items
        ]

        try:
            doc_repo.create_batch(doc_records, commit=False)
            evi_repo.create_batch(evi_records, commit=False)
            db.commit()
            for d in doc_records:
                db.refresh(d)
            for e in evi_records:
                db.refresh(e)
            logger.info(
                f"Persisted {len(doc_records)} SourceDocuments and {len(evi_records)} EvidenceItems to database in single atomic transaction."
            )
        except Exception:
            db.rollback()
            raise

    return EvidenceRetrievalResponse(
        query_text=batch.query.raw_query,
        claim_id=claim_id,
        source_documents=batch.source_documents,
        evidence_items=batch.evidence_items,
        total_sources=batch.total_sources,
        total_evidence_items=batch.total_evidence_items,
        duplicates_detected=batch.duplicates_detected,
        execution_time_ms=batch.execution_time_ms,
        provider_status=batch.provider_status,
        warnings=batch.warnings,
    )


@router.post(
    "/retrieve-for-claim/{claim_id}",
    response_model=EvidenceRetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve evidence for an existing persisted claim",
    description="Loads a persisted claim by ID and executes full evidence retrieval and ranking.",
)
async def retrieve_for_claim(
    claim_id: str,
    max_results: int = Query(10, ge=1, le=50),
    persist: bool = Query(True),
    db: Session = Depends(get_db),
) -> EvidenceRetrievalResponse:
    # 1. Validate identifier syntax
    try:
        validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
    except ValueError:
        raise InvalidIdentifierError(identifier=claim_id, expected_format="clm_<uuid4>")

    # 2. Query claim
    claim_repo = ClaimRepository(db)
    claim_record = claim_repo.get_by_id(claim_id)
    if not claim_record:
        raise ResourceNotFoundError("Claim", claim_id)

    payload = EvidenceRetrievalRequest(
        claim_id=claim_id,
        query_text=claim_record.claim_text,
        entities=claim_record.claim_entities,
        language=claim_record.language,
        max_results=max_results,
        persist=persist,
    )
    return await retrieve_evidence(payload, db)


@router.get(
    "/sources/{source_id}",
    response_model=SourceDocument,
    status_code=status.HTTP_200_OK,
    summary="Retrieve source document metadata",
    description="Fetches a persisted SourceDocument by its prefixed identifier (doc_<uuid4>).",
)
async def get_source_document(
    source_id: str,
    db: Session = Depends(get_db),
) -> SourceDocument:
    try:
        validate_prefixed_id(source_id, EntityPrefix.SOURCE_DOCUMENT)
    except ValueError:
        raise InvalidIdentifierError(identifier=source_id, expected_format="doc_<uuid4>")

    repo = SourceDocumentRepository(db)
    record = repo.get_by_id(source_id)
    if not record:
        raise ResourceNotFoundError("SourceDocument", source_id)

    return record.to_schema()


@router.get(
    "/{evidence_id}",
    response_model=EvidenceItem,
    status_code=status.HTTP_200_OK,
    summary="Retrieve evidence item metadata",
    description="Fetches a persisted EvidenceItem by its prefixed identifier (evi_<uuid4>).",
)
async def get_evidence_item(
    evidence_id: str,
    db: Session = Depends(get_db),
) -> EvidenceItem:
    try:
        validate_prefixed_id(evidence_id, EntityPrefix.EVIDENCE_ITEM)
    except ValueError:
        raise InvalidIdentifierError(identifier=evidence_id, expected_format="evi_<uuid4>")

    repo = EvidenceItemRepository(db)
    record = repo.get_by_id(evidence_id)
    if not record:
        raise ResourceNotFoundError("EvidenceItem", evidence_id)

    return record.to_schema()


@router.get(
    "",
    response_model=List[EvidenceItem],
    status_code=status.HTTP_200_OK,
    summary="List evidence items with filtering",
    description="Lists evidence items filtered by claim_id, source_document_id, stance, or minimum relevance.",
)
async def list_evidence_items(
    claim_id: Optional[str] = Query(None, description="Filter by claim ID (clm_...)"),
    source_document_id: Optional[str] = Query(None, description="Filter by source document ID (doc_...)"),
    min_relevance: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum relevance score"),
    stance: Optional[str] = Query(None, description="Filter by stance"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[EvidenceItem]:
    repo = EvidenceItemRepository(db)

    if claim_id:
        try:
            validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
        except ValueError:
            raise InvalidIdentifierError(identifier=claim_id, expected_format="clm_<uuid4>")
        records = repo.list_by_claim(
            claim_id=claim_id,
            min_relevance=min_relevance,
            stance=stance,
            limit=limit,
            offset=offset,
        )
        return [r.to_schema() for r in records]

    if source_document_id:
        try:
            validate_prefixed_id(source_document_id, EntityPrefix.SOURCE_DOCUMENT)
        except ValueError:
            raise InvalidIdentifierError(identifier=source_document_id, expected_format="doc_<uuid4>")
        records = repo.list_by_source_document(
            source_document_id=source_document_id,
            limit=limit,
            offset=offset,
        )
        return [r.to_schema() for r in records]

    records = repo.list_all(
        min_relevance=min_relevance,
        stance=stance,
        limit=limit,
        offset=offset,
    )
    return [r.to_schema() for r in records]

