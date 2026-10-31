"""
Pydantic schemas for the Video Forensics API.

These define the response shapes for POST /api/v1/video/analyze.
"""

from typing import Any
from pydantic import BaseModel, Field


class VideoForensicFinding(BaseModel):
    """A single forensic detector result for video analysis."""

    analysis_id: str = Field(..., description="UUID of the parent analysis run.")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp of the analysis.")
    detector_name: str = Field(..., description="Stable snake_case identifier for this detector.")
    status: str = Field(
        ...,
        description="One of: completed, partial, unavailable, error, not_found.",
    )
    result_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Detector-specific result payload.",
    )
    artifact_paths: dict[str, str] = Field(
        default_factory=dict,
        description="Named file-system paths for any output artefacts produced.",
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Caveats that contextualise this detector's findings.",
    )


class VideoAnalysisResponse(BaseModel):
    """Top-level response envelope returned by POST /api/v1/video/analyze."""

    analysis_id: str = Field(..., description="UUID of this analysis run.")
    timestamp: str = Field(..., description="ISO-8601 UTC timestamp when the analysis started.")
    status: str = Field(
        ...,
        description="Overall status: 'completed' when all detectors ran, 'partial' if any errored.",
    )
    artifact_paths: dict[str, str] = Field(
        default_factory=dict,
        description="Flat map of all artifact paths produced, keyed as <detector>.<name>.",
    )
    findings: list[VideoForensicFinding] = Field(
        default_factory=list,
        description="Ordered list of per-detector forensic findings.",
    )
