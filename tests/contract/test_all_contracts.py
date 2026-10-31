"""
Contract tests validating all 12 shared schemas against synthetic fixtures.

Verifies:
1. Every valid fixture strictly passes schema validation.
2. Every invalid fixture is rejected with a pydantic ValidationError.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from contracts.schemas.models import (
    Investigation,
    EvidenceAsset,
    AssetDerivation,
    ProcessingResult,
    Claim,
    SourceDocument,
    EvidenceItem,
    ClaimAssessment,
    ForensicFinding,
    ProvenanceRelationship,
    InvestigationReport,
    AuditEvent,
)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "contracts" / "fixtures"

MODEL_FIXTURE_PAIRS = [
    (Investigation, "valid_investigation.json", "invalid_investigation.json"),
    (EvidenceAsset, "valid_evidence_asset.json", "invalid_evidence_asset.json"),
    (AssetDerivation, "valid_asset_derivation.json", "invalid_asset_derivation.json"),
    (ProcessingResult, "valid_processing_result.json", "invalid_processing_result.json"),
    (Claim, "valid_claim.json", "invalid_claim.json"),
    (SourceDocument, "valid_source_document.json", "invalid_source_document.json"),
    (EvidenceItem, "valid_evidence_item.json", "invalid_evidence_item.json"),
    (ClaimAssessment, "valid_claim_assessment.json", "invalid_claim_assessment.json"),
    (ForensicFinding, "valid_forensic_finding.json", "invalid_forensic_finding.json"),
    (ProvenanceRelationship, "valid_provenance_relationship.json", "invalid_provenance_relationship.json"),
    (InvestigationReport, "valid_investigation_report.json", "invalid_investigation_report.json"),
    (AuditEvent, "valid_audit_event.json", "invalid_audit_event.json"),
]


@pytest.mark.parametrize("model_cls,valid_file,invalid_file", MODEL_FIXTURE_PAIRS)
def test_valid_fixtures_pass_contract(model_cls, valid_file, invalid_file):
    """Verifies that valid synthetic fixture strictly satisfies model validation."""
    path = FIXTURES_DIR / valid_file
    assert path.exists(), f"Missing fixture file {valid_file}"
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    instance = model_cls.model_validate(data)
    assert instance is not None
    assert str(instance.id).startswith(f"{model_cls.__name__[:3].lower()}_") or "_" in str(instance.id)


@pytest.mark.parametrize("model_cls,valid_file,invalid_file", MODEL_FIXTURE_PAIRS)
def test_invalid_fixtures_fail_contract(model_cls, valid_file, invalid_file):
    """Verifies that intentionally malformed fixture fails validation."""
    path = FIXTURES_DIR / invalid_file
    assert path.exists(), f"Missing fixture file {invalid_file}"
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    with pytest.raises(ValidationError):
        model_cls.model_validate(data)

