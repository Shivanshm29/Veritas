"""
API tests for Veritas Claim Intelligence endpoints (/api/v1/claims).
"""

from fastapi import status
import pytest


def test_extract_claims_basic(client):
    payload = {
        "text": "The Ministry of Health announced a nationwide vaccination campaign on October 15, 2026.",
        "investigation_id": "inv_12345678-1234-4234-8234-123456789abc",
    }
    response = client.post("/api/v1/claims/extract", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["detected_language"] == "en"
    assert data["total_claims"] == 1
    assert len(data["claims"]) == 1

    claim = data["claims"][0]
    assert claim["id"].startswith("clm_")
    assert claim["investigation_id"] == payload["investigation_id"]
    assert claim["category"] == "PUBLIC_HEALTH"
    assert claim["source_char_start"] is not None
    assert claim["source_char_end"] is not None
    assert payload["text"][claim["source_char_start"]:claim["source_char_end"]] == claim["claim_text"]


def test_extract_claims_multilingual_hindi(client):
    payload = {
        "text": "भारतीय रिजर्व बैंक ने आज रेपो दर में 25 आधार अंकों की वृद्धि की घोषणा की।",
    }
    response = client.post("/api/v1/claims/extract", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["detected_language"] == "hi"
    assert data["total_claims"] == 1
    claim = data["claims"][0]
    assert claim["language"] == "hi"


def test_extract_claims_with_abstentions_and_warnings(client):
    payload = {
        "text": "Good morning everyone! Did the minister resign? The treasury confirmed the tax cut yesterday.",
    }
    response = client.post("/api/v1/claims/extract", json=payload)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # 1 factual claim extracted
    assert data["total_claims"] == 1
    assert "treasury confirmed" in data["claims"][0]["claim_text"].lower()

    # Greetings and questions preserved in unprocessed_segments
    assert len(data["unprocessed_segments"]) >= 2
    reasons = [u["reason"].lower() for u in data["unprocessed_segments"]]
    assert any("greeting" in r or "fragment" in r for r in reasons)
    assert any("interrogative" in r or "question" in r for r in reasons)


def test_extract_claims_empty_text_rejected(client):
    response = client.post("/api/v1/claims/extract", json={"text": "   "})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    problem = response.json()
    assert problem["code"] == "EMPTY_TEXT"


def test_extract_claims_with_database_persistence(client):
    inv_id = "inv_aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
    payload = {
        "text": "The state governor signed the education funding bill on Monday.",
        "investigation_id": inv_id,
        "persist": True,
    }
    response = client.post("/api/v1/claims/extract", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_claims"] == 1
    claim_id = data["claims"][0]["id"]

    # Verify claim can now be fetched by GET /api/v1/claims/{claim_id}
    get_res = client.get(f"/api/v1/claims/{claim_id}")
    assert get_res.status_code == status.HTTP_200_OK
    persisted = get_res.json()
    assert persisted["id"] == claim_id
    assert persisted["investigation_id"] == inv_id


def test_get_claim_not_found(client):
    missing_id = "clm_99999999-9999-4999-8999-999999999999"
    response = client.get(f"/api/v1/claims/{missing_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    problem = response.json()
    assert problem["code"] == "RESOURCE_NOT_FOUND"


def test_get_claim_invalid_id_format(client):
    response = client.get("/api/v1/claims/invalid-claim-id")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    problem = response.json()
    assert problem["code"] == "INVALID_IDENTIFIER"


def test_extract_from_asset_not_found(client):
    missing_asset_id = "ast_88888888-8888-4888-8888-888888888888"
    payload = {"text": "The report states that revenue increased by 10%."}
    response = client.post(f"/api/v1/claims/extract-from-asset/{missing_asset_id}", json=payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    problem = response.json()
    assert problem["code"] == "RESOURCE_NOT_FOUND"


def test_list_claims_filter(client):
    inv_id = "inv_bbbbbbbb-cccc-4ddd-8eee-ffffffffffff"
    payload = {
        "text": "The hospital confirmed 50 patients recovered today.",
        "investigation_id": inv_id,
        "persist": True,
    }
    client.post("/api/v1/claims/extract", json=payload)

    # Filter by investigation_id
    list_res = client.get(f"/api/v1/claims?investigation_id={inv_id}")
    assert list_res.status_code == status.HTTP_200_OK
    claims = list_res.json()
    assert len(claims) >= 1
    assert claims[0]["investigation_id"] == inv_id
