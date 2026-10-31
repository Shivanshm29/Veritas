import hashlib
from pathlib import Path
from typing import Any

import cv2


def analyze_video_metadata(video_path: str | Path) -> dict[str, Any]:
    path = Path(video_path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError("Could not open video file with OpenCV")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC) or 0)
    
    # Decode FourCC code
    fourcc_str = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip()
    duration_seconds = round(frame_count / fps, 2) if fps > 0 else 0.0

    cap.release()

    # Calculate SHA-256 hash of the video file
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return {
        "filename": path.name,
        "file_size_bytes": path.stat().st_size,
        "width": width,
        "height": height,
        "fps": round(fps, 2),
        "frame_count": frame_count,
        "duration_seconds": duration_seconds,
        "fourcc": fourcc_str,
        "sha256": digest.hexdigest(),
        "limitations": [
            "Container metadata can be stripped or modified by re-encoding tools without altering video content.",
            "Variable frame rate (VFR) videos may report nominal average FPS values.",
        ],
    }
