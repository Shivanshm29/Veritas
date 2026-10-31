"""
Integration & unit tests for Module 8: Provenance & Historical Media Matching.
"""

from io import BytesIO
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from backend.app.schemas.provenance import (
    MatchGrade,
    MediaFingerprint,
    ProvenanceEdge,
    ProvenanceNode,
)
from backend.app.services.provenance.graph_builder import (
    build_provenance_graph,
    detect_cycles_in_graph,
)
from backend.app.services.provenance.hasher import (
    compute_ahash,
    compute_dhash,
    compute_image_fingerprint,
    compute_phash,
    hamming_distance,
)
from backend.app.services.provenance.matcher import match_against_historical_references
from backend.app.services.provenance.reference_store import (
    HistoricalReferenceStore,
    ReferenceMediaItem,
)

client = TestClient(app)


def _generate_test_image_bytes(color: tuple = (100, 150, 200), width: int = 64, height: int = 64) -> bytes:
    buf = BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Unit Tests: Hasher & Distance
# ---------------------------------------------------------------------------
def test_hasher_phash_determinism():
    """Identical images must yield identical perceptual hashes."""
    img = np.full((64, 64, 3), 128, dtype=np.uint8)
    cv2.circle(img, (32, 32), 16, (255, 0, 0), -1)

    h1 = compute_phash(img)
    h2 = compute_phash(img)
    assert h1 == h2
    assert len(h1) == 16  # 64 bits = 16 hex characters
    assert hamming_distance(h1, h2) == 0


def test_hasher_resizing_and_compression_resistance():
    """Near-duplicate recompressed/resized images must produce low Hamming distance (<= 5)."""
    img1 = np.zeros((120, 120, 3), dtype=np.uint8)
    cv2.circle(img1, (60, 60), 35, (255, 255, 255), -1)

    # Resize slightly and recompress
    img2 = cv2.resize(img1, (80, 80), interpolation=cv2.INTER_AREA)

    h1 = compute_phash(img1)
    h2 = compute_phash(img2)
    dist = hamming_distance(h1, h2)
    assert dist <= 5, f"Hamming distance {dist} exceeds expected near-duplicate threshold 5"


def test_hasher_dissimilar_images_have_large_distance():
    """Completely different image structures must produce high Hamming distance."""
    # Pattern 1: Vertical stripes
    img1 = np.zeros((64, 64, 3), dtype=np.uint8)
    img1[:, ::4] = 255

    # Pattern 2: Concentric circle
    img2 = np.zeros((64, 64, 3), dtype=np.uint8)
    cv2.circle(img2, (32, 32), 20, (255, 255, 255), -1)

    h1 = compute_phash(img1)
    h2 = compute_phash(img2)
    assert hamming_distance(h1, h2) >= 12


# ---------------------------------------------------------------------------
# Unit Tests: Matcher & Origin Rules
# ---------------------------------------------------------------------------
def test_matching_distinguishes_verified_from_tentative():
    """
    Acceptance Rule:
    Distinguish verified relationships from tentative similarity matches.
    Avoid treating visual similarity alone as proof of common origin.
    """
    custom_store = HistoricalReferenceStore()
    ref = ReferenceMediaItem(
        id="ref_test_001",
        title="Test Reference",
        source_url="https://example.com/original.jpg",
        publisher="Reuters",
        original_published_date="2021-01-01T00:00:00Z",
        sha256_hash="0000000000000000000000000000000000000000000000000000000000000000",
        phash="ffff0000ffff0000",
        dhash="ffff0000ffff0000",
        ahash="ffff0000ffff0000",
        description="Reference test asset",
    )
    custom_store.add_reference(ref)

    # 1. Exact match test
    fp_exact = MediaFingerprint(
        phash="ffff0000ffff0000",
        dhash="ffff0000ffff0000",
        ahash="ffff0000ffff0000",
        color_fingerprint="00000000",
    )
    res_exact = match_against_historical_references(fp_exact, "sha_exact", store=custom_store)
    assert res_exact.matches_found == 1
    assert res_exact.matches[0].match_grade == MatchGrade.EXACT
    assert res_exact.matches[0].is_confirmed_origin is True

    # 2. Near-duplicate match test (Hamming distance = 2)
    # Flip 2 bits in hex: 0 -> 3 (0011 in binary)
    fp_near = MediaFingerprint(
        phash="ffff0000ffff0003",
        dhash="ffff0000ffff0003",
        ahash="ffff0000ffff0000",
        color_fingerprint="00000000",
    )
    res_near = match_against_historical_references(fp_near, "sha_near", store=custom_store)
    assert res_near.matches_found == 1
    assert res_near.matches[0].match_grade == MatchGrade.NEAR_DUPLICATE
    assert res_near.matches[0].is_confirmed_origin is True

    # 3. Tentative match test (Hamming distance = 8)
    # Flip 8 bits: 0000 -> 00ff
    fp_tentative = MediaFingerprint(
        phash="ffff0000ffff00ff",
        dhash="ffff0000ffff00ff",
        ahash="ffff0000ffff0000",
        color_fingerprint="00000000",
    )
    res_tentative = match_against_historical_references(fp_tentative, "sha_tentative", store=custom_store)
    assert res_tentative.matches_found == 1
    assert res_tentative.matches[0].match_grade == MatchGrade.TENTATIVE_SIMILAR
    # Crucial acceptance criteria: visual similarity is NOT treated as proof of origin
    assert res_tentative.matches[0].is_confirmed_origin is False


# ---------------------------------------------------------------------------
# Unit Tests: Graph Builder & Multi-Hop Cycle Detection
# ---------------------------------------------------------------------------
def test_graph_cycle_detection_valid_dag():
    """A linear derivation chain (Asset -> Keyframe -> Crop) must be a valid DAG."""
    edges = [
        ProvenanceEdge(id="e1", source="ast_video", target="ast_keyframe", relationship_type="DERIVED_FROM", confidence=1.0, basis="Keyframe extracted"),
        ProvenanceEdge(id="e2", source="ast_keyframe", target="ast_face_crop", relationship_type="DERIVED_FROM", confidence=0.95, basis="Face bounded crop"),
    ]
    has_cycle, path = detect_cycles_in_graph(edges)
    assert has_cycle is False
    assert len(path) == 0


def test_graph_multi_hop_cycle_detection():
    """Multi-hop circular derivation loop (A -> B -> C -> A) must be detected and rejected."""
    edges = [
        ProvenanceEdge(id="e1", source="node_a", target="node_b", relationship_type="DERIVED_FROM", confidence=1.0, basis="A to B"),
        ProvenanceEdge(id="e2", source="node_b", target="node_c", relationship_type="DERIVED_FROM", confidence=1.0, basis="B to C"),
        ProvenanceEdge(id="e3", source="node_c", target="node_a", relationship_type="DERIVED_FROM", confidence=1.0, basis="C back to A loop"),
    ]
    has_cycle, path = detect_cycles_in_graph(edges)
    assert has_cycle is True
    assert "node_a" in path


# ---------------------------------------------------------------------------
# Integration Tests: Endpoints
# ---------------------------------------------------------------------------
def test_api_list_historical_references():
    res = client.get("/api/v1/provenance/references")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert any(ref["id"] == "ref_hist_2020_001" for ref in data)


def test_api_generate_media_fingerprint():
    img_bytes = _generate_test_image_bytes()
    res = client.post(
        "/api/v1/provenance/fingerprint",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert "phash" in data
    assert "dhash" in data
    assert "ahash" in data
    assert len(data["phash"]) == 16


def test_api_match_via_phash_query():
    # Query with exact seed reference pHash
    seed_phash = "9c3a6e8f1b2d4c7a"
    res = client.post(f"/api/v1/provenance/match?phash={seed_phash}")
    assert res.status_code == 200
    data = res.json()
    assert data["matches_found"] >= 1
    assert data["matches"][0]["reference_id"] == "ref_hist_2020_001"
    assert data["matches"][0]["match_grade"] == "EXACT"


def test_api_graph_validation():
    payload = {
        "investigation_id": "inv_12345678-1234-4234-8234-123456789abc",
        "nodes": [
            {"id": "ast_1", "type": "ASSET", "label": "Original Video"},
            {"id": "ast_2", "type": "DERIVATION", "label": "Keyframe 1"},
        ],
        "edges": [
            {"id": "rel_1", "source": "ast_1", "target": "ast_2", "relationship_type": "DERIVED_FROM", "confidence": 1.0, "basis": "Extracted frame"}
        ],
    }
    res = client.post("/api/v1/provenance/graph/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_dag"] is True
    assert data["cycle_detected"] is False
    assert len(data["nodes"]) == 2
