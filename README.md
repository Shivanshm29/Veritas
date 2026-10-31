# Veritas — Multimodal Deepfake Detection & Claim Verification Network

> **Project:** Veritas / PRAMAAN (Provenance, Reliability & Authenticity Monitoring and Analysis Network)  
> **Phase:** Phase 1 — Data Ingestion & Evidence Asset Management (Active Feature Branch)  
> **GitHub Repository:** [https://github.com/Shivanshm29/Veritas.git](https://github.com/Shivanshm29/Veritas.git)  
> **Default Branch:** `main`  
> **Phase 1 Branch:** `feature/phase-1-data-ingestion`

---

## 1. What Veritas Is & Purpose of the Project

**Veritas** (architecturally designated as **PRAMAAN**) is an asynchronous, contract-first multimodal intelligence and verification platform engineered to:
1. **Detect synthetic media manipulation:** Identify deepfakes, synthetic faces, audio voice clones, and AI-generated diffusion artifacts across video, audio, and images.
2. **Verify factual assertions:** Extract claims from multimedia content, retrieve corroborated ground-truth evidence from trusted sources, and generate explainable factual assessments.
3. **Trace media provenance:** Build cross-modal provenance graphs tracking asset transformations, derivation lineages, and multi-hop dissemination patterns.

Veritas operates under a **decoupled, contract-first multi-developer architecture**. Two developers (Person 1 and Person 2) work completely independently on separate machines without shared filesystems, local databases, or running runtime dependencies.

---

## 2. Fixed 14-Phase Project Roadmap

Veritas follows an immutable, 14-phase roadmap (Phases 0 through 13). Phases must not be renamed, reordered, merged, split, skipped, or renumbered:

- **Phase 0 — Project Foundation & Architecture** *(Shared Foundation / Person 1 Baseline — Completed)*
- **Phase 1 — Data Ingestion & Evidence Asset Management** *(Person 1 — Module 1)*
- **Phase 2 — Claim Intelligence & Multilingual NLP** *(Person 1 — Module 2)*
- **Phase 3 — Source Intelligence & Evidence Retrieval** *(Person 1 — Module 3)*
- **Phase 4 — Evidence-Based Claim Verification** *(Person 1 — Module 4)*
- **Phase 5 — Image Forensics Engine** *(Person 2 — Forensics)*
- **Phase 6 — Video Forensics Engine** *(Person 2 — Forensics)*
- **Phase 7 — Audio Forensics Engine** *(Person 2 — Forensics)*
- **Phase 8 — Provenance Graph & Cross-Modal Intelligence** *(Person 2 — Forensics & Graph)*
- **Phase 9 — Real-Time Monitoring & Early Warning** *(Joint Collaboration)*
- **Phase 10 — Investigator Workspace & Reporting** *(Person 2 — Frontend & Workspace)*
- **Phase 11 — Security, Privacy & Red-Team Hardening** *(Joint Collaboration)*
- **Phase 12 — Benchmarking, Calibration & Robustness** *(Joint Collaboration)*
- **Phase 13 — Deployment, Integration & Hackathon Demo** *(Joint Collaboration)*

---

## 3. Engineering Ownership Boundaries

To ensure independent progress without blocking dependencies:

### Person 1 Ownership (Backend & Verification)
- **Phase 0:** Core backend architecture, shared data contracts, and local development infrastructure.
- **Phase 1:** Data Ingestion & Evidence Asset Management (`EvidenceAsset`, storage adapters, SHA-256 deduplication).
- **Phase 2:** Claim Intelligence & Multilingual NLP (`Claim`, `ProcessingResult`, Whisper/ASR transcription, OCR, claim extraction).
- **Phase 3:** Source Intelligence & Evidence Retrieval (`SourceDocument`, `EvidenceItem`, search providers, vector retrieval).
- **Phase 4:** Evidence-Based Claim Verification (`ClaimAssessment`, NLI stance detection, citation graphs).
- Shared coordination in **Phases 9, 11, 12, and 13**.

### Person 2 Ownership (Forensics, Provenance & Workspace)
- **Phase 5:** Image Forensics Engine (Face forensics, frequency analysis, GAN/diffusion artifacts).
- **Phase 6:** Video Forensics Engine (Temporal consistency, audio-visual sync, frame manipulation).
- **Phase 7:** Audio Forensics Engine (Voice cloning detection, synthetic speech acoustics).
- **Phase 8:** Provenance Graph & Cross-Modal Intelligence (`ProvenanceRelationship`, multi-hop DAG cycle detection, media fusion).
- **Phase 10:** Investigator Workspace & Reporting (`InvestigationReport`, interactive web dossier, analyst UI).
- Shared coordination in **Phases 9, 11, 12, and 13**.

> **Boundary Rule:** Neither developer implements business logic for the other person's assigned modules. All integration points occur strictly via canonical contracts in `contracts/`.

---

## 4. Repository Structure

```text
Veritas/
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI workflow (Python 3.12)
├── backend/
│   ├── app/
│   │   ├── api/                    # Versioned REST router (/api/v1)
│   │   ├── core/                   # Settings, logging, RFC 9457 errors
│   │   ├── db/                     # SQLAlchemy session factory & base
│   │   ├── schemas/                # Health & Problem Details schemas
│   │   ├── services/               # System diagnostics & health probing
│   │   └── main.py                 # FastAPI application factory
│   ├── tests/                      # API and configuration test suite
│   ├── pyproject.toml              # Isolated backend package configuration
│   └── README.md                   # Backend documentation
├── contracts/
│   ├── fixtures/                   # 24 valid & invalid synthetic JSON fixtures
│   ├── schemas/
│   │   ├── json/                   # 12 exported standalone JSON Schema files
│   │   ├── models.py               # 12 canonical Pydantic v2 data models
│   │   └── __init__.py             # Contract package exports
│   └── README.md                   # Person 2 contract consumption guide
├── datasets/
│   └── manifests/
│       └── README.md               # Benchmark evaluation manifest specification
├── docs/
│   ├── API_CONVENTIONS.md          # Naming, prefixes, UTC timestamps, RFC 9457
│   ├── DATA_GOVERNANCE.md          # Data minimization, retention & privacy
│   ├── PROJECT_CHARTER.md          # Project goals, personas & constraints
│   ├── ROADMAP.md                  # Fixed 14-phase master roadmap
│   ├── SYSTEM_ARCHITECTURE.md      # Subsystems, data flow & integration
│   ├── TEAM_HANDOFF.md             # Person 2 onboarding & independent setup
│   ├── TEST_STRATEGY.md            # 7-tier test pyramid & QA gates
│   └── THREAT_MODEL.md             # STRIDE threat model & SSRF mitigations
├── infra/
│   ├── docker-compose.yml          # PostgreSQL 16, Redis 7, MinIO S3 containers
│   └── README.md                   # Infrastructure guide & fallback instructions
├── reviews/
│   ├── initial-integration-audit.md# Pre-existing project inspection report
│   └── phase-0-review.md           # Formal Phase 0 verification & audit verdict
├── scripts/
│   ├── export_schemas.py           # Exports standalone JSON Schemas
│   └── run_checks.py               # Pre-flight quality & test gate runner
├── tests/
│   ├── contract/                   # Contract fixture & JSON schema validators
│   ├── integration/                # Isolated SQLite database tests
│   ├── security/                   # SSRF, CORS & path disclosure tests
│   └── unit/                       # Pydantic invariant, logging & error tests
├── workers/
│   ├── app/                        # Decoupled task runner & probe tasks
│   ├── tests/                      # Worker asynchronous task tests
│   └── README.md                   # Worker architecture guide
├── .env.example                    # Template environment variables (safe defaults)
├── .gitignore                      # Git exclusion rules (virtual environments, secrets)
├── pyproject.toml                  # Root project packaging & pytest configuration
└── README.md                       # Master project overview
```

---

## 5. Prerequisites & Environment Setup

- **Python:** Version `3.12` or higher (verified on Python `3.14.5`).
- **Git:** Version `2.40` or higher.
- **Docker & Docker Compose:** Optional for local containers; automated tests fall back cleanly to in-memory SQLite and workers without Docker.

### Local Installation
```bash
# 1. Clone repository
git clone https://github.com/Shivanshm29/Veritas.git
cd Veritas

# 2. Configure environment file from safe template
cp .env.example .env

# 3. Install dependencies in editable development mode
python -m pip install -e .[test]
```

---

## 6. How to Run Tests & Verification

The test battery contains **73 automated tests** with 100% pass rate:

```bash
# Run all tests across unit, contract, API, integration, and security tiers
python -m pytest -v

# Run contract fixture validation only
python -m pytest tests/contract -v

# Run backend API tests only
python -m pytest backend/tests -v

# Run worker scaffold tests only
python -m pytest workers/tests -v

# Export updated standalone JSON Schemas
python scripts/export_schemas.py

# Run pre-flight quality check (schema export + full pytest battery)
python scripts/run_checks.py
```

---

## 7. How Person 2 Consumes Shared Contracts Independently

Person 2 does not need to run Person 1's backend or database. Three consumption pathways are supported:

### 1. Direct Python Import (Pydantic v2)
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

# Parse incoming EvidenceAsset mock
asset = EvidenceAsset.model_validate(json_data)

# Generate uncalibrated detector output
finding = ForensicFinding(
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
    score_interpretation="Raw anomaly index measuring inter-frame inconsistency.",
    limitations_notes="Tested on 1080p video; performance degrades on heavy H.264 compression.",
    executed_at="2026-10-31T06:12:30.000000Z",
)
```

### 2. TypeScript / Frontend Codegen (JSON Schema)
Person 2 can generate TypeScript interfaces for the Phase 10 Investigator Workspace directly from `contracts/schemas/json/`:
```bash
npx json-schema-to-typescript contracts/schemas/json/ForensicFinding.json > src/types/forensic.ts
```

### 3. Synthetic Fixtures
Load synthetic test doubles from `contracts/fixtures/`:
- `valid_evidence_asset.json`: Test image/video forensic pipelines without Person 1's ingestion API.
- `valid_claim.json` & `valid_claim_assessment.json`: Test provenance graph linking and workspace dossiers without Person 1's verification engine.

---

## 8. Implemented vs. Planned Features

| Component / Phase | Status | Details |
| :--- | :--- | :--- |
| **Phase 0 Foundation** | `IMPLEMENTED` | Application factory, router, logging, RFC 9457 errors, session factory, CI workflow. |
| **Shared Contracts (12 Models)** | `IMPLEMENTED` | Pydantic v2 schemas, 24 synthetic fixtures, 12 exported JSON schemas. |
| **Contract Semantics Remediated** | `IMPLEMENTED` | Explicit raw vs. calibrated scores, local direct self-derivation checks vs Phase 8 graph checks. |
| **Worker Subsystem Scaffold** | `IMPLEMENTED` | `InMemoryTaskRunner` for non-blocking asynchronous task execution without Redis. |
| **Phase 1 Ingestion** | `IMPLEMENTED` | Bounded chunk streaming, SHA-256 calculation, magic-byte MIME validation, atomic file storage, path traversal defense, transactional storage rollback on DB failure. |
| **Evidence Asset API** | `IMPLEMENTED` | `POST /api/v1/assets/upload`, `GET /api/v1/assets/{asset_id}`, `GET /api/v1/assets`. |
| **Automated Tests** | `IMPLEMENTED` | **108 passing tests** across unit, contract, API, integration, and security suites. |
| **Phase 2 Claims & NLP** | `PLANNED` | Whisper ASR transcription, Surya OCR, claim extraction pipelines. |
| **Phase 3 Source Retrieval** | `PLANNED` | SearXNG / Google Search providers, dense vector retrieval (BM25 + Chroma/Qdrant). |
| **Phase 4 Claim Verification** | `PLANNED` | NLI cross-encoder fact checking, verdict synthesis, citation generation. |
| **Phases 5–7 Media Forensics** | `PLANNED` | Person 2 ownership: Image, video, and audio forensic detection engines. |
| **Phase 8 Provenance Graph** | `PLANNED` | Person 2 ownership: Multi-hop DAG traversal, acyclicity enforcement, media fusion. |
| **Phase 10 Investigator Workspace**| `PLANNED` | Person 2 ownership: React/TypeScript frontend dossier and analyst workspace. |

---

## 9. Environmental Limitations & Untested Infrastructure

1. **Local Containers Offline:** Docker Desktop was not active during initial validation. All tests executed cleanly against an in-memory SQLite fallback (`sqlite:///:memory:`). Live PostgreSQL, Redis, and MinIO containers are specified in `infra/docker-compose.yml` and will execute in CI and live staging.
2. **Host FFmpeg Missing:** Static FFmpeg/FFprobe binaries are not currently installed on the host PATH. This is non-blocking for Phase 0 (no media decoding was implemented), but will be required when beginning Phase 1.
3. **No Heavy ML Dependencies:** Deep learning frameworks (PyTorch, Hugging Face transformers, Whisper) are deliberately omitted from Phase 0 to ensure fast, lightweight, and reproducible setup.

---

## 10. Bug Reporting & Shared Contract Governance

- **Feature Branch Workflow:** Person 2 must develop on dedicated feature branches (e.g. `feature/phase-5-image-forensics`), never committing directly to `main`.
- **Contract Change Protocol:**
  1. No unilateral modifications to `contracts/` are permitted.
  2. If Person 2 or Person 1 needs a field modification, submit a proposed change in a pull request with updated Pydantic models, JSON fixtures, and schema exports (`python scripts/export_schemas.py`).
  3. Ensure all 73 existing tests pass with zero regressions before requesting review.
  4. Both Person 1 and Person 2 must sign off on contract changes before merging to `main`.
