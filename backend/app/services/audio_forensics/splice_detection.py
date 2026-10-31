from pathlib import Path
from typing import Any

import cv2
import numpy as np
from scipy.io import wavfile


def detect_splices_and_silence(
    audio_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """
    Detects audio editing artifacts:
    - Digital zero insertion (absolute silence where ambient noise floor should exist)
    - Abrupt energy discontinuities (audio cuts and splicing points)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    energy_contour_path = output_dir / "energy_contour.png"

    sample_rate, data = wavfile.read(str(audio_path))
    if data.ndim > 1:
        samples = data.mean(axis=1).astype(np.float32)
    else:
        samples = data.astype(np.float32)

    if len(samples) == 0:
        raise ValueError("Audio file is empty")

    # Normalize
    max_val = np.max(np.abs(samples)) or 1.0
    samples = samples / max_val

    # 1. Digital absolute zero check (slices of exact 0.0)
    zero_runs = 0
    zero_samples_count = int(np.sum(samples == 0.0))
    zero_ratio = zero_samples_count / len(samples)

    # 2. Windowed Root-Mean-Square (RMS) Energy Contour
    window_size = int(0.02 * sample_rate)  # 20ms window
    if window_size < 1:
        window_size = 1

    num_windows = len(samples) // window_size
    rms_values: list[float] = []

    for i in range(num_windows):
        window = samples[i * window_size : (i + 1) * window_size]
        rms = float(np.sqrt(np.mean(window ** 2)))
        rms_values.append(rms)

    # Detect sudden energy jumps between consecutive windows
    energy_diffs = np.abs(np.diff(rms_values)) if len(rms_values) > 1 else np.array([0.0])
    mean_jump = float(np.mean(energy_diffs))
    std_jump = float(np.std(energy_diffs))

    # Potential splice points: energy transitions that deviate abnormally from surrounding context
    threshold = mean_jump + 3.0 * (std_jump + 1e-6)
    splice_candidates = int(np.sum(energy_diffs > threshold))

    # 3. Create Energy Contour Visual Plot
    img_height, img_width = 160, 400
    canvas = np.zeros((img_height, img_width, 3), dtype=np.uint8)
    if len(rms_values) > 1:
        norm_rms = np.array(rms_values)
        max_rms = np.max(norm_rms) or 1.0
        norm_rms = norm_rms / max_rms

        # Interpolate to canvas width
        x_points = np.linspace(0, img_width - 1, len(norm_rms)).astype(int)
        y_points = (img_height - 1 - norm_rms * (img_height - 20)).astype(int)
        
        pts = np.vstack((x_points, y_points)).T.reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts], isClosed=False, color=(0, 255, 120), thickness=2)

    cv2.imwrite(str(energy_contour_path), canvas)

    # Synthetic silence indicator: Real mic recordings rarely have > 5% exact digital 0.0
    has_synthetic_digital_silence = zero_ratio > 0.08

    return {
        "status": "completed",
        "digital_zero_ratio": round(zero_ratio, 5),
        "has_synthetic_digital_silence": has_synthetic_digital_silence,
        "splice_candidate_count": splice_candidates,
        "is_continuous_recording": splice_candidates == 0 and not has_synthetic_digital_silence,
        "interpretation": (
            "Natural acoustic recordings maintain a persistent room noise floor. "
            "Slices of pure digital silence (0.0) indicate synthetic silence insertion, "
            "and abnormal energy gradient spikes indicate cut/splice boundaries."
        ),
        "limitations": [
            "Noise-gate hardware and aggressive audio denoisers naturally mute background hiss into silence.",
            "Intentional artistic cuts in podcasts or edited broadcasts will register as splice candidates.",
        ],
        "artifact_paths": {
            "energy_contour": str(energy_contour_path.resolve()),
        },
    }
