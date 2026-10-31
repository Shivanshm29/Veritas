"""
API tests for Evidence-Based Claim Verification Endpoints (Phase 4).
"""

from uuid import uuid4
from fastapi.testclient import TestClient


def test_classify_stance_api(client: TestClient):
    payload = {
        "claim_text": "Drinking seawater cures COVID-19.",
        "evidence_text": "The World Health Organization confirmed that claims suggesting seawater cures COVID-19 are false and dangerous.",
    }
    response = client.post("/api/v1/verification/stance", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["stance"] in ("CONTRADICTS", "REFUTES")
    assert data["confidence"] >= 0.70
    assert "rationale" in data
    assert "epistemic_disclaimer" in data


def test_verify_claim_by_text_api(client: TestClient):
    payload = {
        "claim_text": "NASA's James Webb Space Telescope detected atmospheric water vapor on exoplanet WASP-96b.",
        "persist": False,
    }
    response = client.post("/api/v1/verification/verify-claim", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "assessment" in data
    assessment = data["assessment"]
    assert assessment["id"].startswith("asm_")
    assert assessment["verdict"] in ["SUPPORTED", "INSUFFICIENT_EVIDENCE", "REFUTED", "CONTRADICTORY_EVIDENCE"]
    assert 0.0 <= assessment["confidence_score"] <= 1.0
    assert len(assessment["explanation"]) >= 20
    assert "execution_time_ms" in data


def test_verify_claim_empty_input_fails(client: TestClient):
    payload = {}
    response = client.post("/api/v1/verification/verify-claim", json=payload)
    assert response.status_code == 400


def test_verify_claim_invalid_id_format_fails(client: TestClient):
    payload = {"claim_id": "invalid_id_format"}
    response = client.post("/api/v1/verification/verify-claim", json=payload)
    assert response.status_code == 422


def test_verify_claim_nonexistent_id_returns_404(client: TestClient):
    payload = {"claim_id": f"clm_{uuid4()}"}
    response = client.post("/api/v1/verification/verify-claim", json=payload)
    assert response.status_code == 404


def test_verify_claim_with_persisted_flow(client: TestClient):
    # 1. Extract and persist claim
    extract_payload = {
        "text": "The Ministry confirmed that healthcare subsidies will expand by ten percent next year.",
        "investigation_id": f"inv_{uuid4()}",
        "persist": True,
    }
    extract_resp = client.post("/api/v1/claims/extract", json=extract_payload)
    assert extract_resp.status_code == 200
    claims = extract_resp.json()["claims"]
    assert len(claims) > 0
    claim_id = claims[0]["id"]

    # 2. Verify the persisted claim
    verify_payload = {
        "claim_id": claim_id,
        "persist": True,
    }
    verify_resp = client.post("/api/v1/verification/verify-claim", json=verify_payload)
    assert verify_resp.status_code == 200
    asm = verify_resp.json()["assessment"]
    assert asm["claim_id"] == claim_id
    asm_id = asm["id"]

    # 3. Lookup assessment by assessment_id
    get_asm_resp = client.get(f"/api/v1/verification/assessments/{asm_id}")
    assert get_asm_resp.status_code == 200
    assert get_asm_resp.json()["id"] == asm_id

    # 4. Lookup assessments for claim_id
    by_claim_resp = client.get(f"/api/v1/verification/assessments/claim/{claim_id}")
    assert by_claim_resp.status_code == 200
    assert len(by_claim_resp.json()) >= 1

    # 5. List assessments with filter
    list_resp = client.get("/api/v1/verification/assessments", params={"claim_id": claim_id})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_get_assessment_not_found(client: TestClient):
    fake_id = f"asm_{uuid4()}"
    response = client.get(f"/api/v1/verification/assessments/{fake_id}")
    assert response.status_code == 404


def test_get_assessment_invalid_id_format(client: TestClient):
    response = client.get("/api/v1/verification/assessments/bad-format")
    assert response.status_code == 422
