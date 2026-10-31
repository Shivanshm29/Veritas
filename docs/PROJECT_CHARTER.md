# Veritas — Project Charter

> **Project Identity:** Veritas (architecturally designated as PRAMAAN — Provenance, Reliability & Authenticity Monitoring and Analysis Network)  
> **Document:** Project Charter & Operational Mandate  
> **Classification:** Open Architecture / Forensic Standards  
> **Target Delivery:** High-Trust Multimodal Digital Authenticity & Claim Verification  

---

## 1. Problem Statement

The proliferation of hyper-realistic generative artificial intelligence (AI), including synthetic video reenactment, diffusion-based image synthesis, voice cloning, and AI-accelerated disinformation networks, poses an unprecedented threat to public discourse, democratic elections, financial stability, and digital forensics.

Current verification solutions suffer from three fundamental architectural flaws:
1. **Isolated Forensic Silos:** Image, video, and audio forensic detectors operate independently without cross-modal reasoning or correlation.
2. **Conflation of Media Authenticity and Semantic Truth:** Legacy fact-checkers fail to assess synthetic media generation, while deepfake detectors fail to evaluate the factual truthfulness of assertions made within the media.
3. **Absence of Verifiable Provenance:** Verification outputs frequently present uncalibrated "scores" without citing traceable, verifiable ground-truth evidence, preventing legal and investigative admissibility.

---

## 2. Project Goals & Vision

**Veritas** solves these challenges by combining state-of-the-art **multimodal media forensics**, **automated claim intelligence**, **retrieval-grounded source verification**, and an **immutable provenance graph**.

### Core Objectives
1. **Decoupled, Reliable Architecture:** Establish an independent, modular architecture enabling Person 1 (Ingestion & Claims) and Person 2 (Forensics & Workspace) to develop and test without cross-system runtime coupling.
2. **Comprehensive Multimodal Verification:** Extract claims from video, audio, and visual text, verifying assertions against authoritative source corpora.
3. **Admissible Provenance Tracking:** Build Directed Acyclic Graphs (DAGs) linking every verified claim to specific timecodes, bounding boxes, source document passages, and forensic detector traces.
4. **Transparent Epistemic Standards:** Explicitly represent uncertainty, conflicting evidence, uncalibrated scores, and inconclusive findings without forced artificial consensus.

---

## 3. Scope Boundaries

### In Scope for Person 1 (This Repository)
- High-throughput content ingestion (HTTP upload, URL stream pull).
- Cryptographic hashing (SHA-256) and C2PA manifest presence detection.
- Multimodal processing normalization (audio demuxing, keyframe sampling, Whisper ASR, OCR extraction).
- Atomic claim extraction, multilingual parsing, and normalization.
- Source intelligence, hybrid retrieval (BM25 + Dense vector search), and domain credibility scoring.
- Evidence-based claim verification and transparent stance synthesis (`SUPPORTED`, `REFUTED`, `CONTRADICTORY_EVIDENCE`, `INSUFFICIENT_EVIDENCE`).
- Baseline FastAPI service, worker execution scaffolding, and canonical data contract maintenance.

### In Scope for Person 2 (Teammate's Repository)
- Spatial, spectral, and frequency-domain image forensics.
- Temporal consistency, inter-frame flicker, and biometric video forensics.
- Voice clone, vocoder artifact, and acoustic audio forensics.
- Interactive provenance graph engine and cross-modal fusion.
- Investigator dashboard, timeline visualization, and PDF forensic reporting.

### Out of Scope (Phase 0)
- End-to-end heavy neural model inference (Whisper large, WavLM, UnivNet).
- Real-time social platform scraping pipelines.
- Production multi-tenant Kubernetes clusters.
- Front-end React/Next.js dashboard (owned by Person 2 in Phase 10).

---

## 4. User Personas

| Persona | Role | Primary Needs |
| :--- | :--- | :--- |
| **Investigative Journalist** | Verifies viral media under tight editorial deadlines. | Fast turnaround, reliable claim stance synthesis, clear citations, human-readable explanations. |
| **Forensic Analyst** | Analyzes digital evidence for legal / regulatory admissibility. | Cryptographic chain of custody, uncalibrated detector transparency, raw heatmaps, C2PA manifest audits. |
| **Fact-Checking Organization** | Cross-references claims against trusted public records. | Automated claim extraction from speeches, high-precision retrieval from official gazettes, multi-source conflict detection. |
| **Platform Trust & Safety Officer** | Screens flagged content at scale for high-harm synthetic disinformation. | Low-latency API response, unambiguous status codes, verifiable provenance graphs, exportable dossiers. |

---

## 5. Constraints & Assumptions

- **Independent Development Constraint:** Person 1 and Person 2 must develop on independent workstations with isolated databases, different Python/Node environments, and zero requirement for the peer's application to be running.
- **Contract-First Constraint:** All entity exchanges must comply with agreed Pydantic v2 schemas and versioned JSON contracts.
- **Zero Hallucination Constraint:** Claim assessments must never assert factual verification without citing concrete `EvidenceItem` identifiers.
- **Resource Constraints:** Phase 0 runs on standard developer workstations (Windows/Linux/macOS) without mandatory GPU hardware.

---

## 6. Success & Acceptance Criteria

1. **Phase 0 Baseline:** Clean, reproducible repository structure, passing contract tests for all 12 shared schemas, functioning health check APIs, and zero unhandled exceptions.
2. **Independent Testing:** 100% of Person 1's automated tests execute cleanly using in-memory databases and synthetic fixtures without external dependencies.
3. **Admissibility & Auditability:** Every action, asset ingestion, and claim evaluation emits an immutable `AuditEvent`.

