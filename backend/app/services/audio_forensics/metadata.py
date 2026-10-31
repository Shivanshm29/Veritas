import hashlib
import wave
from pathlib import Path
from typing import Any

from scipy.io import wavfile


def analyze_audio_metadata(audio_path: str | Path) -> dict[str, Any]:
    """
    Extracts container and stream metadata from audio files:
    - Sample rate, channels, bit depth, duration, sample count
    - File SHA-256 digest
    """
    path = Path(audio_path)
    sample_rate = 0
    channels = 0
    sample_count = 0
    duration_seconds = 0.0
    bit_depth = 16

    # Attempt to read WAV parameters using Python's standard wave library
    try:
        with wave.open(str(path), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_count = wf.getnframes()
            sampwidth = wf.getsampwidth()
            bit_depth = sampwidth * 8
            duration_seconds = round(sample_count / sample_rate, 3) if sample_rate > 0 else 0.0
    except Exception:
        # Fallback to scipy.io.wavfile
        try:
            sr, data = wavfile.read(str(path))
            sample_rate = int(sr)
            channels = 1 if data.ndim == 1 else int(data.shape[1])
            sample_count = len(data)
            duration_seconds = round(sample_count / sample_rate, 3) if sample_rate > 0 else 0.0
            bit_depth = data.dtype.itemsize * 8
        except Exception as exc:
            raise ValueError(f"Could not parse audio metadata: {exc}") from exc

    # Calculate SHA-256 hash
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    # Forensic observation on sample rate
    typical_ai_sample_rates = {16000, 22050, 24000}
    is_common_tts_rate = sample_rate in typical_ai_sample_rates

    return {
        "filename": path.name,
        "file_size_bytes": path.stat().st_size,
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "channel_layout": "mono" if channels == 1 else "stereo" if channels == 2 else f"{channels}-channel",
        "bit_depth": bit_depth,
        "total_samples": sample_count,
        "duration_seconds": duration_seconds,
        "is_common_tts_sample_rate": is_common_tts_rate,
        "sha256": digest.hexdigest(),
        "limitations": [
            "Metadata headers can be easily rewritten using standard audio conversion utilities.",
            "Common TTS sample rates (16kHz / 22.05kHz / 24kHz) are also widely used by telecom and VoIP systems.",
        ],
    }
