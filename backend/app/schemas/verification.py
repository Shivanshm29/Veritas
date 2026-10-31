"""
Pydantic API schemas for Phase 4: Evidence-Based Claim Verification.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from contracts.schemas.models import ClaimAssessment, EvidenceStance


class VerifyClaimRequest(BaseModel):
    """Request payload for verifying a claim."""
    claim_id: Optional[str] = Field(
        None,
        description="ID of existing persisted claim (format: clm_<uuid4>). If omitted, claim_text is required.",
    )
    claim_text: Optional[str] = Field(
        None,
        description="Raw factual claim text to verify if claim_id is not provided.",
    )
    investigation_id: Optional[str] = Field(
        None,
        description="Investigation ID (format: inv_<uuid4>). Auto-generated if omitted.",
    )
    persist: bool = Field(
        default=True,
        description="Whether to persist the generated assessment and update claim status in database.",
    )


class VerifyClaimResponse(BaseModel):
    """Response payload containing synthesized ClaimAssessment and audit metrics."""
    assessment: ClaimAssessment
    execution_time_ms: int
    verification_method: str = "veritas-hybrid-verifier-v1.0"
    audit_notes: List[str] = Field(default_factory=list)


class StanceClassificationRequest(BaseModel):
    """Request payload for evaluating the stance of an individual evidence passage."""
    claim_text: str = Field(..., min_length=3, description="Target claim text.")
    evidence_text: str = Field(..., min_length=3, description="Passage or snippet to evaluate against claim.")


class StanceClassificationResponse(BaseModel):
    """Response payload for stance evaluation."""
    stance: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    key_phrases: List[str] = Field(default_factory=list)
    is_calibrated: bool = False
    epistemic_disclaimer: str = (
        "Stance confidence reflects linguistic corroboration intensity, "
        "not an uncalibrated Bayesian probability of real-world truth."
    )
