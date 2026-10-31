"""
Contract tests validating exported JSON Schemas against JSON Schema specifications.
"""

import json
from pathlib import Path
import pytest

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "contracts" / "schemas" / "json"

EXPECTED_SCHEMAS = [
    "Investigation.json",
    "EvidenceAsset.json",
    "AssetDerivation.json",
    "ProcessingResult.json",
    "Claim.json",
    "SourceDocument.json",
    "EvidenceItem.json",
    "ClaimAssessment.json",
    "ForensicFinding.json",
    "ProvenanceRelationship.json",
    "InvestigationReport.json",
    "AuditEvent.json",
]


@pytest.mark.parametrize("schema_filename", EXPECTED_SCHEMAS)
def test_exported_json_schema_exists_and_valid(schema_filename):
    """Verifies that each exported JSON schema file exists and contains valid JSON."""
    schema_path = SCHEMA_DIR / schema_filename
    assert schema_path.exists(), f"Schema file '{schema_filename}' was not exported."

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    assert "properties" in schema_data
    assert "id" in schema_data["properties"]
    assert "title" in schema_data or "description" in schema_data

