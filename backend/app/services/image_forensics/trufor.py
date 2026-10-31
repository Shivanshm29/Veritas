import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


def run_trufor(
    image_path: str | Path, output_dir: str | Path
) -> dict[str, Any]:
    repo_dir = Path(os.getenv("TRUFOR_DIR", "")).expanduser()
    weights = Path(os.getenv("TRUFOR_MODEL_FILE", "")).expanduser()
    python_executable = os.getenv("TRUFOR_PYTHON", sys.executable)
    test_script = repo_dir / "TruFor_train_test" / "test.py"
    if not repo_dir.is_dir() or not test_script.is_file():
        return {
            "status": "unavailable",
            "model": "TruFor",
            "model_version": "official GRIP-UNINA project (CVPR 2023)",
            "details": "Set TRUFOR_DIR to a local official TruFor checkout.",
        }
    if not weights.is_file():
        return {
            "status": "unavailable",
            "model": "TruFor",
            "model_version": "official GRIP-UNINA project (CVPR 2023)",
            "checkpoint": weights.name if weights.is_file() else None,
            "details": (
                "Set TRUFOR_MODEL_FILE to the official pretrained trufor.pth.tar "
                "checkpoint after obtaining it under the project's license."
            ),
        }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_path = Path(image_path)
    model_output_dir = output_dir / "trufor_raw"
    model_output_dir.mkdir(exist_ok=True)
    command = [
        python_executable,
        str(test_script),
        "-g",
        "-1",
        "-in",
        str(source_path.resolve()).replace("\\", "/"),
        "-out",
        str(model_output_dir.resolve()),
        "-exp",
        "trufor_ph3",
        "TEST.MODEL_FILE",
        str(weights.resolve()),
    ]
    completed = subprocess.run(
        command,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=int(os.getenv("TRUFOR_TIMEOUT_SECONDS", "240")),
        check=False,
    )
    npz_path = model_output_dir / f"{source_path.name}.npz"
    if completed.returncode != 0 or not npz_path.is_file():
        raise RuntimeError(
            "TruFor inference failed "
            f"(exit {completed.returncode}): "
            f"{(completed.stderr or completed.stdout)[-2000:]}"
        )

    with np.load(npz_path, allow_pickle=False) as prediction:
        anomaly_map = np.asarray(prediction["map"], dtype=np.float32)
        detection_score = (
            float(np.asarray(prediction["score"]).item())
            if "score" in prediction.files
            else None
        )
        confidence_map = (
            np.asarray(prediction["conf"], dtype=np.float32)
            if "conf" in prediction.files
            else None
        )

    anomaly_map = np.nan_to_num(anomaly_map, nan=0.0, posinf=1.0, neginf=0.0)
    anomaly_map = np.clip(anomaly_map, 0.0, 1.0)
    localization_path = output_dir / "trufor_localization.png"
    overlay_path = output_dir / "trufor_overlay.png"
    mask_path = output_dir / "trufor_mask.png"
    confidence_path: Path | None = None
    anomaly_uint8 = np.round(anomaly_map * 255).astype(np.uint8)
    Image.fromarray(anomaly_uint8).save(localization_path)
    Image.fromarray((anomaly_map >= 0.5).astype(np.uint8) * 255).save(mask_path)
    if confidence_map is not None:
        confidence_map = np.clip(
            np.nan_to_num(confidence_map, nan=0.0, posinf=1.0, neginf=0.0),
            0.0,
            1.0,
        )
        confidence_path = output_dir / "trufor_reliability.png"
        Image.fromarray(np.round(confidence_map * 255).astype(np.uint8)).save(
            confidence_path
        )

    with Image.open(image_path) as original:
        original_rgb = np.asarray(original.convert("RGB"))
    resized_map = cv2.resize(
        anomaly_uint8,
        (original_rgb.shape[1], original_rgb.shape[0]),
        interpolation=cv2.INTER_LINEAR,
    )
    color_map = cv2.applyColorMap(resized_map, cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(
        cv2.cvtColor(original_rgb, cv2.COLOR_RGB2BGR), 0.6, color_map, 0.4, 0
    )
    cv2.imwrite(str(overlay_path), overlay)

    return {
        "status": "completed",
        "model": "TruFor",
        "model_version": _git_revision(repo_dir)
        or "unknown (local checkout does not expose a Git revision)",
        "checkpoint": weights.name,
        "detection_score": detection_score,
        "localization_map": {
            "minimum": float(anomaly_map.min()),
            "maximum": float(anomaly_map.max()),
            "mean": float(anomaly_map.mean()),
            "threshold_for_visual_mask": 0.5,
        },
        "reliability_map": (
            {
                "minimum": float(confidence_map.min()),
                "maximum": float(confidence_map.max()),
                "mean": float(confidence_map.mean()),
            }
            if confidence_map is not None
            else None
        ),
        "reliability_map_available": confidence_map is not None,
        "limitations": (
            "The binary visualization threshold is for display, not a calibrated "
            "decision threshold. The official TruFor code/checkpoint is restricted "
            "to nonprofit use by its license."
        ),
        "artifact_paths": {
            "localization_map": str(localization_path.resolve()),
            "overlay": str(overlay_path.resolve()),
            "mask": str(mask_path.resolve()),
            "raw_model_output": str(npz_path.resolve()),
            **({
                "reliability_map": str(confidence_path.resolve())
            } if confidence_path else {}),
        },
    }


def _git_revision(repo_dir: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None
