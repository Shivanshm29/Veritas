"""
Integration tests for POST /api/v1/audio/analyze.
"""

import wave
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

ANALYZE_URL = "/api/v1/audio/analyze"


def _create_dummy_wav(target_path: Path, duration_seconds: float = 1.0, sample_rate: int = 22050) -> Path:
    """Creates a valid 16-bit PCM WAV audio file containing a compound tone."""
    total_samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, total_samples, endpoint=False)
    # Generate 440 Hz (A4) + 880 Hz harmonic
    audio = 0.6 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 880 * t)
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(str(target_path), "wb") as wf:
        wf.setnchannels(1)  # Mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    return target_path


def test_rejects_empty_audio_upload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.audio as audio_ep
    monkeypatch.setattr(audio_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("empty.wav", b"", "audio/wav")},
    )
    assert response.status_code == 400
    assert "empty" in response.text.lower()


def test_rejects_corrupted_audio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.audio as audio_ep
    monkeypatch.setattr(audio_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("corrupt.wav", b"not a valid wav stream header", "audio/wav")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.text.lower() or "not a recognized" in response.text.lower()


def test_rejects_unsupported_audio_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.audio as audio_ep
    monkeypatch.setattr(audio_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("audio.midi", b"dummy midi content", "audio/midi")},
    )
    assert response.status_code == 415
    assert "unsupported" in response.text.lower()


def test_analyze_valid_audio_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Full pipeline integration test on a generated valid WAV audio file."""
    import backend.app.api.v1.endpoints.audio as audio_ep
    monkeypatch.setattr(audio_ep, "ARTIFACTS_ROOT", tmp_path)

    dummy_wav_path = _create_dummy_wav(tmp_path / "test_sample.wav", duration_seconds=1.2, sample_rate=22050)

    with dummy_wav_path.open("rb") as f:
        response = client.post(
            ANALYZE_URL,
            files={"file": ("test_sample.wav", f, "audio/wav")},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["analysis_id"]
    assert data["timestamp"]
    assert data["status"] in {"completed", "partial"}
    assert "original" in data["artifact_paths"]

    # Verify all detectors ran
    detector_names = {finding["detector_name"] for finding in data["findings"]}
    expected_detectors = {
        "audio_metadata_analysis",
        "spectrogram_frequency_analysis",
        "pitch_and_modulation_analysis",
        "splice_and_silence_detection",
        "c2pa_credential_validation",
    }
    assert expected_detectors.issubset(detector_names)

    # Check metadata details
    meta_finding = next(f for f in data["findings"] if f["detector_name"] == "audio_metadata_analysis")
    assert meta_finding["result_details"]["sample_rate_hz"] == 22050
    assert meta_finding["result_details"]["channels"] == 1
    assert meta_finding["result_details"]["duration_seconds"] > 1.0

    # Check spectrogram details
    spec_finding = next(f for f in data["findings"] if f["detector_name"] == "spectrogram_frequency_analysis")
    assert spec_finding["status"] == "completed"
    assert "high_frequency_energy_ratio" in spec_finding["result_details"]
    assert "spectrogram_frequency_analysis.spectrogram_heatmap" in data["artifact_paths"]

    # Check pitch details
    pitch_finding = next(f for f in data["findings"] if f["detector_name"] == "pitch_and_modulation_analysis")
    assert pitch_finding["status"] == "completed"
    assert pitch_finding["result_details"]["mean_pitch_hz"] > 0

    # Check splice details
    splice_finding = next(f for f in data["findings"] if f["detector_name"] == "splice_and_silence_detection")
    assert splice_finding["status"] == "completed"
    assert "splice_and_silence_detection.energy_contour" in data["artifact_paths"]
