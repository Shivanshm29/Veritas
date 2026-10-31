"""
Image Forensics API Endpoint.

Route: POST /api/v1/image/analyze

Accepts an image upload, validates it, and runs the full forensic analysis
pipeline, returning structured findings.
"""

import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from backend.app.schemas.image import ImageAnalysisResponse
from backend.app.services.image_forensics.analysis import analyze_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["Image Forensics"])

# ---------------------------------------------------------------------------
# Configuration (mirrors original forge env-var conventions)
# ---------------------------------------------------------------------------
MAX_UPLOAD_BYTES: int = int(os.getenv("VERITAS_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
MAX_IMAGE_PIXELS: int = int(os.getenv("VERITAS_MAX_IMAGE_PIXELS", "40000000"))
ARTIFACTS_ROOT: Path = Path(os.getenv("VERITAS_ARTIFACTS_DIR", "artifacts"))
ALLOWED_FORMATS: frozenset[str] = frozenset({"JPEG", "PNG", "WEBP", "TIFF", "BMP"})

_FORMAT_SUFFIX: dict[str, str] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "TIFF": ".tiff",
    "BMP": ".bmp",
}


@router.post(
    "/analyze",
    response_model=ImageAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze an image for forensic indicators",
    description=(
        "Upload an image (JPEG, PNG, WEBP, TIFF, BMP — max 25 MB) and receive a "
        "structured forensic report covering metadata, ELA, copy-move detection, "
        "TruFor forgery localization, AI-image classification, and C2PA credential "
        "validation. All findings are **indicators**, not proof of manipulation."
    ),
)
async def analyze_image_upload(
    file: UploadFile = File(..., description="Image file to analyze."),
) -> ImageAnalysisResponse:
    """Full forensic analysis pipeline for a single uploaded image."""
    upload_id = str(uuid4())
    staging_dir = ARTIFACTS_ROOT / ".uploads"
    staging_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = staging_dir / f"{upload_id}.upload"
    total_bytes = 0

    try:
        # ── Stream upload with size guard ───────────────────────────────────
        with temporary_path.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeds the {MAX_UPLOAD_BYTES}-byte limit.",
                    )
                target.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # ── Validate image ───────────────────────────────────────────────────
        try:
            with Image.open(temporary_path) as image:
                if image.format not in ALLOWED_FORMATS:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported image format: {image.format}.",
                    )
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Image exceeds the {MAX_IMAGE_PIXELS}-pixel limit.",
                    )
                image_format = image.format
                image.verify()
        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is not a recognized image.",
            ) from exc
        except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image is corrupted or unreadable.",
            ) from exc

        # ── Rename to a typed extension ──────────────────────────────────────
        normalized_path = staging_dir / f"{upload_id}{_FORMAT_SUFFIX[image_format]}"
        if normalized_path != temporary_path:
            temporary_path.replace(normalized_path)
            temporary_path = normalized_path

        # ── Run forensics pipeline (thread-pool, non-blocking) ───────────────
        raw = await run_in_threadpool(analyze_image, temporary_path, ARTIFACTS_ROOT)

        # ── Inject original filename into metadata finding ───────────────────
        metadata_finding = next(
            (f for f in raw["findings"] if f["detector_name"] == "metadata_analysis"),
            None,
        )
        if metadata_finding:
            metadata_finding["result_details"]["filename"] = Path(
                file.filename or "uploaded_image"
            ).name

        return ImageAnalysisResponse(**raw)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Image analysis failed for upload_id=%s", upload_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {exc}",
        ) from exc
    finally:
        await file.close()
        if temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
