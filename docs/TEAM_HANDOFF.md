# Veritas — Engineering Onboarding & Team Handoff (Person 2)

> **Document:** Team Handoff & Developer Collaboration Specification  
> **Repository:** [https://github.com/Shivanshm29/Veritas.git](https://github.com/Shivanshm29/Veritas.git)  
> **Target Audience:** Person 2 (Media Forensics, Provenance Graph & Investigator Workspace Engineer)  
> **Author:** Person 1 (Backend Core, Ingestion, Claim Intelligence & Verification Lead)  
> **Status:** Phase 0 Baseline Handoff  

---

## 1. Welcome & Collaboration Overview

Welcome to **Veritas** (PRAMAAN)! This document provides everything you need to clone the repository, configure your environment, consume shared contracts independently, and begin developing your assigned modules on your independent machine.

You do **not** need to run Person 1's backend API, database, or worker processes to build and test your modules. Everything is decoupled contract-first.

---

## 2. Person 2 Assigned Modules & Roadmap

You are the sole owner of the following roadmap phases:

- **Phase 5 — Image Forensics Engine:**
  - Spatial manipulation detection, frequency artifact analysis (DCT/FFT), GAN/diffusion fingerprints, facial tampering classifiers.
- **Phase 6 — Video Forensics Engine:**
  - Temporal inconsistency detection, inter-frame jitter, audio-visual synchronization, deepfake video classification.
- **Phase 7 — Audio Forensics Engine:**
  - Voice cloning detection, synthetic speech vocoder artifacts, acoustic anomaly detection.
- **Phase 8 — Provenance Graph & Cross-Modal Intelligence:**
  - Graph synthesis linking `EvidenceAsset`, `AssetDerivation`, `ForensicFinding`, and `ClaimAssessment`.
  - Multi-hop DAG traversal and cycle detection ($A \to B \to C \to A$).
  - Cross-modal conflict resolution and evidence fusion.
- **Phase 10 — Investigator Workspace & Reporting:**
  - Interactive analyst web UI (React/TypeScript), case dossier, report generation (`InvestigationReport`).
- **Joint Coordination:**
  - Phase 9 (Real-Time Monitoring), Phase 11 (Security Hardening), Phase 12 (Benchmarking & Calibration), and Phase 13 (Hackathon Demo & Integration).

> **Important:** Person 1 is developing Phases 1–4 (Ingestion, Normalization, Claim Intelligence, and Retrieval Verification). Neither person touches the other's internal business logic.

---

## 3. Clone & Environment Setup

### 3.1 Clone the Repository
```bash
git clone https://github.com/Shivanshm29/Veritas.git
cd Veritas
```

### 3.2 Branching Policy
> [!IMPORTANT]
> **Do not commit ongoing work directly to `main`.**  
> Always branch off `main` for your feature work:
> ```bash
> git checkout -b feature/phase-5-image-forensics
> ```

### 3.3 System Prerequisites
- **Python:** `3.12` or higher (tested on `3.14.5`).
- **Git:** `2.40` or higher.
- **Node.js:** `18+` / `20+` (for Phase 10 Investigator Workspace frontend when you begin).

### 3.4 Python Dependency Installation
```bash
# Optional: create a local virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on Linux/macOS:
source .venv/bin/activate

# Install development & test dependencies in editable mode
python -m pip install -e .[test]
```

### 3.5 Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
The defaults in `.env.example` are pre-configured for safe local testing using in-memory fallbacks (`sqlite:///:memory:`). No live database or cloud service is required.

---

## 4. Shared Contract Locations & Consumption

Shared data models reside in the `contracts/` directory:

```text
contracts/
├── schemas/
│   ├── models.py       # Pydantic v2 canonical definitions (12 core models)
│   ├── __init__.py     # Package exports
│   └── json/           # 12 exported standalone JSON Schema files
├── fixtures/           # 24 valid and invalid synthetic JSON fixtures
└── README.md           # Detailed contract guide
```

### Option A: Python Import (Forensics Engines)
```python
from contracts.schemas import (
    EvidenceAsset,
    ForensicFinding,
    ForensicVerdict,
    RawScoreType,
    CalibrationStatus,
)

# 1. Parse incoming asset mock
asset = EvidenceAsset.model_validate(json_data)

# 2. Return valid forensic finding
finding = ForensicFinding(
    id="fnd_90123456-9012-4012-8012-901234567234",
    investigation_id=asset.investigation_id,
    asset_id=asset.id,
    modality="IMAGE",
    technique="FREQUENCY_DCT_ANALYSIS",
    raw_score=0.88,
    raw_score_type=RawScoreType.ANOMALY_INDEX,
    calibration_status=CalibrationStatus.UNCALIBRATED,
    calibrated_score=None,
    verdict=ForensicVerdict.LIKELY_SYNTHETIC,
    model_name="DCTArtifactNet",
    model_version="1.0.0",
    score_interpretation="High frequency energy anomaly in high-pass DCT subbands.",
    limitations_notes="Susceptible to false positives on aggressive JPEG recompression (Q < 50).",
    executed_at="2026-10-31T12:00:00.000000Z",
)
```

### Option B: TypeScript Code Generation (Investigator Workspace)
Generate TypeScript interfaces for the React UI from standalone JSON schemas:
```bash
npx json-schema-to-typescript contracts/schemas/json/ForensicFinding.json > src/types/forensic.ts
npx json-schema-to-typescript contracts/schemas/json/InvestigationReport.json > src/types/report.ts
```

### Option C: Synthetic Mock Fixtures
Use the pre-packaged fixtures in `contracts/fixtures/`:
- `valid_evidence_asset.json`: Test image/video loading without calling Person 1's ingestion API.
- `valid_claim.json` & `valid_claim_assessment.json`: Test provenance graph creation without calling Person 1's claim verification pipeline.

---

## 5. Verification Commands

Verify that your local environment passes all quality checks:

```bash
# 1. Run all 73 automated tests
python -m pytest -v

# 2. Export updated JSON schemas (if you modify contracts)
python scripts/export_schemas.py

# 3. Run pre-flight quality checks
python scripts/run_checks.py
```

---

## 6. Shared Contract Evolution & Governance

1. **No Unilateral Breaking Changes:** Neither developer may unilaterally delete, rename, or alter required fields in shared contracts.
2. **Coordinated Modification Protocol:**
   - Create a proposed contract change on your feature branch.
   - Update `contracts/schemas/models.py`.
   - Update or add corresponding valid and invalid fixtures in `contracts/fixtures/`.
   - Re-export JSON schemas with `python scripts/export_schemas.py`.
   - Run `python -m pytest -v` to ensure zero regressions across the 73 baseline tests.
   - Open a Pull Request for mutual review and sign-off.

---

## 7. Pending Approvals & Known Environmental Notes

1. **Pending Approval on ForensicFinding & AssetDerivation:**
   - In Phase 0, Person 1 refined `ForensicFinding` to separate raw model scores (`raw_score`, `raw_score_type`) from calibrated probabilities (`calibrated_score`), and clarified that `AssetDerivation` local checks only prevent direct self-derivation ($A \to A$), leaving multi-hop DAG cycle checks to your Phase 8 graph engine.
   - **Status:** **PENDING**. This is documented as a proposal for your formal review. Please inspect `contracts/schemas/models.py` and confirm sign-off before merging shared contract changes.
2. **Untested Live Infrastructure:** Docker Compose services (PostgreSQL 16, Redis 7, MinIO S3) are specified in `infra/docker-compose.yml`, but were not tested against a live daemon during Phase 0 local validation. In-memory SQLite (`sqlite:///:memory:`) was used for test isolation.
3. **Host FFmpeg:** Ensure FFmpeg and FFprobe are installed and present in your system PATH before developing media decoding pipelines in Phase 5 and Phase 6.

---

## 8. Shared Contract Specification Matrix & Formal Handoff

The 12 canonical Pydantic v2 schemas in `contracts/schemas/models.py` form the single source of truth across all 14 roadmap phases:

| Canonical Entity | ID Prefix | Primary Owner | Required Fields | Optional Fields | Score Semantics | Version & Compatibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`Investigation`** | `inv_` | Shared | `id`, `title`, `description`, `status`, `lead_investigator_id`, `created_at`, `updated_at` | `priority`, `tags`, `assigned_collaborator_ids`, `closed_at`, `closure_reason` | Strict `InvestigationStatus` enum | v1.0.0; additive changes backward-compatible. |
| **`EvidenceAsset`** | `ast_` | Person 1 | `id`, `investigation_id`, `asset_type`, `mime_type`, `original_filename`, `file_size_bytes`, `sha256_hash`, `storage_uri`, `status`, `created_at` | `source_url`, `acquisition_method`, `md5_hash`, `duration_seconds`, `width_px`, `height_px`, `parent_asset_id` | Checksum & MIME invariants | v1.0.0; storage URI scheme validated. |
| **`AssetDerivation`** | `drv_` | Shared | `id`, `derived_asset_id`, `parent_asset_id`, `derivation_type`, `created_at` | `operator_id`, `tool_name`, `tool_version`, `parameters`, `bounding_box`, `time_range_ms` | Rejects direct self-derivation ($A \to A$) | v1.0.0; multi-hop DAG cycle detection deferred to Phase 8. |
| **`ProcessingResult`** | `res_` | Person 1 | `id`, `asset_id`, `task_name`, `worker_id`, `status`, `execution_time_ms`, `created_at` | `output_payload`, `error_message`, `error_code`, `model_name`, `model_version` | Execution metrics; non-negative duration | v1.0.0; `error_message` required on FAILED status. |
| **`Claim`** | `clm_` | Person 1 | `id`, `investigation_id`, `claim_text`, `language`, `extraction_confidence`, `status`, `extracted_at` | `source_asset_id`, `source_timecode_start_ms`, `source_timecode_end_ms`, `speaker_id`, `claim_type` | `extraction_confidence` in $[0.0, 1.0]$; timecode ordering | v1.0.0; start $\le$ end milliseconds enforced. |
| **`SourceDocument`** | `doc_` | Person 1 | `id`, `title`, `url`, `domain`, `retrieval_timestamp`, `content_snippet`, `content_sha256` | `author`, `publisher`, `published_date`, `source_reliability_score`, `full_text_storage_uri` | `source_reliability_score` in $[0.0, 1.0]$ | v1.0.0; URL scheme & 64-char hex hash enforced. |
| **`EvidenceItem`** | `evi_` | Person 1 | `id`, `claim_id`, `source_document_id`, `evidence_text`, `stance`, `relevance_score`, `created_at` | `page_number`, `paragraph_index`, `retrieval_method` | `relevance_score` in $[0.0, 1.0]$; `EvidenceStance` enum | v1.0.0; text length 10–4000 characters. |
| **`ClaimAssessment`** | `asm_` | Person 1 | `id`, `investigation_id`, `claim_id`, `verdict`, `confidence_score`, `explanation`, `model_identifier`, `assessed_at` | `cited_evidence_ids`, `conflicting_points`, `limitations` | `confidence_score` in $[0.0, 1.0]$; `ClaimVerdict` enum | v1.0.0; `cited_evidence_ids` non-empty on SUPPORTED/REFUTED. |
| **`ForensicFinding`** | `fnd_` | Person 2 | `id`, `investigation_id`, `asset_id`, `modality`, `technique`, `raw_score`, `raw_score_type`, `calibration_status`, `verdict`, `model_name`, `model_version`, `executed_at` | `calibrated_score`, `calibration_method`, `calibration_metadata`, `score_interpretation`, `region_of_interest`, `heatmap_artifact_uri`, `detected_artifacts`, `limitations_notes` | Decoupled: `raw_score` (scale typed by `RawScoreType`); `calibrated_score` in $[0.0, 1.0]$ requires empirical `calibration_method` and `calibration_status == "CALIBRATED"` | v1.0.0; legacy `score_type` preserved as backward-compatible alias. **Pending Person 2 Sign-Off.** |
| **`ProvenanceRelationship`** | `rel_` | Person 2 | `id`, `investigation_id`, `source_node_id`, `source_node_type`, `target_node_id`, `target_node_type`, `relationship_type`, `confidence`, `created_at` | `evidence_citation_id`, `edge_weight`, `metadata` | `confidence` in $[0.0, 1.0]$; self-loop ($A \to A$) strictly rejected | v1.0.0; multi-hop DAG cycle checks deferred to Phase 8. |
| **`InvestigationReport`** | `rpt_` | Person 2 | `id`, `investigation_id`, `version`, `executive_summary`, `overall_media_authenticity`, `overall_claim_validity`, `lead_investigator_id`, `generated_at` | `report_status`, `included_finding_ids`, `included_assessment_ids`, `disclaimers`, `exported_pdf_uri` | Authenticity & validity enums; summary $\ge 50$ chars | v1.0.0; version $\ge 1$. |
| **`AuditEvent`** | `adt_` | Shared | `id`, `investigation_id`, `event_type`, `actor_id`, `actor_role`, `timestamp` | `target_entity_id`, `target_entity_type`, `action_details`, `sha256_payload_hash`, `ip_address`, `user_agent` | Append-only immutability | v1.0.0; payload SHA-256 hash verified. |

### Sign-off Status
- **Person 1 Approval:** `APPROVED` (Phase 0 Author).
- **Person 2 Approval:** `PENDING` (Awaiting review on separate machine).


