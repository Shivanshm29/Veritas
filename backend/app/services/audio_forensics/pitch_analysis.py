from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import wavfile


def analyze_pitch_and_modulation(audio_path: str | Path) -> dict[str, Any]:
    """
    Evaluates pitch (F0) continuity, micro-tremors, and Zero-Crossing Rate (ZCR).
    Human speech features natural vocal fold jitter and continuous pitch glides,
    whereas low-tier neural clones can sound robotically steady or exhibit discontinuous jumps.
    """
    sample_rate, data = wavfile.read(str(audio_path))

    if data.ndim > 1:
        samples = data.mean(axis=1).astype(np.float32)
    else:
        samples = data.astype(np.float32)

    if len(samples) < 512:
        return {
            "status": "partial",
            "details": "Audio length is too short for pitch & modulation analysis.",
            "limitations": ["Requires at least 512 samples."],
        }

    # Normalize samples
    max_val = np.max(np.abs(samples)) or 1.0
    samples = samples / max_val

    # 1. Zero Crossing Rate (ZCR)
    zero_crossings = np.sum(np.abs(np.diff(np.sign(samples)))) / (2 * len(samples))

    # 2. Frame-based Short-Time Energy & Pitch Tracking via Autocorrelation
    frame_size = int(0.03 * sample_rate)  # 30 ms frames
    hop_size = int(0.015 * sample_rate)   # 15 ms hop
    num_frames = (len(samples) - frame_size) // hop_size

    pitches: list[float] = []
    min_lag = int(sample_rate / 450)  # max human pitch ~450 Hz
    max_lag = int(sample_rate / 60)   # min human pitch ~60 Hz

    for i in range(max(1, num_frames)):
        frame = samples[i * hop_size : i * hop_size + frame_size]
        # Only process voiced frames with sufficient energy
        frame_energy = np.mean(frame ** 2)
        if frame_energy > 0.001:
            # Autocorrelation
            corr = np.correlate(frame, frame, mode="full")
            corr = corr[len(corr) // 2 :]

            if len(corr) > max_lag:
                valid_corr = corr[min_lag:max_lag]
                peak_idx = np.argmax(valid_corr) + min_lag
                if corr[peak_idx] > 0.25 * corr[0]:  # Valid pitch peak
                    freq = sample_rate / peak_idx
                    pitches.append(freq)

    voiced_ratio = len(pitches) / max(1, num_frames)
    mean_pitch = float(np.mean(pitches)) if pitches else 0.0
    pitch_std = float(np.std(pitches)) if pitches else 0.0
    
    # Robotic Voice Indicator: If pitch variation is unnaturally flat during voiced speech
    is_unnaturally_flat_pitch = (len(pitches) > 10) and (pitch_std < 4.0)

    return {
        "status": "completed",
        "mean_pitch_hz": round(mean_pitch, 2),
        "pitch_standard_deviation": round(pitch_std, 2),
        "voiced_speech_ratio": round(voiced_ratio, 3),
        "zero_crossing_rate": round(float(zero_crossings), 4),
        "is_unnaturally_monotone": is_unnaturally_flat_pitch,
        "interpretation": (
            "Natural human speech displays continuous pitch fluctuations, vibrato, and intonation variations. "
            "A pitch standard deviation below 4 Hz during sustained speech indicates robotic or synthetic flat generation."
        ),
        "limitations": [
            "Whispered speech or purely unvoiced audio cannot be tracked with pitch autocorrelation.",
            "Monotone singing or deliberate robotic voice imitation by humans can produce low pitch variance.",
        ],
    }
