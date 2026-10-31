from pathlib import Path
from typing import Any

import cv2
import numpy as np


def analyze_frequency_domain(
    sampled_frames: list[tuple[int, np.ndarray]],
    output_dir: str | Path,
) -> dict[str, Any]:
    """
    Analyzes 2D Fast Fourier Transform (FFT) power spectra across video frames.
    Synthetic diffusion and GAN generators leave periodic spectral artifacts
    and atypical high-frequency energy distributions.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    spectrum_path = output_dir / "fft_spectral_magnitude.png"

    if not sampled_frames:
        return {
            "status": "partial",
            "details": "No frames provided for frequency analysis.",
            "limitations": ["Requires at least 1 decodable frame."],
        }

    high_freq_ratios: list[float] = []
    accumulated_magnitude: np.ndarray | None = None

    for _, frame_rgb in sampled_frames:
        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        h, w = gray.shape

        # Compute 2D FFT and shift zero-frequency to center
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-7)

        if accumulated_magnitude is None:
            accumulated_magnitude = magnitude_spectrum.copy()
        else:
            accumulated_magnitude += magnitude_spectrum

        # Measure high-frequency ratio (outer region vs inner low-frequency core)
        cy, cx = h // 2, w // 2
        radius = min(h, w) // 4
        y, x = np.ogrid[:h, :w]
        mask_low = (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
        
        low_energy = float(np.sum(np.abs(fshift)[mask_low]))
        total_energy = float(np.sum(np.abs(fshift))) + 1e-7
        high_freq_ratio = float((total_energy - low_energy) / total_energy)
        high_freq_ratios.append(high_freq_ratio)

    avg_magnitude = accumulated_magnitude / len(sampled_frames)
    norm_mag = cv2.normalize(avg_magnitude, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    color_spectrum = cv2.applyColorMap(norm_mag, cv2.COLORMAP_VIRIDIS)
    cv2.imwrite(str(spectrum_path), color_spectrum)

    mean_high_freq = float(np.mean(high_freq_ratios))

    return {
        "status": "completed",
        "method": "2D Fast Fourier Transform (FFT) Power Spectrum Analysis",
        "frames_analyzed": len(sampled_frames),
        "mean_high_frequency_ratio": round(mean_high_freq, 4),
        "interpretation": (
            "Examines the spatial frequency distribution across video frames. "
            "Generative AI video models (diffusion networks and GANs) frequently display "
            "abnormal frequency spikes or severe high-frequency attenuation compared to optical camera sensors."
        ),
        "limitations": [
            "Heavy H.264/H.265 video compression naturally suppresses high frequencies.",
            "Visual spectrum plot provides qualitative forensic assessment rather than binary truth.",
        ],
        "artifact_paths": {
            "spectral_magnitude_heatmap": str(spectrum_path.resolve()),
        },
    }
