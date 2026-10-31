# Veritas — Phase 2 Design Note: Claim Intelligence & Multilingual NLP

## 1. Overview and Objectives
Phase 2 builds a reliable, testable claim-intelligence subsystem that converts supplied text (or text associated with an evidence asset) into structured, traceable claim candidates.

**Core Invariant:** The subsystem extracts and structures claims; it does **not** determine truth/falsity (Phase 4), retrieve external evidence (Phase 3), or run media forensics (Phases 5–7).

## 2. Inputs and Outputs
- **Inputs:**
  - Raw textual assertions (string, bounded to 50,000 characters).
  - Optional associated `investigation_id` (`inv_<uuid4>`) and `source_asset_id` (`ast_<uuid4>`).
  - Optional modality origin (`USER_PROMPT`, `EXTERNAL_POST`, `TRANSCRIPT`, `OCR`).
  - Optional timecode bounds (`source_timecode_start_ms`, `source_timecode_end_ms`).
- **Outputs:**
  - Structured canonical `Claim` objects (`clm_<uuid4>`).
  - Traceable source character offsets (`source_char_start`, `source_char_end`) pointing into the original text.
  - Language identification and confidence (`detected_language`, `language_confidence`).
  - Assessability status (`FACTUAL_CLAIM`, `OPINION`, `QUESTION`, `COMMAND_OR_REQUEST`, `INCOMPLETE_OR_FRAGMENT`, `AMBIGUOUS`).
  - Structured `UnprocessedSegment` records explaining abstentions (questions, opinions, fragments).
  - Processing metadata (execution time, extractor version, warnings).

## 3. Canonical Contracts Reused and Extended
- **Reused Canonical Model:** `Claim` from `contracts/schemas/models.py`.
- **Backward-Compatible Extensions:**
  - `source_char_start: Optional[int] = Field(None, ge=0)`
  - `source_char_end: Optional[int] = Field(None, ge=0)`
  - `language: Optional[str] = Field(None, max_length=10)`
  - `extraction_method: Optional[str] = Field(None)`
  *Compatibility Impact:* Purely additive with default `None`. All existing Phase 0 and Phase 1 fixtures, tests, and JSON Schemas remain 100% valid.
- **Traceability Guarantee:** Character offsets map directly into the original input string.

## 4. Subsystem Architecture & Modules
```
backend/app/
├── api/v1/endpoints/
│   └── claims.py                 # REST API endpoints (/api/v1/claims)
├── db/
│   ├── models/claim.py           # SQLAlchemy ORM model for ClaimRecord
│   └── repositories/claim.py     # ClaimRepository for CRUD and filtering
└── services/nlp/
    ├── __init__.py               # Service exports
    ├── language.py               # Multilingual script & language detector
    ├── normalization.py          # Deterministic NFC and whitespace normalizer
    ├── assessability.py          # Factual vs opinion/question/fragment classifier
    ├── extractor.py              # End-to-end claim extraction & span tracking engine
    └── provider.py               # Pluggable NLP provider (heuristic, LLM adapter, mock)
```

## 5. Dependencies
- Leverages existing project dependencies: `pydantic`, `fastapi`, `sqlalchemy`, `regex`, Python standard library (`unicodedata`, `hashlib`, `uuid`).
- Pluggable provider abstraction allows optional LLM integration (e.g. `openai` library already installed) with zero hard network dependencies during core test execution.

## 6. Failure, Uncertainty & Abstention Handling
- **Non-Factual Content:** Questions, opinions, commands, and greeting fragments are classified as non-assessable and returned in `unprocessed_segments` with explanatory reasons rather than forced into false claims.
- **Empty / Whitespace Input:** Rejected with `EmptyTextError` (HTTP 400).
- **Oversized Input:** Rejected with `PayloadTooLargeError` (HTTP 413) if > 50,000 characters.
- **Unsupported / Ambiguous Languages:** Identified with language code `und` (undetermined) and flagged with warnings.
- **Confidence Semantics:**
  - `extraction_confidence`: Represents extraction syntactic and entity completeness (0.0 to 1.0).
  - Explicitly documented: **Extraction confidence does NOT represent factual truth.**

## 7. Scope Exclusions (Strict Phase Boundaries)
- No web search, RAG, or source document retrieval (Phase 3).
- No NLI verification, stance scoring, or truth verdict generation (Phase 4).
- No image/video/audio forensic models (Phases 5–7, owned by Person 2).
- No provenance graph building (Phase 8).
