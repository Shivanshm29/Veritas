"""
Video Forensics API Endpoint.

Route: POST /api/v1/video/analyze

Accepts a video upload, validates it, and runs the full video forensic analysis
pipeline, returning structured findings.
"""

import logging
import os
from pathlib import Path
from uuid import uuid4

import cv2
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from backend.app.schemas.video import VideoAnalysisResponse
from backend.app.services.video_forensics.analysis import analyze_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["Video Forensics"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_VIDEO_UPLOAD_BYTES: int = int(os.getenv("VERITAS_MAX_VIDEO_UPLOAD_BYTES", str(100 * 1024 * 1024)))
ARTIFACTS_ROOT: Path = Path(os.getenv("VERITAS_ARTIFACTS_DIR", "artifacts"))
ALLOWED_VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mp4", ".avi", ".mov", ".mkv", ".webm"})


@router.post(
    "/analyze",
    response_model=VideoAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a video for forensic and synthesis indicators",
    description=(
        "Upload a video file (MP4, AVI, MOV, MKV, WEBM — max 100 MB) and receive a "
        "structured forensic report covering container metadata, inter-frame temporal consistency, "
        "deepfake face boundary blending/sharpness artifacts, 2D spectral frequency anomalies, "
        "and C2PA content credentials."
    ),
)
async def analyze_video_upload(
    file: UploadFile = File(..., description="Video file to analyze."),
) -> VideoAnalysisResponse:
    """Full forensic analysis pipeline for a single uploaded video."""
    upload_id = str(uuid4())
    staging_dir = ARTIFACTS_ROOT / ".uploads"
    staging_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(file.filename or "uploaded_video.mp4").name
    file_ext = Path(filename).suffix.lower()

    if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported video format: '{file_ext}'. Allowed formats: {sorted(ALLOWED_VIDEO_EXTENSIONS)}",
        )

    temporary_path = staging_dir / f"{upload_id}{file_ext}"
    total_bytes = 0

    try:
        # Stream upload with size guard
        with temporary_path.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_VIDEO_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeds the {MAX_VIDEO_UPLOAD_BYTES}-byte limit.",
                    )
                target.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video file is empty.",
            )

        # Validate that video is decodable by OpenCV
        cap = cv2.VideoCapture(str(temporary_path))
        if not cap.isOpened():
            cap.release()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is corrupted or not a recognized video container.",
            )

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        ret, first_frame = cap.read()
        cap.release()

        if not ret or first_frame is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video does not contain decodable image frames.",
            )

        # Run video forensics pipeline in worker threadpool
        raw = await run_in_threadpool(analyze_video, temporary_path, ARTIFACTS_ROOT)

        # Set original filename in metadata result
        for finding in raw.get("findings", []):
            if finding["detector_name"] == "video_metadata_analysis":
                finding["result_details"]["filename"] = filename

        return VideoAnalysisResponse(**raw)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Video analysis failed for upload_id=%s", upload_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video analysis pipeline encountered an error: {exc}",
        ) from exc
    finally:
        await file.close()
        if temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
