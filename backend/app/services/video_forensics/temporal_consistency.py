from pathlib import Path
from typing import Any

import cv2
import numpy as np


def analyze_temporal_consistency(
    sampled_frames: list[tuple[int, np.ndarray]],
    output_dir: str | Path,
) -> dict[str, Any]:
    """
    Evaluates temporal transitions between sampled frames:
    - Mean absolute pixel difference
    - Color histogram correlation
    - Sudden jumps/splicing artifacts
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    heatmap_path = output_dir / "temporal_difference_heatmap.png"

    if len(sampled_frames) < 2:
        return {
            "status": "partial",
            "frame_sample_count": len(sampled_frames),
            "details": "Insufficient frames to perform temporal analysis (video too short or single frame).",
            "limitations": ["Temporal consistency requires at least 2 consecutive sampled frames."],
        }

    differences: list[float] = []
    histogram_correlations: list[float] = []
    max_diff_img: np.ndarray | None = None
    max_diff_val = -1.0

    for i in range(len(sampled_frames) - 1):
        _, curr_rgb = sampled_frames[i]
        _, next_rgb = sampled_frames[i + 1]

        # Convert to grayscale
        curr_gray = cv2.cvtColor(curr_rgb, cv2.COLOR_RGB2GRAY)
        next_gray = cv2.cvtColor(next_rgb, cv2.COLOR_RGB2GRAY)

        # Absolute frame difference
        diff = cv2.absdiff(curr_gray, next_gray)
        mean_diff = float(np.mean(diff))
        differences.append(mean_diff)

        if mean_diff > max_diff_val:
            max_diff_val = mean_diff
            max_diff_img = diff

        # Color histogram correlation
        curr_hist = cv2.calcHist([curr_rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        next_hist = cv2.calcHist([next_rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        cv2.normalize(curr_hist, curr_hist)
        cv2.normalize(next_hist, next_hist)
        corr = float(cv2.compareHist(curr_hist, next_hist, cv2.HISTCMP_CORREL))
        histogram_correlations.append(corr)

    # Save visualization of peak difference
    if max_diff_img is not None:
        colored_diff = cv2.applyColorMap(max_diff_img, cv2.COLORMAP_JET)
        cv2.imwrite(str(heatmap_path), colored_diff)

    mean_temporal_diff = float(np.mean(differences))
    std_temporal_diff = float(np.std(differences))
    avg_hist_corr = float(np.mean(histogram_correlations))
    
    # Anomaly indicator: if standard deviation is exceptionally high relative to mean,
    # indicates unnatural jumps or cuts between frames.
    irregular_transitions = int(sum(d > (mean_temporal_diff + 2.0 * std_temporal_diff) for d in differences))

    return {
        "status": "completed",
        "sampled_transitions": len(differences),
        "mean_frame_difference": round(mean_temporal_diff, 3),
        "difference_standard_deviation": round(std_temporal_diff, 3),
        "mean_histogram_correlation": round(avg_hist_corr, 4),
        "irregular_transition_count": irregular_transitions,
        "is_smooth_transition": irregular_transitions == 0,
        "interpretation": (
            "Temporal consistency assesses continuity across consecutive frames. "
            "High variance or abrupt histogram drops indicate scene cuts, frame dropping, "
            "or temporal flickering common in synthesized video."
        ),
        "limitations": [
            "Camera motion, rapid scene panning, and intentional quick cuts cause legitimate temporal variance.",
            "Compression artifacts can slightly distort inter-frame correlation metrics.",
        ],
        "artifact_paths": {
            "peak_difference_heatmap": str(heatmap_path.resolve()),
        },
    }
