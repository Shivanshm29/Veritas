"""
Pydantic API request and response schemas for Veritas Evidence Retrieval.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from contracts.schemas.models import EvidenceItem, SourceDocument


class EvidenceRetrievalRequest(BaseModel):
    """Request payload to retrieve source intelligence and evidence for a query or claim."""
    query_text: Optional[str] = Field(
        None,
        description="Text statement, factual assertion, or question to retrieve evidence for.",
        json_schema_extra={"example": "The Federal Reserve raised interest rates by 0.5% in September 2026."},
    )
    claim_id: Optional[str] = Field(
        None,
        description="Optional canonical claim ID (clm_<uuid4>) linking retrieved evidence.",
        json_schema_extra={"example": "clm_12345678-1234-4234-8234-123456789abc"},
    )
    entities: Optional[List[str]] = Field(
        None,
        description="Optional list of named entities, numerical anchors, or organizations to boost in search.",
        json_schema_extra={"example": ["Federal Reserve", "0.5%", "September 2026"]},
    )
    language: Optional[str] = Field(
        None,
        description="Optional ISO 639-1 language code (e.g. 'en', 'hi', 'es').",
        json_schema_extra={"example": "en"},
    )
    max_results: int = Field(
        10,
        ge=1,
        le=50,
        description="Maximum number of source documents to retrieve.",
    )
    domain_filters: Optional[List[str]] = Field(
        None,
        description="Optional list of domains to filter results by.",
    )
    persist: bool = Field(
        False,
        description="If True, persists retrieved SourceDocument and EvidenceItem records to database.",
    )


class EvidenceRetrievalResponse(BaseModel):
    """Structured response containing retrieved source documents and evidence items."""
    query_text: str
    claim_id: Optional[str] = None
    source_documents: List[SourceDocument]
    evidence_items: List[EvidenceItem]
    total_sources: int
    total_evidence_items: int
    duplicates_detected: int
    execution_time_ms: int
    provider_status: str
    warnings: List[str] = Field(default_factory=list)
