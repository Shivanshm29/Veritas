"""
Integration tests for POST /api/v1/video/analyze.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

ANALYZE_URL = "/api/v1/video/analyze"


def _create_dummy_video(target_path: Path, num_frames: int = 15, width: int = 120, height: int = 120) -> Path:
    """Creates a small valid MP4 video with simple motion for testing."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(target_path), fourcc, 10.0, (width, height))
    for i in range(num_frames):
        # Create frames with changing patterns
        frame = np.full((height, width, 3), (i * 12) % 255, dtype=np.uint8)
        # Draw a moving circle
        cv2.circle(frame, (20 + (i * 5) % 80, 50), 15, (0, 255, 0), -1)
        out.write(frame)
    out.release()
    return target_path


def test_rejects_empty_video_upload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.video as video_ep
    monkeypatch.setattr(video_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("empty.mp4", b"", "video/mp4")},
    )
    assert response.status_code == 400
    assert "empty" in response.text.lower()


def test_rejects_corrupted_video(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.video as video_ep
    monkeypatch.setattr(video_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("corrupt.mp4", b"not a valid video content", "video/mp4")},
    )
    assert response.status_code == 400
    assert "corrupted" in response.text.lower() or "not a recognized" in response.text.lower()


def test_rejects_unsupported_video_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.video as video_ep
    monkeypatch.setattr(video_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("clip.flv", b"dummy flv header", "video/x-flv")},
    )
    assert response.status_code == 415
    assert "unsupported" in response.text.lower()


def test_analyze_valid_video_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Full pipeline integration test on a generated valid MP4."""
    import backend.app.api.v1.endpoints.video as video_ep
    monkeypatch.setattr(video_ep, "ARTIFACTS_ROOT", tmp_path)

    dummy_video_path = _create_dummy_video(tmp_path / "test_sample.mp4")

    with dummy_video_path.open("rb") as f:
        response = client.post(
            ANALYZE_URL,
            files={"file": ("test_sample.mp4", f, "video/mp4")},
        )

    assert response.status_code == 200
    data = response.json()

    assert data["analysis_id"]
    assert data["timestamp"]
    assert data["status"] in {"completed", "partial"}
    assert "original" in data["artifact_paths"]

    # Verify all expected detectors ran
    detector_names = {finding["detector_name"] for finding in data["findings"]}
    expected_detectors = {
        "video_metadata_analysis",
        "keyframe_extraction",
        "temporal_consistency_analysis",
        "deepfake_face_detection",
        "spectral_frequency_analysis",
        "c2pa_credential_validation",
    }
    assert expected_detectors.issubset(detector_names)

    # Check metadata details
    meta_finding = next(f for f in data["findings"] if f["detector_name"] == "video_metadata_analysis")
    assert meta_finding["result_details"]["width"] == 120
    assert meta_finding["result_details"]["height"] == 120
    assert meta_finding["result_details"]["frame_count"] == 15

    # Check temporal consistency details
    temporal_finding = next(f for f in data["findings"] if f["detector_name"] == "temporal_consistency_analysis")
    assert temporal_finding["status"] == "completed"
    assert "mean_frame_difference" in temporal_finding["result_details"]
