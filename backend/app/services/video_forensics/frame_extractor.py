from pathlib import Path
from typing import Any

import cv2
import numpy as np


def extract_sample_frames(
    video_path: str | Path,
    output_dir: str | Path,
    max_samples: int = 16,
) -> tuple[list[tuple[int, np.ndarray]], dict[str, str]]:
    """
    Extracts representative sample frames uniformly spaced across the video.
    Returns (list of (frame_index, frame_rgb), artifact_paths dict).
    """
    output_dir = Path(output_dir)
    frames_dir = output_dir / "keyframes"
    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("Could not open video file for frame extraction")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if total_frames <= 0:
        # Fallback reading sequentially
        all_frames: list[np.ndarray] = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            all_frames.append(frame)
        total_frames = len(all_frames)
        cap.release()

        if total_frames == 0:
            raise ValueError("Video contains 0 decodable frames")

        indices = np.linspace(0, total_frames - 1, min(max_samples, total_frames), dtype=int)
        sampled = [(int(idx), cv2.cvtColor(all_frames[idx], cv2.COLOR_BGR2RGB)) for idx in indices]
    else:
        indices = np.linspace(0, total_frames - 1, min(max_samples, total_frames), dtype=int)
        sampled = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ret, frame = cap.read()
            if ret and frame is not None:
                sampled.append((int(idx), cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        cap.release()

    if not sampled:
        raise ValueError("Failed to extract any valid frames from the video")

    artifact_paths: dict[str, str] = {}
    for i, (frame_idx, frame_rgb) in enumerate(sampled):
        frame_filename = f"keyframe_{i:02d}_frame_{frame_idx}.png"
        frame_file_path = frames_dir / frame_filename
        cv2.imwrite(str(frame_file_path), cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))
        artifact_paths[f"keyframe_{i}"] = str(frame_file_path.resolve())

    return sampled, artifact_paths
