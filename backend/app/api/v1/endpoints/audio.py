"""
Audio Forensics API Endpoint.

Route: POST /api/v1/audio/analyze

Accepts an audio upload, validates it, and runs the full audio forensic analysis
pipeline, returning structured findings.
"""

import logging
import os
import wave
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from scipy.io import wavfile
from starlette.concurrency import run_in_threadpool

from backend.app.schemas.audio import AudioAnalysisResponse
from backend.app.services.audio_forensics.analysis import analyze_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["Audio Forensics"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MAX_AUDIO_UPLOAD_BYTES: int = int(os.getenv("VERITAS_MAX_AUDIO_UPLOAD_BYTES", str(50 * 1024 * 1024)))
ARTIFACTS_ROOT: Path = Path(os.getenv("VERITAS_ARTIFACTS_DIR", "artifacts"))
ALLOWED_AUDIO_EXTENSIONS: frozenset[str] = frozenset({".wav", ".mp3", ".ogg", ".flac", ".m4a"})


@router.post(
    "/analyze",
    response_model=AudioAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze an audio file for synthetic voice and tampering indicators",
    description=(
        "Upload an audio file (WAV, MP3, OGG, FLAC, M4A — max 50 MB) and receive a "
        "structured forensic report covering container metadata, STFT spectrogram frequency cutoffs, "
        "pitch & voice modulation continuity (AI voice clone indicator), silence/splice discontinuity detection, "
        "and C2PA content credentials."
    ),
)
async def analyze_audio_upload(
    file: UploadFile = File(..., description="Audio file to analyze."),
) -> AudioAnalysisResponse:
    """Full forensic analysis pipeline for a single uploaded audio asset."""
    upload_id = str(uuid4())
    staging_dir = ARTIFACTS_ROOT / ".uploads"
    staging_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(file.filename or "uploaded_audio.wav").name
    file_ext = Path(filename).suffix.lower()

    if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format: '{file_ext}'. Allowed formats: {sorted(ALLOWED_AUDIO_EXTENSIONS)}",
        )

    temporary_path = staging_dir / f"{upload_id}{file_ext}"
    total_bytes = 0

    try:
        # Stream upload with size guard
        with temporary_path.open("wb") as target:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_AUDIO_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Upload exceeds the {MAX_AUDIO_UPLOAD_BYTES}-byte limit.",
                    )
                target.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded audio file is empty.",
            )

        # Validate that audio can be parsed
        is_decodable = False
        try:
            with wave.open(str(temporary_path), "rb") as wf:
                if wf.getnframes() > 0:
                    is_decodable = True
        except Exception:
            try:
                sr, data = wavfile.read(str(temporary_path))
                if len(data) > 0:
                    is_decodable = True
            except Exception:
                pass

        if not is_decodable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is corrupted or not a recognized audio stream.",
            )

        # Run audio forensics pipeline in threadpool
        raw = await run_in_threadpool(analyze_audio, temporary_path, ARTIFACTS_ROOT)

        # Inject original filename into metadata finding
        for finding in raw.get("findings", []):
            if finding["detector_name"] == "audio_metadata_analysis":
                finding["result_details"]["filename"] = filename

        return AudioAnalysisResponse(**raw)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Audio analysis failed for upload_id=%s", upload_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio analysis pipeline encountered an error: {exc}",
        ) from exc
    finally:
        await file.close()
        if temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
