#!/usr/bin/env python3
"""
Export Pydantic v2 schemas to standard JSON Schema files.

Outputs to contracts/schemas/json/<ModelName>.json
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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

MODELS = [
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
]

def export_all():
    output_dir = Path(__file__).resolve().parent.parent / "contracts" / "schemas" / "json"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exported = []
    for model_cls in MODELS:
        schema = model_cls.model_json_schema()
        file_path = output_dir / f"{model_cls.__name__}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
        exported.append(file_path.name)
        print(f"Exported: {file_path}")
    
    print(f"\nSuccessfully exported {len(exported)} JSON Schemas to {output_dir}")

if __name__ == "__main__":
    export_all()
