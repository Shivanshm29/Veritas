import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.app.services.audio_forensics.c2pa_validation import validate_audio_c2pa
from backend.app.services.audio_forensics.metadata import analyze_audio_metadata
from backend.app.services.audio_forensics.pitch_analysis import analyze_pitch_and_modulation
from backend.app.services.audio_forensics.spectrogram import analyze_spectrogram
from backend.app.services.audio_forensics.splice_detection import detect_splices_and_silence

logger = logging.getLogger(__name__)


def analyze_audio(audio_path: str | Path, artifacts_root: str | Path) -> dict[str, Any]:
    """
    Executes the full forensic analysis pipeline on an uploaded audio file:
    1. Container and stream metadata extraction
    2. STFT Spectrogram & high-frequency cutoff analysis
    3. Pitch (F0) continuity & voice modulation analysis
    4. Silence & splice discontinuity detection
    5. C2PA content credential validation
    """
    analysis_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    output_dir = Path(artifacts_root) / analysis_id
    output_dir.mkdir(parents=True, exist_ok=False)

    source_path = Path(audio_path)
    stored_original = output_dir / f"original{source_path.suffix.lower()}"
    if source_path.resolve() != stored_original.resolve():
        shutil.copy2(source_path, stored_original)
    audio_path = stored_original

    artifact_paths: dict[str, str] = {
        "original": str(stored_original.resolve()),
    }
    findings: list[dict[str, Any]] = []

    # 1. Metadata Analysis
    _run_detector(
        findings,
        "audio_metadata_analysis",
        "completed",
        analyze_audio_metadata,
        audio_path,
    )

    # 2. Spectrogram & Frequency Cutoff
    _run_detector(
        findings,
        "spectrogram_frequency_analysis",
        "completed",
        analyze_spectrogram,
        audio_path,
        output_dir,
    )

    # 3. Pitch & Voice Modulation Continuity
    _run_detector(
        findings,
        "pitch_and_modulation_analysis",
        "completed",
        analyze_pitch_and_modulation,
        audio_path,
    )

    # 4. Silence & Splice Discontinuity Detection
    _run_detector(
        findings,
        "splice_and_silence_detection",
        "completed",
        detect_splices_and_silence,
        audio_path,
        output_dir,
    )

    # 5. C2PA Content Credentials Validation
    _run_detector(
        findings,
        "c2pa_credential_validation",
        "unavailable",
        validate_audio_c2pa,
        audio_path,
    )

    for finding in findings:
        finding["analysis_id"] = analysis_id
        finding["timestamp"] = created_at
        artifact_paths.update(
            {
                f"{finding['detector_name']}.{name}": path
                for name, path in finding.get("artifact_paths", {}).items()
            }
        )

    return {
        "analysis_id": analysis_id,
        "timestamp": created_at,
        "status": (
            "partial"
            if any(finding["status"] == "error" for finding in findings)
            else "completed"
        ),
        "artifact_paths": artifact_paths,
        "findings": findings,
    }


def _run_detector(
    findings: list[dict[str, Any]],
    detector_name: str,
    default_status: str,
    detector: Callable[..., dict[str, Any]],
    *args: Any,
) -> None:
    try:
        result = detector(*args)
        status = str(result.pop("status", default_status))
        paths = result.pop("artifact_paths", {})
        limitations = result.pop("limitations", [])
        if isinstance(limitations, str):
            limitations = [limitations]
        findings.append(
            {
                "detector_name": detector_name,
                "status": status,
                "result_details": result,
                "artifact_paths": paths,
                "limitations": limitations,
            }
        )
    except Exception as error:
        logger.exception("Audio detector %s failed", detector_name)
        findings.append(
            {
                "detector_name": detector_name,
                "status": "error",
                "result_details": {"error": str(error)},
                "artifact_paths": {},
                "limitations": [],
            }
        )
