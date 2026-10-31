"""
Pydantic API request and response schemas for Claim Extraction in Veritas.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from contracts.schemas.models import (
    Claim,
    ClaimCategory,
    ClaimModalityOrigin,
    EntityPrefix,
    validate_prefixed_id,
)


class ClaimExtractionRequest(BaseModel):
    """Payload for submitting text to the claim extraction pipeline."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Source textual assertion or transcript to analyze (max 50,000 characters)",
    )
    investigation_id: Optional[str] = Field(
        None,
        description="Associated investigation ID (inv_<uuid4>)",
    )
    source_asset_id: Optional[str] = Field(
        None,
        description="Optional source evidence asset ID (ast_<uuid4>)",
    )
    modality_origin: Optional[ClaimModalityOrigin] = Field(
        ClaimModalityOrigin.USER_PROMPT,
        description="Origin modality of the source text",
    )
    source_timecode_start_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Optional start timecode in milliseconds if text originates from ASR",
    )
    source_timecode_end_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Optional end timecode in milliseconds if text originates from ASR",
    )
    speaker_tag: Optional[str] = Field(
        None,
        description="Speaker identity tag if attributed",
    )
    persist: bool = Field(
        False,
        description="If True, persists extracted claims directly into the database",
    )

    @field_validator("investigation_id")
    @classmethod
    def validate_inv_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)
        return v

    @field_validator("source_asset_id")
    @classmethod
    def validate_asset_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ASSET)
        return v


class UnprocessedSegmentSchema(BaseModel):
    """Represents a skipped non-factual utterance, opinion, question, or fragment."""
    text: str
    reason: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class ClaimExtractionResponse(BaseModel):
    """Structured response from the claim extraction pipeline."""
    original_text: str
    normalized_text: str
    detected_language: str
    language_confidence: float
    claims: List[Claim]
    unprocessed_segments: List[UnprocessedSegmentSchema]
    total_claims: int
    execution_time_ms: int
    extraction_method: str
    warnings: List[str] = Field(default_factory=list)
