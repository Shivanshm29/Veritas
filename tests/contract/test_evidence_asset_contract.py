"""
Contract conformance test for EvidenceAsset API responses.
"""

import io
import json
from pathlib import Path
import pytest
from contracts.schemas.models import EvidenceAsset

JPEG_HEADER = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 64


def test_uploaded_asset_conforms_to_contract_and_schema(client):
    """Verifies API response parses into EvidenceAsset and conforms to contract specification."""
    response = client.post(
        "/api/v1/assets/upload",
        files={"file": ("contract_test.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")},
    )
    assert response.status_code == 201
    payload = response.json()

    # 1. Pydantic contract validation (checks all types, regex patterns, prefixes, bounds)
    model = EvidenceAsset.model_validate(payload)
    assert model.id.startswith("ast_")
    assert model.investigation_id.startswith("inv_")
    assert len(model.sha256_hash) == 64
    assert model.storage_uri.startswith("file://")
    assert model.mime_type == "image/jpeg"
    assert model.file_size_bytes == len(JPEG_HEADER)

    # 2. Schema properties alignment
    schema_path = Path("contracts/schemas/json/EvidenceAsset.json")
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        for required_prop in schema.get("required", []):
            assert required_prop in payload, f"Missing required contract property '{required_prop}'"
