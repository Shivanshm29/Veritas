"""
API endpoint integration tests for Veritas Phase 1 Evidence Asset Ingestion.
"""

import io
import pytest
from fastapi import status


JPEG_HEADER = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 64
PNG_HEADER = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 32
MP4_HEADER = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00" + b"\x00" * 32


def test_upload_valid_jpeg(client):
    """Test successful multipart upload of a valid JPEG asset."""
    file_payload = ("test_image.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
        data={"source_platform": "twitter"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["id"].startswith("ast_")
    assert data["investigation_id"].startswith("inv_")
    assert data["original_filename"] == "test_image.jpg"
    assert data["mime_type"] == "image/jpeg"
    assert data["file_size_bytes"] == len(JPEG_HEADER)
    assert len(data["sha256_hash"]) == 64
    assert data["storage_uri"].startswith("file://")
    assert data["status"] == "STORED"
    assert data["c2pa_status"] == "ABSENT"


def test_upload_with_explicit_investigation_id(client):
    """Test asset upload attached to a specific investigation."""
    valid_inv_id = "inv_12345678-1234-4234-8234-123456789abc"
    file_payload = ("clip.mp4", io.BytesIO(MP4_HEADER), "video/mp4")
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
        data={"investigation_id": valid_inv_id},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["investigation_id"] == valid_inv_id
    assert data["mime_type"] == "video/mp4"


def test_upload_with_invalid_investigation_id(client):
    """Test rejection with HTTP 422 Problem Details when investigation_id is malformed."""
    file_payload = ("test.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
        data={"investigation_id": "malformed_inv_id"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    problem = response.json()
    assert problem["code"] == "INVALID_IDENTIFIER"
    assert "Expected format: 'inv_<uuid4>'" in problem["detail"]


def test_upload_empty_file_rejected(client):
    """Test rejection with HTTP 400 Problem Details for 0-byte file."""
    file_payload = ("empty.jpg", io.BytesIO(b""), "image/jpeg")
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    problem = response.json()
    assert problem["code"] == "EMPTY_FILE"


def test_upload_executable_rejected(client):
    """Test rejection with HTTP 400 Problem Details for executable payload."""
    exe_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00"
    file_payload = ("malware.exe", io.BytesIO(exe_payload), "application/octet-stream")
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    problem = response.json()
    assert problem["code"] == "INVALID_ASSET"
    assert "Executable binary uploads" in problem["detail"]


def test_upload_spoofed_mime_type_rejected(client):
    """Test rejection when declared MIME does not match magic bytes."""
    file_payload = ("sneaky.jpg", io.BytesIO(PNG_HEADER), "image/jpeg")
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    problem = response.json()
    assert problem["code"] == "INVALID_ASSET"
    assert "MIME type mismatch" in problem["detail"]


def test_get_asset_success(client):
    """Test retrieving existing asset by its ID."""
    file_payload = ("retrieval_test.png", io.BytesIO(PNG_HEADER), "image/png")
    upload_res = client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    asset_id = upload_res.json()["id"]

    get_res = client.get(f"/api/v1/assets/{asset_id}")
    assert get_res.status_code == status.HTTP_200_OK
    data = get_res.json()
    assert data["id"] == asset_id
    assert data["original_filename"] == "retrieval_test.png"
    assert data["mime_type"] == "image/png"


def test_get_asset_not_found(client):
    """Test 404 Problem Details when requesting non-existent asset."""
    missing_id = "ast_99999999-9999-4999-8999-999999999999"
    response = client.get(f"/api/v1/assets/{missing_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    problem = response.json()
    assert problem["code"] == "RESOURCE_NOT_FOUND"
    assert missing_id in problem["detail"]


def test_get_asset_invalid_id_format(client):
    """Test 422 Problem Details when asset ID has invalid format."""
    response = client.get("/api/v1/assets/not-a-valid-uuid")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    problem = response.json()
    assert problem["code"] == "INVALID_IDENTIFIER"


def test_list_assets_filter(client):
    """Test listing assets filtered by investigation ID."""
    inv_id = "inv_aabbccdd-1122-4334-8556-aabbccddeeff"
    file_payload = ("sample1.png", io.BytesIO(PNG_HEADER), "image/png")
    client.post(
        "/api/v1/assets/upload",
        files={"file": file_payload},
        data={"investigation_id": inv_id},
    )

    response = client.get(f"/api/v1/assets?investigation_id={inv_id}")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) >= 1
    assert all(item["investigation_id"] == inv_id for item in items)


def test_upload_duplicate_file_creates_distinct_asset_records(client):
    """
    Verifies that uploading the exact same binary content twice creates distinct
    EvidenceAsset records with distinct IDs while preserving the identical sha256_hash.
    """
    file_payload1 = ("duplicate_a.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")
    res1 = client.post("/api/v1/assets/upload", files={"file": file_payload1})
    assert res1.status_code == status.HTTP_201_CREATED
    data1 = res1.json()

    file_payload2 = ("duplicate_b.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")
    res2 = client.post("/api/v1/assets/upload", files={"file": file_payload2})
    assert res2.status_code == status.HTTP_201_CREATED
    data2 = res2.json()

    assert data1["id"] != data2["id"]
    assert data1["sha256_hash"] == data2["sha256_hash"]
    assert data1["storage_uri"] != data2["storage_uri"]
