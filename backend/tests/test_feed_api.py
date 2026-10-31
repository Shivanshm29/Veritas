"""
Integration tests for Mode A (oEmbed URL Audit) and Mode B (Live Social Feed Radar).
"""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_get_live_social_feed():
    """Verify Mode B returns live stream items with virality telemetry."""
    response = client.get("/api/v1/feed/live?include_live_network=false")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    first_item = data[0]
    assert "id" in first_item
    assert "platform" in first_item
    assert "virality_score" in first_item
    assert "shares_per_minute" in first_item
    assert "is_viral_spike" in first_item
    assert 0.0 <= first_item["virality_score"] <= 1.0


def test_trigger_viral_spike():
    """Verify Mode B demo trigger injects an urgent viral spike."""
    response = client.post("/api/v1/feed/trigger-spike?custom_claim=Emergency%20deepfake%20broadcast%20detected")
    assert response.status_code == 200
    data = response.json()
    assert data["is_viral_spike"] is True
    assert data["virality_score"] >= 0.90
    assert "Emergency deepfake" in data["content"]

    # Verify it now appears in the live stream
    feed_res = client.get("/api/v1/feed/live?include_live_network=false")
    feed_data = feed_res.json()
    assert feed_data[0]["id"] == data["id"]


def test_resolve_social_url():
    """Verify Mode A URL resolver identifies platforms and normalizes structure."""
    payload = {"url": "https://x.com/WHO/status/1635678901234567890"}
    response = client.post("/api/v1/feed/resolve-url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "X / Twitter"
    assert "url" in data


def test_audit_feed_post_pipeline():
    """Verify Mode B one-click audit executes the unified pipeline."""
    payload = {
        "item_id": "post_live_x_001",
        "feed_item": {
            "id": "post_live_x_001",
            "platform": "X / Twitter",
            "author": "Geopolitics Wire",
            "title": "Alleged leaked diplomatic audio reveals secret defense alliance",
            "content": "A leaked high-level audio recording allegedly captures foreign ministry officials agreeing to secret bilateral defense terms.",
            "media_url": None,
            "media_type": "text",
            "virality_score": 0.94,
            "shares_per_minute": 4200,
            "total_impressions": 184000,
            "is_viral_spike": True,
            "posted_at": "2026-10-31T12:00:00Z",
            "source_url": "https://twitter.com/GeoWireGlobal/status/1789012345678901234",
        },
    }
    response = client.post("/api/v1/feed/audit-post", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["investigation_id"].startswith("inv_")
    assert data["status"] == "COMPLETED"
    assert data["mode"] == "LIVE_FEED_RADAR"
    assert "verdict_summary" in data
    assert len(data["verdict_summary"]) > 10


def test_audit_url_pipeline():
    """Verify Mode A URL audit executes the unified pipeline."""
    payload = {"url": "https://x.com/WHO/status/1635678901234567890"}
    response = client.post("/api/v1/feed/audit-url", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["investigation_id"].startswith("inv_")
    assert data["status"] == "COMPLETED"
    assert data["mode"] == "URL_AUDIT"
    assert "verdict_summary" in data
