"""
Provenance & Historical Media Matching API Endpoints.
Module 8 of PRAMAAN / Veritas.

Routes:
- POST /api/v1/provenance/fingerprint: Generates perceptual fingerprints
- POST /api/v1/provenance/match: Searches historical reference collection
- GET /api/v1/provenance/references: Lists known historical reference assets
- POST /api/v1/provenance/graph/validate: Validates DAG and builds evidence graph
"""

import hashlib
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from backend.app.schemas.provenance import (
    HistoricalMatchResponse,
    MediaFingerprint,
    ProvenanceEdge,
    ProvenanceGraphResponse,
    ProvenanceNode,
    ProvenanceTimelineEntry,
)
from backend.app.services.provenance.graph_builder import build_provenance_graph
from backend.app.services.provenance.hasher import (
    compute_image_fingerprint,
    compute_video_fingerprints,
)
from backend.app.services.provenance.matcher import match_against_historical_references
from backend.app.services.provenance.reference_store import (
    ReferenceMediaItem,
    reference_store,
)

router = APIRouter(prefix="/provenance", tags=["Provenance & Historical Matching"])


class GraphValidationRequest(BaseModel):
    investigation_id: str
    nodes: List[ProvenanceNode]
    edges: List[ProvenanceEdge]
    timeline_entries: Optional[List[ProvenanceTimelineEntry]] = None


class ReferenceItemResponse(BaseModel):
    id: str
    title: str
    source_url: str
    publisher: str
    original_published_date: str
    sha256_hash: str
    phash: str
    description: str


@router.post(
    "/fingerprint",
    response_model=MediaFingerprint,
    status_code=status.HTTP_200_OK,
    summary="Generate perceptual fingerprint for media",
    description="Computes DCT pHash, dHash, aHash, and color moments for an uploaded image or video.",
)
async def generate_media_fingerprint(
    file: UploadFile = File(..., description="Image or video asset to fingerprint."),
) -> MediaFingerprint:
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    filename = (file.filename or "").lower()
    try:
        if any(filename.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"]):
            fp = compute_image_fingerprint(content)
            return MediaFingerprint(**fp)
        elif any(filename.endswith(ext) for ext in [".mp4", ".mov", ".avi", ".webm"]):
            # For video, save to temp and extract
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                fp = compute_video_fingerprints(tmp_path)
                return MediaFingerprint(**fp)
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        else:
            # Fallback treat as image
            fp = compute_image_fingerprint(content)
            return MediaFingerprint(**fp)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not generate perceptual fingerprint: {exc}",
        ) from exc


@router.post(
    "/match",
    response_model=HistoricalMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Match media against historical reference collection",
    description=(
        "Searches reference media collections for visually similar or identical assets. "
        "Distinguishes verified identical/derivative matches from tentative similarity."
    ),
)
async def match_media_against_references(
    file: Optional[UploadFile] = File(None, description="Image/video asset to search for."),
    phash: Optional[str] = Query(None, description="Optional direct 64-bit pHash hex string."),
    dhash: Optional[str] = Query(None, description="Optional direct 64-bit dHash hex string."),
) -> HistoricalMatchResponse:
    if file is not None:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
        sha256 = hashlib.sha256(content).hexdigest()
        try:
            fp_dict = compute_image_fingerprint(content)
            fingerprint = MediaFingerprint(**fp_dict)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to process media: {exc}")
    elif phash is not None:
        fingerprint = MediaFingerprint(
            phash=phash,
            dhash=dhash or phash,
            ahash=phash,
            color_fingerprint="00000000",
        )
        sha256 = "manual_query_hash"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a media file upload or a perceptual hash parameter.",
        )

    return match_against_historical_references(fingerprint, query_sha256=sha256)


@router.get(
    "/references",
    response_model=List[ReferenceItemResponse],
    summary="List historical reference assets",
    description="Returns all verified historical original and archival reference items in the store.",
)
async def list_historical_references() -> List[ReferenceItemResponse]:
    items = reference_store.get_all()
    return [
        ReferenceItemResponse(
            id=item.id,
            title=item.title,
            source_url=item.source_url,
            publisher=item.publisher,
            original_published_date=item.original_published_date,
            sha256_hash=item.sha256_hash,
            phash=item.phash,
            description=item.description,
        )
        for item in items
    ]


@router.post(
    "/graph/validate",
    response_model=ProvenanceGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate and build provenance evidence graph",
    description="Constructs the provenance graph, validates that it is a cycle-free DAG, and generates the timeline.",
)
async def validate_and_build_graph(request: GraphValidationRequest) -> ProvenanceGraphResponse:
    return build_provenance_graph(
        investigation_id=request.investigation_id,
        nodes=request.nodes,
        edges=request.edges,
        timeline_entries=request.timeline_entries,
    )
