"""
Pydantic schemas for Module 8: Provenance & Historical Media Matching.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MatchGrade(str, Enum):
    EXACT = "EXACT"                       # Hamming distance 0
    NEAR_DUPLICATE = "NEAR_DUPLICATE"     # Hamming distance 1 - 5 (recompressed, cropped, resized)
    TENTATIVE_SIMILAR = "TENTATIVE_SIMILAR" # Hamming distance 6 - 12 (visual similarity only, unconfirmed)
    UNMATCHED = "UNMATCHED"               # Hamming distance > 12


class MediaFingerprint(BaseModel):
    """Multi-algorithm perceptual fingerprint for media identification."""
    phash: str = Field(..., description="64-bit DCT Perceptual Hash (hex)")
    dhash: str = Field(..., description="64-bit Difference Hash (hex)")
    ahash: str = Field(..., description="64-bit Average Hash (hex)")
    color_fingerprint: str = Field(..., description="Color distribution descriptor (hex)")
    frame_hashes: Optional[List[str]] = Field(default=None, description="Keyframe hashes if video")


class HistoricalMatch(BaseModel):
    """Result of searching the historical reference collection."""
    reference_id: str
    title: str
    source_url: str
    publisher: Optional[str] = None
    original_published_date: Optional[str] = None
    hamming_distance: int = Field(..., ge=0, le=64)
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    match_grade: MatchGrade
    basis: str = Field(..., description="Explanation of why the relationship was inferred")
    is_confirmed_origin: bool = Field(
        ...,
        description="True only if match_grade is EXACT or NEAR_DUPLICATE; avoids treating visual similarity as proof."
    )


class HistoricalMatchResponse(BaseModel):
    """Response returned by POST /api/v1/provenance/match."""
    query_sha256: str
    fingerprint: MediaFingerprint
    total_references_searched: int
    matches_found: int
    matches: List[HistoricalMatch]


class ProvenanceNode(BaseModel):
    id: str
    type: str  # ASSET, CLAIM, SOURCE_DOCUMENT, FORENSIC_FINDING, DERIVATION
    label: str
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProvenanceEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str  # DERIVED_FROM, SHARES_PERCEPTUAL_HASH, DUPLICATE_OF, SUPPORTS, CONTRADICTS
    confidence: float = Field(..., ge=0.0, le=1.0)
    basis: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProvenanceTimelineEntry(BaseModel):
    timestamp: str
    event: str
    entity_id: str
    entity_type: str
    description: str


class ProvenanceGraphResponse(BaseModel):
    """Full visual evidence graph & investigation timeline."""
    investigation_id: str
    is_dag: bool = Field(..., description="True if the provenance graph is a valid cycle-free DAG.")
    cycle_detected: bool = Field(..., description="True if circular derivation was detected.")
    nodes: List[ProvenanceNode]
    edges: List[ProvenanceEdge]
    timeline: List[ProvenanceTimelineEntry]
