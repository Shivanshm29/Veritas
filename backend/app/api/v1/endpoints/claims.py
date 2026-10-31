"""
Claim Intelligence & Multilingual NLP API endpoints for Veritas.

Provides endpoints for extracting structured claim candidates from raw text,
extracting claims associated with existing assets, and retrieving persisted claims.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from contracts.schemas.models import Claim, EntityPrefix, validate_prefixed_id
from backend.app.core.errors import InvalidIdentifierError, ResourceNotFoundError
from backend.app.core.logging import logger
from backend.app.db.models.claim import ClaimRecord
from backend.app.db.repositories.asset import AssetRepository
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.session import get_db
from backend.app.schemas.claim import (
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    UnprocessedSegmentSchema,
)
from backend.app.services.nlp.extractor import get_claim_service


router = APIRouter(prefix="/claims", tags=["claims"])


@router.post(
    "/extract",
    response_model=ClaimExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured claims from raw text",
    description="Analyzes supplied text, detects language, normalizes, extracts assessable factual claims, and computes source spans.",
)
async def extract_claims(
    payload: ClaimExtractionRequest,
    db: Session = Depends(get_db),
) -> ClaimExtractionResponse:
    service = get_claim_service()

    batch = service.extract_claims(
        text=payload.text,
        investigation_id=payload.investigation_id,
        source_asset_id=payload.source_asset_id,
        modality_origin=payload.modality_origin,
        source_timecode_start_ms=payload.source_timecode_start_ms,
        source_timecode_end_ms=payload.source_timecode_end_ms,
        speaker_tag=payload.speaker_tag,
    )

    if payload.persist and batch.claims:
        repo = ClaimRepository(db)
        records = [
            ClaimRecord(
                id=c.id,
                investigation_id=c.investigation_id,
                source_asset_id=c.source_asset_id,
                claim_text=c.claim_text,
                modality_origin=c.modality_origin.value if hasattr(c.modality_origin, "value") else str(c.modality_origin),
                extraction_confidence=c.extraction_confidence,
                source_timecode_start_ms=c.source_timecode_start_ms,
                source_timecode_end_ms=c.source_timecode_end_ms,
                source_char_start=c.source_char_start,
                source_char_end=c.source_char_end,
                speaker_tag=c.speaker_tag,
                claim_entities=c.claim_entities,
                category=(c.category.value if hasattr(c.category, "value") else str(c.category)) if c.category else None,
                status=c.status.value if hasattr(c.status, "value") else str(c.status),
                language=c.language,
                extraction_method=c.extraction_method,
                created_at=c.created_at,
            )
            for c in batch.claims
        ]
        repo.create_batch(records)
        logger.info(f"Persisted {len(records)} extracted claims to database.")

    unprocessed_schemas = [
        UnprocessedSegmentSchema(
            text=u.text,
            reason=u.reason,
            char_start=u.char_start,
            char_end=u.char_end,
        )
        for u in batch.unprocessed_segments
    ]

    return ClaimExtractionResponse(
        original_text=batch.original_text,
        normalized_text=batch.normalized_text,
        detected_language=batch.detected_language,
        language_confidence=batch.language_confidence,
        claims=batch.claims,
        unprocessed_segments=unprocessed_schemas,
        total_claims=batch.total_claims,
        execution_time_ms=batch.execution_time_ms,
        extraction_method=batch.extraction_method,
        warnings=batch.warnings,
    )


@router.post(
    "/extract-from-asset/{asset_id}",
    response_model=ClaimExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract claims associated with an evidence asset",
    description="Validates evidence asset existence and extracts claims linked to the source asset.",
)
async def extract_claims_from_asset(
    asset_id: str,
    payload: ClaimExtractionRequest,
    db: Session = Depends(get_db),
) -> ClaimExtractionResponse:
    # 1. Validate identifier syntax
    try:
        validate_prefixed_id(asset_id, EntityPrefix.EVIDENCE_ASSET)
    except ValueError:
        raise InvalidIdentifierError(identifier=asset_id, expected_format="ast_<uuid4>")

    # 2. Check asset existence
    asset_repo = AssetRepository(db)
    asset = asset_repo.get_by_id(asset_id)
    if not asset:
        raise ResourceNotFoundError("EvidenceAsset", asset_id)

    # 3. Associate with asset ID
    payload.source_asset_id = asset_id
    if not payload.investigation_id:
        payload.investigation_id = asset.investigation_id

    return await extract_claims(payload, db)


@router.get(
    "/{claim_id}",
    response_model=Claim,
    status_code=status.HTTP_200_OK,
    summary="Retrieve claim metadata",
    description="Fetches a persisted claim by its unique prefixed identifier (clm_<uuid4>).",
)
async def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
) -> Claim:
    # 1. Validate identifier syntax
    try:
        validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
    except ValueError:
        raise InvalidIdentifierError(identifier=claim_id, expected_format="clm_<uuid4>")

    # 2. Query repository
    repo = ClaimRepository(db)
    record = repo.get_by_id(claim_id)
    if not record:
        raise ResourceNotFoundError("Claim", claim_id)

    return record.to_schema()


@router.get(
    "",
    response_model=List[Claim],
    status_code=status.HTTP_200_OK,
    summary="List claims with filtering",
    description="Lists claims filtered by investigation_id, source_asset_id, category, or status.",
)
async def list_claims(
    investigation_id: Optional[str] = Query(None, description="Filter by investigation ID"),
    source_asset_id: Optional[str] = Query(None, description="Filter by source asset ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[Claim]:
    repo = ClaimRepository(db)

    if investigation_id:
        try:
            validate_prefixed_id(investigation_id, EntityPrefix.INVESTIGATION)
        except ValueError:
            raise InvalidIdentifierError(identifier=investigation_id, expected_format="inv_<uuid4>")
        records = repo.list_by_investigation(
            investigation_id=investigation_id,
            category=category,
            status=status,
            limit=limit,
            offset=offset,
        )
        return [r.to_schema() for r in records]

    if source_asset_id:
        try:
            validate_prefixed_id(source_asset_id, EntityPrefix.EVIDENCE_ASSET)
        except ValueError:
            raise InvalidIdentifierError(identifier=source_asset_id, expected_format="ast_<uuid4>")
        records = repo.list_by_asset(source_asset_id=source_asset_id, limit=limit, offset=offset)
        return [r.to_schema() for r in records]

    # If neither investigation_id nor source_asset_id is provided, query all with limits
    records = db.query(ClaimRecord).order_by(ClaimRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [r.to_schema() for r in records]
