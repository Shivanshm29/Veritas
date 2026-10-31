import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.app.services.video_forensics.c2pa_validation import validate_video_c2pa
from backend.app.services.video_forensics.deepfake_face_detector import detect_face_artifacts
from backend.app.services.video_forensics.frame_extractor import extract_sample_frames
from backend.app.services.video_forensics.frequency_analysis import analyze_frequency_domain
from backend.app.services.video_forensics.metadata import analyze_video_metadata
from backend.app.services.video_forensics.temporal_consistency import analyze_temporal_consistency

logger = logging.getLogger(__name__)


def analyze_video(video_path: str | Path, artifacts_root: str | Path) -> dict[str, Any]:
    """
    Executes the full forensic analysis pipeline on an uploaded video file:
    1. Container & stream metadata extraction
    2. Representative keyframe extraction
    3. Inter-frame temporal consistency & motion analysis
    4. Deepfake face artifact & sharpness mismatch detection
    5. 2D Spectral/Frequency FFT anomaly analysis
    6. C2PA content credential validation
    """
    analysis_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    output_dir = Path(artifacts_root) / analysis_id
    output_dir.mkdir(parents=True, exist_ok=False)

    source_path = Path(video_path)
    stored_original = output_dir / f"original{source_path.suffix.lower()}"
    if source_path.resolve() != stored_original.resolve():
        shutil.copy2(source_path, stored_original)
    video_path = stored_original

    artifact_paths: dict[str, str] = {
        "original": str(stored_original.resolve()),
    }
    findings: list[dict[str, Any]] = []

    # 1. Metadata Analysis
    _run_detector(
        findings,
        "video_metadata_analysis",
        "completed",
        analyze_video_metadata,
        video_path,
    )

    # 2. Extract Keyframes (Used by downstream visual detectors)
    sampled_frames = []
    try:
        sampled_frames, frame_artifacts = extract_sample_frames(video_path, output_dir, max_samples=16)
        artifact_paths.update(frame_artifacts)
        findings.append({
            "detector_name": "keyframe_extraction",
            "status": "completed",
            "result_details": {
                "extracted_frame_count": len(sampled_frames),
                "sampled_frame_indices": [f[0] for f in sampled_frames],
            },
            "artifact_paths": frame_artifacts,
            "limitations": ["Uniform sampling may bypass isolated single-frame edits."],
        })
    except Exception as error:
        logger.exception("Keyframe extraction failed")
        findings.append({
            "detector_name": "keyframe_extraction",
            "status": "error",
            "result_details": {"error": str(error)},
            "artifact_paths": {},
            "limitations": [],
        })

    # 3. Temporal Consistency
    if sampled_frames:
        _run_detector(
            findings,
            "temporal_consistency_analysis",
            "completed",
            analyze_temporal_consistency,
            sampled_frames,
            output_dir,
        )

    # 4. Deepfake Face Artifact Detection
    if sampled_frames:
        _run_detector(
            findings,
            "deepfake_face_detection",
            "completed",
            detect_face_artifacts,
            sampled_frames,
            output_dir,
        )

    # 5. Frequency Domain Spectral Analysis
    if sampled_frames:
        _run_detector(
            findings,
            "spectral_frequency_analysis",
            "completed",
            analyze_frequency_domain,
            sampled_frames,
            output_dir,
        )

    # 6. C2PA Content Credential Validation
    _run_detector(
        findings,
        "c2pa_credential_validation",
        "unavailable",
        validate_video_c2pa,
        video_path,
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
        logger.exception("Video detector %s failed", detector_name)
        findings.append(
            {
                "detector_name": detector_name,
                "status": "error",
                "result_details": {"error": str(error)},
                "artifact_paths": {},
                "limitations": [],
            }
        )
