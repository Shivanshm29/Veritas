"""
Evidence-Based Claim Verification API Endpoints for Veritas (Phase 4).

Provides endpoints for evaluating factual claims against evidence, classifying stances,
and querying synthesized ClaimAssessment records.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from contracts.schemas.models import (
    ClaimAssessment,
    ClaimVerdict,
    EntityPrefix,
    validate_prefixed_id,
)
from backend.app.core.errors import (
    EmptyTextError,
    InvalidIdentifierError,
    ResourceNotFoundError,
)
from backend.app.core.logging import logger
from backend.app.db.repositories.claim_assessment import ClaimAssessmentRepository
from backend.app.db.session import get_db
from backend.app.schemas.verification import (
    StanceClassificationRequest,
    StanceClassificationResponse,
    VerifyClaimRequest,
    VerifyClaimResponse,
)
from backend.app.services.verification.service import get_verification_service
from backend.app.services.verification.stance_classifier import get_stance_classifier


router = APIRouter(prefix="/verification", tags=["verification"])


@router.post(
    "/verify-claim",
    response_model=VerifyClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify claim against retrieved evidence",
    description=(
        "Assesses factual assertions against retrieved evidence passages, identifies contradictions, "
        "discounts syndicated duplicates, calibrates confidence, and outputs a traceable ClaimAssessment."
    ),
)
async def verify_claim_endpoint(
    payload: VerifyClaimRequest,
    db: Session = Depends(get_db),
) -> VerifyClaimResponse:
    start_time = time.perf_counter()
    service = get_verification_service()

    claim_id = payload.claim_id
    claim_text = payload.claim_text

    if not claim_id and not claim_text:
        raise EmptyTextError("Verification requires either a claim_id or claim_text.")

    if claim_id:
        try:
            validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
        except ValueError:
            raise InvalidIdentifierError(identifier=claim_id, expected_format="clm_<uuid4>")

        assessment = service.verify_claim_by_id(
            claim_id=claim_id,
            db=db,
            persist=payload.persist,
        )
    else:
        assessment = service.verify_claim_text(
            claim_text=claim_text,
            investigation_id=payload.investigation_id,
            db=db,
            persist=payload.persist,
        )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    audit_notes = []
    if assessment.verdict == ClaimVerdict.CONTRADICTORY_EVIDENCE:
        audit_notes.append("Irreconcilable evidentiary contradiction detected among sources.")
    elif assessment.verdict == ClaimVerdict.INSUFFICIENT_EVIDENCE:
        audit_notes.append("Under epistemic rules, absence of evidence is not equated with falsity.")

    return VerifyClaimResponse(
        assessment=assessment,
        execution_time_ms=elapsed_ms,
        verification_method="veritas-hybrid-verifier-v1.0",
        audit_notes=audit_notes,
    )


@router.post(
    "/stance",
    response_model=StanceClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify evidence stance relative to claim",
    description="Evaluates whether an individual evidence passage supports, contradicts, or is insufficient for a claim.",
)
async def classify_stance_endpoint(
    payload: StanceClassificationRequest,
) -> StanceClassificationResponse:
    classifier = get_stance_classifier()
    res = classifier.classify_stance(
        claim_text=payload.claim_text,
        evidence_text=payload.evidence_text,
    )
    return StanceClassificationResponse(
        stance=res.stance.value if hasattr(res.stance, "value") else str(res.stance),
        confidence=res.confidence,
        rationale=res.rationale,
        key_phrases=res.key_phrases,
        is_calibrated=res.is_calibrated,
    )


@router.get(
    "/assessments/{assessment_id}",
    response_model=ClaimAssessment,
    status_code=status.HTTP_200_OK,
    summary="Retrieve claim assessment by ID",
)
async def get_assessment_by_id(
    assessment_id: str,
    db: Session = Depends(get_db),
) -> ClaimAssessment:
    try:
        validate_prefixed_id(assessment_id, EntityPrefix.CLAIM_ASSESSMENT)
    except ValueError:
        raise InvalidIdentifierError(identifier=assessment_id, expected_format="asm_<uuid4>")

    repo = ClaimAssessmentRepository(db)
    record = repo.get_by_id(assessment_id)
    if not record:
        raise ResourceNotFoundError("ClaimAssessment", assessment_id)
    return record.to_schema()


@router.get(
    "/assessments/claim/{claim_id}",
    response_model=List[ClaimAssessment],
    status_code=status.HTTP_200_OK,
    summary="Retrieve all assessments for a claim",
)
async def get_assessments_for_claim(
    claim_id: str,
    db: Session = Depends(get_db),
) -> List[ClaimAssessment]:
    try:
        validate_prefixed_id(claim_id, EntityPrefix.CLAIM)
    except ValueError:
        raise InvalidIdentifierError(identifier=claim_id, expected_format="clm_<uuid4>")

    repo = ClaimAssessmentRepository(db)
    records = repo.get_by_claim_id(claim_id)
    return [r.to_schema() for r in records]


@router.get(
    "/assessments",
    response_model=List[ClaimAssessment],
    status_code=status.HTTP_200_OK,
    summary="List claim assessments with filters",
)
async def list_assessments(
    investigation_id: Optional[str] = Query(None, description="Filter by investigation ID"),
    claim_id: Optional[str] = Query(None, description="Filter by claim ID"),
    verdict: Optional[str] = Query(None, description="Filter by verdict"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> List[ClaimAssessment]:
    repo = ClaimAssessmentRepository(db)
    records = repo.list(
        investigation_id=investigation_id,
        claim_id=claim_id,
        verdict=verdict,
        limit=limit,
        offset=offset,
    )
    return [r.to_schema() for r in records]
