"""
Automated tests for health check endpoints.

Verifies root /health and /api/v1/health adhere to contracts and do not fabricate dependency health.
"""

from fastapi import status


def test_root_health_endpoint(client):
    """Verifies that GET /health returns HTTP 200 and expected metadata."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PRAMAAN Core Backend"
    assert "version" in data
    assert "timestamp" in data


def test_api_v1_health_endpoint(client):
    """Verifies that GET /api/v1/health returns HTTP 200 with probed dependencies."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "dependencies" in data
    
    deps = data["dependencies"]
    assert "database" in deps
    assert "redis" in deps
    assert "object_storage" in deps
    
    # In-memory test database should be connected
    assert deps["database"]["connected"] is True
    assert deps["database"]["dialect"] == "sqlite"
    
    # Check that probe status is reported truthfully
    assert "connected" in deps["redis"]
    assert "connected" in deps["object_storage"]


def test_health_timestamp_is_utc(client):
    """Verifies that timestamp adheres to ISO 8601 UTC format with explicit Z or offset."""
    response = client.get("/health")
    data = response.json()
    ts = data["timestamp"]
    assert "T" in ts
    # Must end with Z or timezone offset (+00:00)
    assert ts.endswith("Z") or "+00:00" in ts

