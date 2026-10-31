# Veritas — Shared Data Contracts (v1.0.0)

> **Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
> **Directory:** `contracts/`  
> **Purpose:** Canonical, Machine-Readable Schemas & Fixtures for Decoupled Multi-Developer Systems  
> **Legacy Compatibility Note:** `VeritasBaseModel` is the canonical base class; `PramaanBaseModel` is preserved strictly as a legacy alias for backward compatibility with existing contract consumers; it does not represent the project's official identity.  

---

## 1. Overview for Person 2 (Forensics & Workspace Developer)

Person 2 is developing image, video, audio forensics, provenance graph fusion, and the investigator workspace on an independent workstation. **Person 2 does not need to run Person 1's backend, database, or Python environment.**

This directory provides the definitive single source of truth for:
1. Pydantic v2 source code models (`contracts/schemas/models.py`).
2. Standalone exported JSON Schemas (generated via `python scripts/export_schemas.py`).
3. Representative valid and invalid synthetic JSON fixtures (`contracts/fixtures/`).

---

## 2. Identifier Conventions & Entity Matrix

All shared models use a 3-character lowercase prefix, followed by `_`, and a standard UUIDv4:

| Entity | Prefix | Primary Owner | Module Alignment |
| :--- | :--- | :--- | :--- |
| **Investigation** | `inv_` | Shared | Case container |
| **EvidenceAsset** | `ast_` | Person 1 | Data Ingestion (Phase 1) |
| **AssetDerivation** | `drv_` | Shared | Normalization & Forensics Crops |
| **ProcessingResult** | `res_` | Person 1 | ASR, OCR & Embeddings (Phase 2) |
| **Claim** | `clm_` | Person 1 | Claim Intelligence (Phase 2) |
| **SourceDocument** | `doc_` | Person 1 | Source Intelligence & Retrieval (Phase 3) |
| **EvidenceItem** | `evi_` | Person 1 | Evidentiary Passages (Phase 3) |
| **ClaimAssessment** | `asm_` | Person 1 | Fact Verification (Phase 4) |
| **ForensicFinding** | `fnd_` | Person 2 | Media Forensics Engines (Phases 5–7) |
| **ProvenanceRelationship** | `rel_` | Person 2 | Provenance Graph Engine (Phase 8) |
| **InvestigationReport** | `rpt_` | Person 2 | Investigator Workspace Dossier (Phase 10) |
| **AuditEvent** | `adt_` | Shared | Cryptographic Chain of Custody |

---

## 3. How Person 2 Consumes These Contracts Independently

### Option A: Direct Python Import (If using Python)
Person 2 can copy or import the `contracts/schemas/models.py` file:
```python
from contracts.schemas import (
    EvidenceAsset,
    Claim,
    ClaimAssessment,
    ForensicFinding,
    ForensicVerdict,
    RawScoreType,
    CalibrationStatus,
)

# Validate incoming asset payload from Person 1 mock
asset = EvidenceAsset.model_validate(json_payload)

# Construct valid forensic finding to return to workspace or graph
# Example: Raw detector output (uncalibrated)
finding_raw = ForensicFinding(
    id="fnd_90123456-9012-4012-8012-901234567234",
    investigation_id=asset.investigation_id,
    asset_id=asset.id,
    modality="VIDEO",
    technique="TEMPORAL_FLICKER",
    raw_score=0.94,
    raw_score_type=RawScoreType.ANOMALY_INDEX,
    calibration_status=CalibrationStatus.UNCALIBRATED,
    calibrated_score=None,
    verdict=ForensicVerdict.LIKELY_SYNTHETIC,
    model_name="TemporalSyncNet",
    model_version="1.0.0",
    score_interpretation="Raw anomaly index measuring frame-to-frame temporal inconsistency; higher indicates more flicker anomaly.",
    limitations_notes="Evaluated on 1080p 30fps video; performance degrades on heavy H.264 compression.",
    executed_at="2026-10-31T06:12:30.000000Z",
)

# Example: Calibrated finding (with empirical calibration metadata)
finding_calibrated = ForensicFinding(
    id="fnd_90123456-9012-4012-8012-901234567235",
    investigation_id=asset.investigation_id,
    asset_id=asset.id,
    modality="VIDEO",
    technique="FACIAL_REENACTMENT_DETECTION",
    raw_score=2.85,
    raw_score_type=RawScoreType.UNNORMALIZED_LOGIT,
    calibration_status=CalibrationStatus.CALIBRATED,
    calibrated_score=0.91,
    calibration_method="temperature_scaling",
    calibration_metadata={"temperature": 1.42, "holdout_ece": 0.034, "dataset": "FF++ c23"},
    verdict=ForensicVerdict.LIKELY_SYNTHETIC,
    model_name="FaceForensicsClassifier",
    model_version="2.1.0",
    score_interpretation="Empirically calibrated probability of synthetic manipulation under holdout validation.",
    executed_at="2026-10-31T06:15:00.000000Z",
)
```

### Option B: JSON Schema Consumption (TypeScript / Frontend / Other Languages)
Run `python scripts/export_schemas.py` to produce standard JSON Schema `.json` files in `contracts/schemas/json/`. Person 2 can generate TypeScript types using `quicktype` or `json-schema-to-typescript`:
```bash
npx json-schema-to-typescript contracts/schemas/json/ForensicFinding.json > src/types/forensic.ts
```

### Option C: Using Local JSON Fixtures for Mocking
Person 2 can load the synthetic fixtures from `contracts/fixtures/`:
- `valid_evidence_asset.json`: Load to test video/image decoding pipelines without calling Person 1's API.
- `valid_claim.json` & `valid_claim_assessment.json`: Load to test provenance graph linking and investigator workspace dashboards without calling Person 1's fact-checker.

---

## 4. Contract Governance & Mutual Agreement

1. **No Unilateral Changes:** Person 1 must not modify Person 2's forensic contract (`fnd_`, `rel_`, `rpt_`) unilaterally. Person 2 must not modify Person 1's ingestion and claim contracts (`ast_`, `clm_`, `asm_`) unilaterally. Proposed modifications are documented as RFC-style updates awaiting Person 2's review.
2. **Epistemic Distinctions:**
   - Media manipulation detection (`fnd_`) is strictly independent of claim factuality (`asm_`).
   - A detector score in $[0, 1]$ is **not automatically a probability**. Detector scores remain raw unless empirical calibration is verified.
   - Missing C2PA manifests do not imply media is synthetic.
   - Perceptual similarity is not proof of derivation or shared origin.

---

## 5. Phase 0 Remediation: Semantic Refinements for Review by Person 2

In accordance with Phase 0 audit findings, two contract-design corrections have been introduced in `contracts/schemas/models.py`. **These changes are submitted as a backward-compatible proposal for Person 2's formal review and sign-off.**

### 5.1 ForensicFinding Calibration Semantics
- **The Problem:** The initial draft coupled detector confidence to a single score constrained to $[0, 1]$ and labeled it as calibrated. However, bounding a score to $[0, 1]$ does not make it calibrated, nor does it make it a probability. In forensic machine learning, detectors output raw logits, distance metrics, or anomaly indices that often suffer from overconfidence, domain shift, or uncalibrated sigmoid transformations.
- **The Remediation:**
  - `raw_score` (float): The actual, unmodified output from the forensic detector (can be negative, greater than 1.0, or bounded depending on technique).
  - `raw_score_type` (`RawScoreType` enum): Explicitly indicates what the raw score represents: `UNNORMALIZED_LOGIT`, `ANOMALY_INDEX`, `SIMILARITY`, `DISTANCE`, `NORMALIZED_BOUNDED`, or `OTHER`.
  - `calibration_status` (`CalibrationStatus` enum): Explicitly states calibration state: `UNCALIBRATED`, `CALIBRATED`, or `NOT_APPLICABLE`.
  - `calibrated_score` (Optional[float], bounded $[0.0, 1.0]$): An empirical probability estimate. Populated **only** when `calibration_status == "CALIBRATED"`.
  - `calibration_method` (Optional[str]): The empirical method applied (e.g., `temperature_scaling`, `platt_scaling`, `isotonic_regression`). Required when calibrated.
  - `calibration_metadata` (Dict[str, Any]): Supporting empirical evidence such as holdout dataset, temperature parameter, or Expected Calibration Error (ECE). Calibration metadata must never be fabricated.
  - `score_interpretation` (Optional[str]) & `limitations_notes` (Optional[str]): Explanatory documentation of what the score indicates and known operational limitations (e.g., degradation under H.264 compression).
  - **Backward-Compatibility:** `ScoreType` is retained as an alias to `RawScoreType` so existing code does not break.

### 5.2 AssetDerivation & Provenance Cycle Detection Boundaries
- **The Problem:** Documentation previously claimed that model-level check `derived_asset_id != parent_asset_id` ensured acyclicity. In reality, a local record validator only prevents direct 1-hop self-references (`A -> A`); it cannot detect or prevent multi-hop cycles (`A -> B -> C -> A`), which require full graph traversal.
- **The Remediation:**
  - `AssetDerivation.check_direct_self_reference` explicitly states its scope: it guards solely against immediate self-derivation (`derived_asset_id != parent_asset_id`).
  - Full DAG cycle detection and multi-hop acyclicity enforcement are formal responsibilities of the **Provenance Graph Engine (Phase 8)**, owned by Person 2, where cross-asset relationship state is maintained and traversed.
  - No provenance graph logic has been prematurely implemented in Phase 0.


