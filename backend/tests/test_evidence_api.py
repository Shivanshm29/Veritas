"""
API tests for Veritas Source Intelligence & Evidence Retrieval endpoints (/api/v1/evidence).
"""

from datetime import datetime, timezone
from fastapi import status
import pytest
from sqlalchemy.orm import Session

from backend.app.db.base import Base
import backend.app.db.models  # noqa: F401
from backend.app.db.models.claim import ClaimRecord
from backend.app.db.repositories.claim import ClaimRepository
from backend.app.db.session import engine, SessionLocal


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_retrieve_evidence_from_text(client):
    payload = {
        "query_text": "The Federal Reserve raised interest rates by 0.5% in September 2026.",
        "max_results": 5,
        "persist": False,
    }
    response = client.post("/api/v1/evidence/retrieve", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["query_text"] == payload["query_text"]
    assert data["total_sources"] > 0
    assert data["total_evidence_items"] > 0
    assert len(data["source_documents"]) > 0
    assert len(data["evidence_items"]) > 0

    first_source = data["source_documents"][0]
    assert first_source["id"].startswith("doc_")
    assert first_source["content_sha256"] is not None
    assert first_source["is_simulated"] is True

    first_item = data["evidence_items"][0]
    assert first_item["id"].startswith("evi_")
    assert first_item["source_document_id"] == first_source["id"]
    assert 0.0 <= first_item["relevance_score"] <= 1.0
    assert first_item["page_number"] is None


def test_retrieve_evidence_with_persistence_and_lookups(client):
    payload = {
        "query_text": "The Ministry of Health confirmed 1,200 new cases of the virus across the capital on Monday.",
        "max_results": 5,
        "persist": True,
    }
    response = client.post("/api/v1/evidence/retrieve", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    source_id = data["source_documents"][0]["id"]
    evidence_id = data["evidence_items"][0]["id"]

    # 1. Lookup source document by ID
    src_res = client.get(f"/api/v1/evidence/sources/{source_id}")
    assert src_res.status_code == status.HTTP_200_OK
    src_data = src_res.json()
    assert src_data["id"] == source_id
    assert src_data["is_simulated"] is True
    assert "moh.gov.example" in src_data["domain"]

    # 2. Lookup evidence item by ID
    evi_res = client.get(f"/api/v1/evidence/{evidence_id}")
    assert evi_res.status_code == status.HTTP_200_OK
    evi_data = evi_res.json()
    assert evi_data["id"] == evidence_id
    assert evi_data["source_document_id"] == source_id

    # 3. List evidence items with filter
    list_res = client.get(f"/api/v1/evidence?source_document_id={source_id}")
    assert list_res.status_code == status.HTTP_200_OK
    list_data = list_res.json()
    assert len(list_data) >= 1
    assert any(i["id"] == evidence_id for i in list_data)


def test_retrieve_evidence_for_persisted_claim(client):
    db: Session = SessionLocal()
    claim_id = "clm_abcdef12-3456-4789-a012-3456789abcde"
    try:
        claim_repo = ClaimRepository(db)
        record = ClaimRecord(
            id=claim_id,
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            claim_text="Earthquake of magnitude 6.8 struck coastal regions yesterday morning.",
            modality_origin="USER_PROMPT",
            extraction_confidence=0.9,
            status="EXTRACTED",
            category="DISASTER",
            created_at=datetime.now(timezone.utc),
        )
        claim_repo.create(record)
    finally:
        db.close()

    # Retrieve for this claim
    response = client.post(f"/api/v1/evidence/retrieve-for-claim/{claim_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["claim_id"] == claim_id
    assert len(data["evidence_items"]) > 0
    assert all(i["claim_id"] == claim_id for i in data["evidence_items"])


def test_retrieve_for_nonexistent_claim_returns_404(client):
    missing_id = "clm_ffffffff-ffff-4fff-bfff-ffffffffffff"
    response = client.post(f"/api/v1/evidence/retrieve-for-claim/{missing_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_invalid_identifiers_return_422(client):
    # Invalid claim ID format in retrieve-for-claim
    bad_res1 = client.post("/api/v1/evidence/retrieve-for-claim/not-a-valid-claim-id")
    assert bad_res1.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Invalid source document ID format
    bad_res2 = client.get("/api/v1/evidence/sources/invalid_source_id")
    assert bad_res2.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Invalid evidence item ID format
    bad_res3 = client.get("/api/v1/evidence/invalid_evidence_id")
    assert bad_res3.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_empty_query_returns_error(client):
    payload = {"query_text": "   ", "persist": False}
    response = client.post("/api/v1/evidence/retrieve", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
