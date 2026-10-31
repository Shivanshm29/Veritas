from pathlib import Path
from typing import Any

import cv2
import numpy as np
from scipy.io import wavfile
from scipy.signal import spectrogram


def analyze_spectrogram(
    audio_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """
    Computes STFT spectrogram and detects artificial frequency cutoffs.
    Many generative voice cloning and TTS models fail to synthesize frequencies
    above 8 kHz or 11 kHz, leaving an unnaturally sharp spectral shelf.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    spectrogram_img_path = output_dir / "audio_spectrogram.png"

    # Read audio samples
    sample_rate, data = wavfile.read(str(audio_path))
    
    # If stereo, mix to mono
    if data.ndim > 1:
        samples = data.mean(axis=1).astype(np.float32)
    else:
        samples = data.astype(np.float32)

    if len(samples) == 0:
        raise ValueError("Audio file contains 0 samples")

    # Normalize samples to [-1.0, 1.0]
    max_val = np.max(np.abs(samples)) or 1.0
    samples = samples / max_val

    # Compute Spectrogram using scipy
    nperseg = min(1024, len(samples))
    frequencies, times, sxx = spectrogram(samples, fs=sample_rate, nperseg=nperseg, noverlap=nperseg // 2)

    # Convert power to dB log scale
    sxx_db = 10 * np.log10(sxx + 1e-10)

    # Generate visual spectrogram artifact via OpenCV colormap
    norm_sxx = cv2.normalize(sxx_db, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    # Flip vertically so low frequencies are at the bottom
    norm_sxx_flipped = cv2.flip(norm_sxx, 0)
    color_spec = cv2.applyColorMap(norm_sxx_flipped, cv2.COLORMAP_INFERNO)
    cv2.imwrite(str(spectrogram_img_path), color_spec)

    # Frequency Cutoff Forensic Measurement:
    nyquist = sample_rate / 2.0
    cutoff_threshold_hz = min(8000.0, nyquist * 0.8)
    high_freq_mask = frequencies >= cutoff_threshold_hz

    total_spectral_energy = float(np.sum(sxx)) + 1e-10
    high_freq_energy = float(np.sum(sxx[high_freq_mask, :])) if np.any(high_freq_mask) else 0.0
    high_freq_energy_ratio = high_freq_energy / total_spectral_energy

    # Unnatural cutoff indicator: if audio sample rate allows high frequencies (>16kHz)
    # but high frequency energy is virtually zero (< 0.005), it indicates an artificial bandwidth limit.
    has_unnatural_high_frequency_cutoff = (sample_rate >= 16000) and (high_freq_energy_ratio < 0.005)

    return {
        "status": "completed",
        "sample_rate_hz": sample_rate,
        "max_frequency_hz": round(nyquist, 1),
        "cutoff_threshold_hz": round(cutoff_threshold_hz, 1),
        "high_frequency_energy_ratio": round(high_freq_energy_ratio, 5),
        "has_unnatural_high_frequency_cutoff": has_unnatural_high_frequency_cutoff,
        "interpretation": (
            "Spectral energy analysis evaluates whether frequencies naturally taper off. "
            "A sudden abrupt drop to zero above 8kHz or 11kHz in wideband audio is a signature "
            "of neural vocoder band-limiting (common in synthesized speech and voice clones)."
        ),
        "limitations": [
            "Telephone bandpass filters (e.g., G.711 codec) naturally cut off audio above 3.4kHz.",
            "Aggressive lossy audio compression (e.g., low-bitrate MP3) can artificially truncate high frequencies.",
        ],
        "artifact_paths": {
            "spectrogram_heatmap": str(spectrogram_img_path.resolve()),
        },
    }
