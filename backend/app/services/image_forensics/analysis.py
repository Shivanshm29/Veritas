import logging
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from backend.app.services.image_forensics.ai_detector import detect_ai_image
from backend.app.services.image_forensics.c2pa_validation import validate_c2pa
from backend.app.services.image_forensics.copy_move import detect_copy_move
from backend.app.services.image_forensics.ela import analyze_ela
from backend.app.services.image_forensics.metadata import analyze_metadata
from backend.app.services.image_forensics.trufor import run_trufor

logger = logging.getLogger(__name__)


def analyze_image(image_path: str | Path, artifacts_root: str | Path) -> dict[str, Any]:
    analysis_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    output_dir = Path(artifacts_root) / analysis_id
    output_dir.mkdir(parents=True, exist_ok=False)
    source_path = Path(image_path)
    stored_original = output_dir / f"original{source_path.suffix.lower()}"
    if source_path.resolve() != stored_original.resolve():
        shutil.copy2(source_path, stored_original)
    image_path = stored_original
    artifact_paths: dict[str, str] = {
        "original": str(stored_original.resolve()),
    }
    findings: list[dict[str, Any]] = []

    _run_detector(
        findings,
        "metadata_analysis",
        "completed",
        analyze_metadata,
        image_path,
    )
    _run_detector(
        findings,
        "error_level_analysis",
        "completed",
        analyze_ela,
        image_path,
        output_dir,
    )
    _run_detector(
        findings,
        "copy_move_heuristic",
        "completed",
        detect_copy_move,
        image_path,
        output_dir,
    )
    _run_detector(
        findings,
        "trufor_forgery_localization",
        "unavailable",
        run_trufor,
        image_path,
        output_dir,
    )
    _run_detector(
        findings,
        "ai_image_classification",
        "unavailable",
        detect_ai_image,
        image_path,
    )
    _run_detector(
        findings,
        "c2pa_credential_validation",
        "unavailable",
        validate_c2pa,
        image_path,
    )

    for finding in findings:
        finding["analysis_id"] = analysis_id
        finding["timestamp"] = created_at
        artifact_paths.update(
            {
                f"{finding['detector_name']}.{name}": path
                for name, path in finding["artifact_paths"].items()
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
        logger.exception("Detector %s failed", detector_name)
        findings.append(
            {
                "detector_name": detector_name,
                "status": "error",
                "result_details": {"error": str(error)},
                "artifact_paths": {},
                "limitations": [],
            }
        )
