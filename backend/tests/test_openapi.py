"""
Tests for OpenAPI schema generation and validation.
"""

from fastapi import status


def test_openapi_schema_endpoint(client):
    """Verifies that /api/v1/openapi.json is served with valid structure."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "Veritas Core Backend"
    assert "paths" in schema
    assert "/health" in schema["paths"]
    assert "/api/v1/health" in schema["paths"]


def test_docs_endpoints(client):
    """Verifies that Swagger UI and ReDoc return HTTP 200."""
    res_docs = client.get("/api/v1/docs")
    assert res_docs.status_code == status.HTTP_200_OK
    
    res_redoc = client.get("/api/v1/redoc")
    assert res_redoc.status_code == status.HTTP_200_OK

