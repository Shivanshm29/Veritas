"""
Integration tests for POST /api/v1/image/analyze.

Adapted from the original forge/image_forensics/tests/test_api.py.
"""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.services.image_forensics.ai_detector import detect_ai_image

# ---------------------------------------------------------------------------
# Fixtures & test client
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]   # forge/backend/
SAMPLE_IMAGE = ROOT / "test_images" / "sample.jpg"

client = TestClient(app)

ANALYZE_URL = "/api/v1/image/analyze"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _stub_unavailable(_path):
    return {"status": "unavailable", "details": "stubbed in test"}


def _get_or_create_test_image(target_dir: Path) -> Path:
    """Returns SAMPLE_IMAGE if it exists, otherwise creates a sample JPEG."""
    if SAMPLE_IMAGE.is_file():
        return SAMPLE_IMAGE
    sample_file = target_dir / "generated_sample.jpg"
    img = Image.new("RGB", (250, 250), color=(130, 160, 200))
    img.save(sample_file, format="JPEG")
    return sample_file


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_analyze_real_sample_image(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Full pipeline smoke-test against a real or generated JPEG."""
    import backend.app.api.v1.endpoints.image as image_ep

    monkeypatch.setattr(image_ep, "ARTIFACTS_ROOT", tmp_path)
    monkeypatch.setattr(
        "backend.app.services.image_forensics.analysis.detect_ai_image",
        _stub_unavailable,
    )
    monkeypatch.setattr(
        "backend.app.services.image_forensics.analysis.run_trufor",
        lambda _p, _o: _stub_unavailable(_p),
    )

    image_path = _get_or_create_test_image(tmp_path)
    with image_path.open("rb") as image_file:
        response = client.post(
            ANALYZE_URL,
            files={"file": ("sample.jpg", image_file, "image/jpeg")},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["analysis_id"]
    assert result["timestamp"]
    assert result["status"] in {"completed", "partial"}
    assert all(
        finding["analysis_id"] == result["analysis_id"]
        and finding["timestamp"] == result["timestamp"]
        for finding in result["findings"]
    )
    assert {finding["detector_name"] for finding in result["findings"]} == {
        "metadata_analysis",
        "error_level_analysis",
        "copy_move_heuristic",
        "trufor_forgery_localization",
        "ai_image_classification",
        "c2pa_credential_validation",
    }
    assert all(
        {"status", "result_details", "artifact_paths", "limitations"} <= finding.keys()
        for finding in result["findings"]
    )
    assert Path(result["artifact_paths"]["original"]).is_file()
    assert Path(result["artifact_paths"]["error_level_analysis.heatmap"]).is_file()


def test_rejects_corrupted_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.image as image_ep
    monkeypatch.setattr(image_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("corrupt.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 400


def test_rejects_empty_upload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.app.api.v1.endpoints.image as image_ep
    monkeypatch.setattr(image_ep, "ARTIFACTS_ROOT", tmp_path)

    response = client.post(
        ANALYZE_URL,
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_rejects_unsupported_image_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import backend.app.api.v1.endpoints.image as image_ep
    monkeypatch.setattr(image_ep, "ARTIFACTS_ROOT", tmp_path)

    image_data = BytesIO()
    Image.new("RGB", (2, 2)).save(image_data, format="GIF")
    response = client.post(
        ANALYZE_URL,
        files={"file": ("unsupported.gif", image_data.getvalue(), "image/gif")},
    )
    assert response.status_code == 415


def test_health_endpoint() -> None:
    """Root health probe should return healthy."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_ai_detector_reports_missing_dependencies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AI detector must gracefully surface missing torch/transformers."""

    def missing_model_deps():
        raise ModuleNotFoundError("transformers")

    monkeypatch.setattr(
        "backend.app.services.image_forensics.ai_detector._load_model",
        missing_model_deps,
    )

    image_path = _get_or_create_test_image(tmp_path)
    result = detect_ai_image(image_path)
    assert result["status"] == "unavailable"
    assert "transformers" in result["details"]
