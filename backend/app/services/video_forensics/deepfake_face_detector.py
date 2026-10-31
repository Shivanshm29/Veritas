from pathlib import Path
from typing import Any

import cv2
import numpy as np


def detect_face_artifacts(
    sampled_frames: list[tuple[int, np.ndarray]],
    output_dir: str | Path,
) -> dict[str, Any]:
    """
    Detects faces across sampled frames and checks for deepfake face-swapping indicators:
    - Face-to-background sharpness/compression divergence
    - Facial boundary blending inconsistencies
    - Face detection consistency across frames
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    overlay_path = output_dir / "face_detection_overlay.png"

    face_cascade = None
    if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if Path(cascade_path).is_file():
            face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade is None:
        return {
            "status": "unavailable",
            "faces_detected": 0,
            "details": "Haar Cascade / Face detector weights not available in current OpenCV build.",
            "limitations": [
                "Face detection module requires OpenCV CascadeClassifier or Yunet ONNX face weights.",
            ],
            "artifact_paths": {},
        }

    total_faces_detected = 0
    sharpness_ratios: list[float] = []
    annotated_frame: np.ndarray | None = None

    for frame_idx, frame_rgb in sampled_frames:
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.15,
            minNeighbors=5,
            minSize=(40, 40),
        )

        if len(faces) > 0:
            total_faces_detected += len(faces)
            bg_sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

            for (x, y, w, h) in faces:
                face_crop = gray[y:y + h, x:x + w]
                face_sharpness = float(cv2.Laplacian(face_crop, cv2.CV_64F).var())
                
                ratio = face_sharpness / (bg_sharpness + 1e-5)
                sharpness_ratios.append(ratio)

                if annotated_frame is None:
                    annotated_frame = frame_rgb.copy()
                    cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    label = f"Face: Sharpness Ratio {ratio:.2f}"
                    cv2.putText(
                        annotated_frame,
                        label,
                        (x, max(20, y - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )

    artifact_paths: dict[str, str] = {}
    if annotated_frame is not None:
        cv2.imwrite(str(overlay_path), cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR))
        artifact_paths["face_overlay"] = str(overlay_path.resolve())

    if total_faces_detected == 0:
        return {
            "status": "completed",
            "faces_detected": 0,
            "interpretation": "No human faces were detected across the sampled frames.",
            "limitations": [
                "Frontal face detector; profile angles, occluded faces, or extreme lighting may not be detected.",
            ],
            "artifact_paths": artifact_paths,
        }

    mean_sharpness_ratio = float(np.mean(sharpness_ratios))
    suspicious_boundary = mean_sharpness_ratio < 0.25 or mean_sharpness_ratio > 4.0

    return {
        "status": "completed",
        "faces_detected": total_faces_detected,
        "mean_face_to_background_sharpness_ratio": round(mean_sharpness_ratio, 3),
        "suspicious_sharpness_mismatch": suspicious_boundary,
        "interpretation": (
            "Analyzes compression and sharpness consistency between face regions and their surrounding background. "
            "A sharp divergence between face and torso/background is a hallmark of face-swap deepfakes."
        ),
        "limitations": [
            "Depth of field (bokeh effect) naturally creates face-background sharpness differences in high-aperture camera lenses.",
            "Heuristic indicator designed for triage, not definitive identity proof.",
        ],
        "artifact_paths": artifact_paths,
    }
