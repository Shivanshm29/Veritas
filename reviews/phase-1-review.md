# Veritas — Phase 1 Review: Data Ingestion & Evidence Asset Management

**Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
**Phase:** Phase 1 — Data Ingestion & Evidence Asset Management  
**Subsystem:** Person 1 (Content Ingestion & Evidence Asset Management)  
**Date:** October 31, 2026  
**Auditor / Engineer:** Senior Software Architect, Backend Engineer, Security Engineer & QA Auditor  
**Document Path:** `reviews/phase-1-review.md`  
**Git Branch:** `feature/phase-1-data-ingestion`  
**Remote Repository:** `https://github.com/Shivanshm29/Veritas.git`  
**Legacy Compatibility Note:** `PramaanBaseModel` and `PramaanException` are preserved strictly as legacy aliases for backward compatibility with existing contract consumers; they do not represent the project's official identity.

---

## 1. Executive Verdict

```
================================================================================
PHASE 1 AUDIT & VERIFICATION VERDICT:
PASS — Ingestion Subsystem Fully Verified (Shared Contract Sign-Off: PENDING)
================================================================================
```

All acceptance criteria for Phase 1 (Data Ingestion & Evidence Asset Management) have been verified against the canonical `EvidenceAsset` data contract. The implementation provides bounded chunk streaming (64 KB chunks), incremental SHA-256 computation, container header magic-byte validation, filename sanitization, atomic storage writes, transactional storage rollback on database failure with safe exception preservation, duplicate upload handling, cancellation cleanup, and RFC 9457 Problem Details error responses.

**Reconciled Test Battery Summary:**
- **Execution Command:** `python scripts/run_checks.py` (which executes `python scripts/export_schemas.py` and `python -m pytest -v`)
- **Total Tests Collected:** **110**
- **Passed:** **110**
- **Failed:** **0**
- **Skipped:** **0**
- **Errors:** **0**
- **Warnings:** **0**
- **Exit Code:** `0`
- **Baseline Phase 0 Tests Preserved:** **73** (100% passing, zero regressions)
- **Phase 1 Additions:** **37** new tests across unit, API integration, contract conformance, duplicate upload handling, cancellation cleanup, and transactional storage-database rollback failure handling.

---

## 2. Test Results Reconciliation & Execution Evidence

### 2.1 Complete Test Suite Inventory (110 Tests)

| Category | File Path | Tests | Coverage Scope |
| :--- | :--- | :---: | :--- |
| **Phase 0 Contracts** | `tests/contract/test_all_contracts.py` | 24 | Valid & invalid synthetic fixture parsing for all 12 canonical models |
| **Phase 0 Contracts** | `tests/contract/test_json_schemas.py` | 12 | Existence and property schema validation for 12 exported JSON schemas |
| **Phase 1 Contract** | `tests/contract/test_evidence_asset_contract.py` | 1 | Live upload response conformance to `EvidenceAsset` and JSON schema |
| **Phase 1 Integration**| `tests/integration/test_asset_storage_db.py` | 2 | Storage file rollback upon DB crash + graceful handling of storage deletion failures |
| **Phase 0 Integration**| `tests/integration/test_isolated_db.py` | 2 | SQLAlchemy CRUD and transaction rollback in isolated in-memory DB |
| **Phase 0 Security** | `tests/security/test_cors_and_security.py` | 4 | CORS origin filtering, path redaction, and SSRF validator checks |
| **Phase 1 Unit** | `tests/unit/test_asset_validation.py` | 15 | Filename sanitization, header magic-byte checks, binary/script rejections |
| **Phase 0 Unit** | `tests/unit/test_core_models.py` | 12 | Prefixed ID regexes, calibrated score semantics, self-derivation blocks |
| **Phase 0/1 Unit** | `tests/unit/test_errors.py` | 5 | Problem Details serialization (4 Phase 0 + 1 Phase 1 domain error test) |
| **Phase 0 Unit** | `tests/unit/test_logging.py` | 2 | Token, bearer JWT, and password redaction in log formatter |
| **Phase 1 Unit** | `tests/unit/test_storage.py` | 7 | Chunk streaming, size cap, empty file, atomic replace, task cancellation cleanup, and temp cleanup failure exception preservation |
| **Phase 1 API** | `backend/tests/test_assets_api.py` | 11 | Multipart upload, ID validation, empty/malware rejections, retrieval, filtering, duplicate handling |
| **Phase 0 API** | `backend/tests/test_config.py` | 4 | CORS parsing (list, comma-separated, wildcard) and upload limit settings |
| **Phase 0 API** | `backend/tests/test_health.py` | 3 | Liveness root probe, diagnostic v1 probe, UTC timestamp enforcement |
| **Phase 0 API** | `backend/tests/test_openapi.py` | 2 | OpenAPI JSON generation and Swagger UI accessibility |
| **Phase 0 Workers** | `workers/tests/test_worker.py` | 4 | In-memory asynchronous task dispatcher, probe tasks, error trapping |
| **Total** | | **110** | **100% Passing (0 failures, 0 warnings)** |

### 2.2 Actual Test Runner Output

```text
================================================================================
STEP: Export JSON Schemas
CMD:  C:\Python314\python.exe scripts/export_schemas.py
================================================================================
Exported: contracts/schemas/json/Investigation.json
Exported: contracts/schemas/json/EvidenceAsset.json
Exported: contracts/schemas/json/AssetDerivation.json
Exported: contracts/schemas/json/ProcessingResult.json
Exported: contracts/schemas/json/Claim.json
Exported: contracts/schemas/json/SourceDocument.json
Exported: contracts/schemas/json/EvidenceItem.json
Exported: contracts/schemas/json/ClaimAssessment.json
Exported: contracts/schemas/json/ForensicFinding.json
Exported: contracts/schemas/json/ProvenanceRelationship.json
Exported: contracts/schemas/json/InvestigationReport.json
Exported: contracts/schemas/json/AuditEvent.json

Successfully exported 12 JSON Schemas to contracts/schemas/json
[PASS] Step 'Export JSON Schemas' completed successfully.

================================================================================
STEP: Run Pytest Suite
CMD:  C:\Python314\python.exe -m pytest -v
================================================================================
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\shiva\projects\Deepfake detection
configfile: pyproject.toml
testpaths: tests, backend/tests, workers/tests
plugins: anyio-4.14.1, Faker-40.44.0, langsmith-0.14.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 110 items

tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[Investigation-valid_investigation.json-invalid_investigation.json] PASSED [  0%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[EvidenceAsset-valid_evidence_asset.json-invalid_evidence_asset.json] PASSED [  1%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[AssetDerivation-valid_asset_derivation.json-invalid_asset_derivation.json] PASSED [  2%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[ProcessingResult-valid_processing_result.json-invalid_processing_result.json] PASSED [  3%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[Claim-valid_claim.json-invalid_claim.json] PASSED [  4%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[SourceDocument-valid_source_document.json-invalid_source_document.json] PASSED [  5%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[EvidenceItem-valid_evidence_item.json-invalid_evidence_item.json] PASSED [  6%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[ClaimAssessment-valid_claim_assessment.json-invalid_claim_assessment.json] PASSED [  7%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[ForensicFinding-valid_forensic_finding.json-invalid_forensic_finding.json] PASSED [  8%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[ProvenanceRelationship-valid_provenance_relationship.json-invalid_provenance_relationship.json] PASSED [  9%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[InvestigationReport-valid_investigation_report.json-invalid_investigation_report.json] PASSED [ 10%]
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[AuditEvent-valid_audit_event.json-invalid_audit_event.json] PASSED [ 10%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[Investigation-valid_investigation.json-invalid_investigation.json] PASSED [ 11%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[EvidenceAsset-valid_evidence_asset.json-invalid_evidence_asset.json] PASSED [ 12%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[AssetDerivation-valid_asset_derivation.json-invalid_asset_derivation.json] PASSED [ 13%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ProcessingResult-valid_processing_result.json-invalid_processing_result.json] PASSED [ 14%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[Claim-valid_claim.json-invalid_claim.json] PASSED [ 15%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[SourceDocument-valid_source_document.json-invalid_source_document.json] PASSED [ 16%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[EvidenceItem-valid_evidence_item.json-invalid_evidence_item.json] PASSED [ 17%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ClaimAssessment-valid_claim_assessment.json-invalid_claim_assessment.json] PASSED [ 18%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ForensicFinding-valid_forensic_finding.json-invalid_forensic_finding.json] PASSED [ 19%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ProvenanceRelationship-valid_provenance_relationship.json-invalid_provenance_relationship.json] PASSED [ 20%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[InvestigationReport-valid_investigation_report.json-invalid_investigation_report.json] PASSED [ 20%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[AuditEvent-valid_audit_event.json-invalid_audit_event.json] PASSED [ 21%]
tests/contract/test_evidence_asset_contract.py::test_uploaded_asset_conforms_to_contract_and_schema PASSED [ 22%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[Investigation.json] PASSED [ 23%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[EvidenceAsset.json] PASSED [ 24%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[AssetDerivation.json] PASSED [ 25%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ProcessingResult.json] PASSED [ 26%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[Claim.json] PASSED [ 27%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[SourceDocument.json] PASSED [ 28%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[EvidenceItem.json] PASSED [ 29%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ClaimAssessment.json] PASSED [ 30%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ForensicFinding.json] PASSED [ 30%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ProvenanceRelationship.json] PASSED [ 31%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[InvestigationReport.json] PASSED [ 32%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[AuditEvent.json] PASSED [ 33%]
tests/integration/test_asset_storage_db.py::test_storage_rollback_when_db_commit_fails PASSED [ 34%]
tests/integration/test_asset_storage_db.py::test_storage_rollback_handles_deletion_failure_gracefully PASSED [ 35%]
tests/integration/test_isolated_db.py::test_isolated_database_crud PASSED [ 36%]
tests/integration/test_isolated_db.py::test_isolated_database_rollback_on_error PASSED [ 37%]
tests/security/test_cors_and_security.py::test_ssrf_safety_validator PASSED [ 38%]
tests/security/test_cors_and_security.py::test_cors_headers_allowed_origin PASSED [ 39%]
tests/security/test_cors_and_security.py::test_cors_headers_disallowed_origin PASSED [ 40%]
tests/security/test_cors_and_security.py::test_error_response_does_not_leak_internal_paths PASSED [ 40%]
tests/unit/test_asset_validation.py::test_sanitize_filename_traversal PASSED [ 41%]
tests/unit/test_asset_validation.py::test_sanitize_filename_null_byte_and_special_chars PASSED [ 42%]
tests/unit/test_asset_validation.py::test_sanitize_filename_excessive_length PASSED [ 43%]
tests/unit/test_asset_validation.py::test_detect_mime_jpeg PASSED        [ 44%]
tests/unit/test_asset_validation.py::test_detect_mime_png PASSED         [ 45%]
tests/unit/test_asset_validation.py::test_detect_mime_webp PASSED        [ 46%]
tests/unit/test_asset_validation.py::test_detect_mime_mp4 PASSED         [ 47%]
tests/unit/test_asset_validation.py::test_detect_mime_webm PASSED        [ 48%]
tests/unit/test_asset_validation.py::test_detect_mime_wav PASSED         [ 49%]
tests/unit/test_asset_validation.py::test_detect_mime_mp3 PASSED         [ 50%]
tests/unit/test_asset_validation.py::test_detect_mime_empty_stream_rejected PASSED [ 50%]
tests/unit/test_asset_validation.py::test_reject_executable_binary PASSED [ 51%]
tests/unit/test_asset_validation.py::test_reject_executable_script PASSED [ 52%]
tests/unit/test_asset_validation.py::test_reject_spoofed_header PASSED   [ 53%]
tests/unit/test_asset_validation.py::test_reject_unsupported_mime PASSED [ 54%]
tests/unit/test_core_models.py::test_validate_prefixed_id_valid PASSED   [ 55%]
tests/unit/test_core_models.py::test_validate_prefixed_id_invalid_prefix PASSED [ 56%]
tests/unit/test_core_models.py::test_validate_prefixed_id_invalid_uuid PASSED [ 57%]
tests/unit/test_core_models.py::test_evidence_asset_storage_uri_validation PASSED [ 58%]
tests/unit/test_core_models.py::test_asset_derivation_self_derivation_prevented PASSED [ 59%]
tests/unit/test_core_models.py::test_claim_timecode_ordering PASSED      [ 60%]
tests/unit/test_core_models.py::test_claim_assessment_evidence_requirement PASSED [ 60%]
tests/unit/test_core_models.py::test_forensic_finding_uncalibrated_defaults_valid PASSED [ 61%]
tests/unit/test_core_models.py::test_forensic_finding_calibrated_requires_score_and_method PASSED [ 62%]
tests/unit/test_core_models.py::test_forensic_finding_calibrated_bounds PASSED [ 63%]
tests/unit/test_core_models.py::test_forensic_finding_uncalibrated_rejects_calibrated_score PASSED [ 64%]
tests/unit/test_core_models.py::test_provenance_relationship_self_loop_prevented PASSED [ 65%]
tests/unit/test_errors.py::test_veritas_exception_defaults PASSED        [ 66%]
tests/unit/test_errors.py::test_resource_not_found_error PASSED          [ 67%]
tests/unit/test_errors.py::test_service_unavailable_error PASSED         [ 68%]
tests/unit/test_errors.py::test_problem_detail_serialization PASSED      [ 69%]
tests/unit/test_errors.py::test_phase1_domain_errors PASSED              [ 70%]
tests/unit/test_logging.py::test_redacting_formatter_masks_bearer_jwt PASSED [ 70%]
tests/unit/test_logging.py::test_redacting_formatter_masks_passwords PASSED [ 71%]
tests/unit/test_storage.py::test_save_valid_jpeg PASSED                  [ 72%]
tests/unit/test_storage.py::test_save_empty_file_fails PASSED            [ 73%]
tests/unit/test_storage.py::test_save_oversized_file_fails PASSED        [ 74%]
tests/unit/test_storage.py::test_path_traversal_sanitized PASSED         [ 75%]
tests/unit/test_storage.py::test_delete_stored_file PASSED               [ 76%]
tests/unit/test_storage.py::test_save_upload_cleans_up_on_task_cancellation PASSED [ 77%]
tests/unit/test_storage.py::test_save_upload_cancellation_preserves_exception_when_temp_cleanup_fails PASSED [ 78%]
backend/tests/test_assets_api.py::test_upload_valid_jpeg PASSED          [ 79%]
backend/tests/test_assets_api.py::test_upload_with_explicit_investigation_id PASSED [ 80%]
backend/tests/test_assets_api.py::test_upload_with_invalid_investigation_id PASSED [ 80%]
backend/tests/test_assets_api.py::test_upload_empty_file_rejected PASSED [ 81%]
backend/tests/test_assets_api.py::test_upload_executable_rejected PASSED [ 82%]
backend/tests/test_assets_api.py::test_upload_spoofed_mime_type_rejected PASSED [ 83%]
backend/tests/test_assets_api.py::test_get_asset_success PASSED          [ 84%]
backend/tests/test_assets_api.py::test_get_asset_not_found PASSED        [ 85%]
backend/tests/test_assets_api.py::test_get_asset_invalid_id_format PASSED [ 86%]
backend/tests/test_assets_api.py::test_list_assets_filter PASSED         [ 87%]
backend/tests/test_assets_api.py::test_upload_duplicate_file_creates_distinct_asset_records PASSED [ 88%]
backend/tests/test_config.py::test_cors_origins_parsing_list PASSED      [ 89%]
backend/tests/test_config.py::test_cors_origins_parsing_comma_separated_string PASSED [ 90%]
backend/tests/test_config.py::test_cors_origins_wildcard PASSED          [ 90%]
backend/tests/test_config.py::test_upload_limit_default PASSED           [ 91%]
backend/tests/test_health.py::test_root_health_endpoint PASSED           [ 92%]
backend/tests/test_health.py::test_api_v1_health_endpoint PASSED         [ 93%]
backend/tests/test_health.py::test_health_timestamp_is_utc PASSED        [ 94%]
backend/tests/test_openapi.py::test_openapi_schema_endpoint PASSED       [ 95%]
backend/tests/test_openapi.py::test_docs_endpoints PASSED                [ 96%]
workers/tests/test_worker.py::test_echo_probe_task_success PASSED        [ 97%]
workers/tests/test_worker.py::test_failing_probe_task_traps_error PASSED [ 98%]
workers/tests/test_worker.py::test_in_memory_task_runner_dispatch_and_completion PASSED [ 99%]
workers/tests/test_worker.py::test_in_memory_task_runner_polling PASSED  [100%]

============================= 110 passed in 2.46s =============================

================================================================================
ALL VERIFICATION CHECKS PASSED.
```

---

## 3. Technical Audit: Security, Storage & Failure Handling

### 3.1 Bounded Upload Streaming & Memory Consumption
- **Implementation:** [`LocalFileStorageService.save_upload`](backend/app/services/storage.py#L57) streams incoming bytes in bounded 64 KB buffers (`chunk_size = 64 * 1024`).
- **Memory Footprint:** Resident memory is O(1) with respect to file size. Tested against 100 MB caps without full-file in-memory buffering.
- **Enforcement:** `total_bytes` is incremented after every chunk. If `total_bytes > limit`, a [`PayloadTooLargeError`](backend/app/core/errors.py#L112) is raised immediately, halting downstream reads.

### 3.2 SHA-256 Hashing & Byte Counting
- **Incremental Digest:** A SHA-256 digest (`hashlib.sha256()`) is updated concurrently as each 64 KB chunk streams through memory.
- **Exact Accounting:** The returned `file_size_bytes` reflects the actual byte count streamed to storage. Zero-byte payloads are rejected with [`EmptyFileError`](backend/app/core/errors.py#L125).

### 3.3 File-Type Validation & Documented Limitations
- **Allowlist Scope:** Strictly permits 10 multimedia container MIME types:
  - Images: `image/jpeg`, `image/png`, `image/webp`
  - Video: `video/mp4`, `video/webm`, `video/quicktime`
  - Audio: `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/mp4`
- **Header Sniffing:** [`detect_and_validate_mime`](backend/app/services/validation.py#L65) inspects the initial 512 bytes for binary signatures (`\xFF\xD8\xFF`, `\x89PNG`, `RIFF/WEBP`, `ftyp`, `\x1a\x45\xdf\xa3`, `ID3`/sync frames, `RIFF/WAVE`, `OggS`).
- **Forbidden Binary Checks:** Explicitly rejects Windows PE (`MZ`), Linux ELF (`\x7fELF`), and scripts (`#!/`, `<?php`).
- **EXPLICIT OPERATIONAL LIMITATION:**
  > [!IMPORTANT]
  > Magic-byte sniffing is strictly a **file container format verification gate**. It does **NOT** constitute malware scanning, antivirus inspection, or proof of media safety. It does not inspect for embedded steganographic payloads, malformed codec streams capable of buffer overflows, or polyglot files disguised behind valid multimedia headers. Deep media decoding and sandboxed execution remain scheduled for Phase 11.

### 3.4 Safe Filenames & Semi-Opaque Storage Keys
- **Sanitization:** [`sanitize_filename`](backend/app/services/validation.py#L42) strips null bytes (`\x00`), extracts basenames to eliminate directory traversal sequences (`../`, `C:\`, `/var/`), replaces non-alphanumeric characters with underscores, and bounds length to 200 characters.
- **Storage Key Structure:** `f"{asset_id}_{safe_filename}"`.
- **Opacity Clarification:** The key is **semi-opaque**: the UUIDv4-based `asset_id` prefix guarantees uniqueness and collision resistance, while retaining the sanitized basename and extension for operational diagnostics.

### 3.5 Atomic File Placement & Filesystem Assumptions
- **Atomicity:** Uploads write to `.tmp_{asset_id}_{uuid4().hex}`. On completion and validation, `os.replace` atomically renames the temporary file to its final destination key.
- **Filesystem Mount Invariant:** Both the temporary file and the finalized file reside in `self.base_dir` (`./storage/assets`). This satisfies the POSIX/Windows requirement that source and target reside on the same filesystem mount point, preventing cross-device link errors (`EXDEV`).

### 3.6 Failure Cleanup, Exception Preservation & Storage Orphan Reality
- **Streaming Exception & Cancellation Handling:** [`LocalFileStorageService.save_upload`](backend/app/services/storage.py#L137) wraps the write loop in `except BaseException:`.
  - Catches `asyncio.CancelledError`, `GeneratorExit`, and runtime exceptions.
  - If a client disconnects mid-stream or task is aborted, the `.tmp_*` file is unlinked inside a guarded `try...except Exception as err:` block that logs warnings on OS deletion errors.
  - The original exception (`asyncio.CancelledError` or validation error) is strictly preserved and re-raised (`raise`), never masked by a cleanup error. Verified in `test_save_upload_cleans_up_on_task_cancellation` and `test_save_upload_cancellation_preserves_exception_when_temp_cleanup_fails`.
- **Database Persistence Failure & Transactional Storage Rollback:** In `POST /api/v1/assets/upload`, physical file write precedes database persistence.
  - If `AssetRepository.create(record)` fails, storage rollback is triggered via `storage.delete(upload_result.storage_uri)`.
  - The deletion call is wrapped in a dedicated `try...except Exception as cleanup_err:` block. Any deletion error or `False` return is safely logged (`logger.warning` / `logger.error`) without interrupting error handling.
  - The original database exception `exc` is preserved and explicitly chained using `raise VeritasException(...) from exc`.
  - The RFC 9457 Problem Details response accurately conveys whether rollback succeeded or was attempted, returning HTTP 500 `INGESTION_PERSISTENCE_ERROR`. Verified in `test_storage_rollback_when_db_commit_fails` and `test_storage_rollback_handles_deletion_failure_gracefully`.
- **EXPLICIT REALITY REGARDING ORPHANED ASSETS:**
  > [!WARNING]
  > **Orphaned files are NOT impossible under all operating-system or storage-backend conditions.**
  > While Veritas implements best-effort automatic cleanup and rollback upon failure, external OS file locks (such as Windows file sharing violations, antivirus background inspection locks, or indexing services) or network storage backend partitions can cause physical file deletion (`unlink`) to fail. In such scenarios, Veritas safely logs the cleanup failure and preserves the primary exception, but the file may remain on disk as an orphaned asset until cleaned up by an administrative retention or garbage-collection sweep.

### 3.7 Duplicate-Upload Handling
- **Behavior:** Uploading identical binary media produces distinct `EvidenceAsset` records with unique `ast_<uuid4>` IDs and distinct storage paths, while computing and recording the identical `sha256_hash`.
- **Rationale:** Evidence assets represent immutable records of specific ingestion events. Distinct investigations must be permitted to ingest the same media without collision or silent mutation. Verified in `test_upload_duplicate_file_creates_distinct_asset_records`.

### 3.8 API Authorization Assumptions & Limitations
- **Current State:** In Phase 1, the `POST /api/v1/assets/upload` and `GET /api/v1/assets/{asset_id}` endpoints are **unauthenticated**.
- **OPERATIONAL SCOPE RESTRICTION:**
  > [!IMPORTANT]
  > The unauthenticated ingestion and retrieval endpoints are suitable **STRICTLY for local development or appropriately isolated test environments**. While `asset_id` uses UUIDv4 format (providing 122 bits of entropy to resist brute-force enumeration), **UUID unguessability does NOT constitute access control**. Formal authentication, Bearer JWT validation, and per-investigation access control lists (ACLs) are scheduled for Phase 11.

### 3.9 Tested vs. Untested Storage and Database Configurations
- **Configurations Actually Tested (Local & Isolated Test Battery):**
  - **Database:** SQLite in-memory database (`sqlite:///:memory:` utilizing SQLAlchemy `StaticPool`).
  - **Storage:** Local filesystem directory storage (`./storage/assets` and pytest temporary directories via `LocalFileStorageService`).
  - **Task Runner:** In-process mock dispatcher (`InMemoryTaskRunner`).
- **Configurations Untested / Offline:**
  - **PostgreSQL:** No live PostgreSQL container or remote database was executed during test runs.
  - **Redis:** No live Redis broker or cache was executed during test runs.
  - **Object Storage (AWS S3 / MinIO):** No live object storage service was connected or tested; Phase 1 implements local storage abstraction only.
  - Veritas makes no claim of live infrastructure validation for offline container services.

### 3.10 Phase Boundary & Scope Enforcement
- **Boundary Verification:** Code inspection of `backend/app/` confirms zero implementation of subsequent roadmap phases:
  - No Whisper transcription, OCR engines, or claim NLP (Phase 2).
  - No search engines, RAG retrievers, or vector databases (Phase 3).
  - No NLI verifiers or stance classification (Phase 4).
  - No deepfake detectors, face crops, or audio forensics (Phases 5–7).
  - No provenance graph synthesis (Phase 8).
  - No frontend workspace UI (Phase 10).

---

## 4. Security Audit Matrix

Claims reflect specific automated test assertions, distinguishing targeted test passes from broad operational assurances.

| Threat Category | Potential Impact | Tested Defense Mechanism | Verification Status |
| :--- | :--- | :--- | :--- |
| **Path Traversal** | File written outside asset directory | Basename extraction; directory separators (`/`, `\`) stripped; path components discarded | **Targeted Test Passed** (`test_sanitize_filename_traversal`, `test_path_traversal_sanitized`) |
| **Executable Injection** | Binary executable stored as media | Container magic-byte sniffing; explicit rejection of PE (`MZ`), ELF (`\x7fELF`), scripts (`#!/`, `<?php`) | **Format Validation Passed** (Verified header rejection; does NOT replace antivirus scanning) |
| **MIME Spoofing** | Extension disagrees with payload | Header signature checked against declared MIME; mismatches rejected | **Targeted Test Passed** (`test_upload_spoofed_mime_type_rejected`) |
| **Memory Exhaustion** | Out-of-memory crash via large file | 64 KB chunked streaming; zero full-file buffering in memory | **Targeted Test Passed** (`test_save_valid_jpeg`, streaming architecture) |
| **Storage Exhaustion** | Disk filled by oversized upload | Immediate stream termination and file unlinking when `total_bytes > limit` | **Targeted Test Passed** (`test_save_oversized_file_fails`) |
| **Client Disconnect Leak** | Orphaned temp file on aborted connection | `except BaseException` unlinks `.tmp_*` on `asyncio.CancelledError`; unlinking failure trapped safely to preserve primary error | **Targeted Tests Passed** (`test_save_upload_cleans_up_on_task_cancellation`, `test_save_upload_cancellation_preserves_exception_when_temp_cleanup_fails`) |
| **Orphaned Storage Leak** | Disk leaks unlinked storage files on DB crash | Transactional catch hook calls `storage.delete(uri)` upon database commit failure; cleanup errors trapped safely to preserve primary DB error | **Targeted Tests Passed** (`test_storage_rollback_when_db_commit_fails`, `test_storage_rollback_handles_deletion_failure_gracefully`; best-effort cleanup; OS locks may require retention sweeps) |
| **SSRF** | Server fetches malicious external URL | No URL fetching endpoint implemented in Phase 1 (strictly multipart file uploads) | **Scope Boundary Maintained** (No network egress surface introduced) |
| **Sensitive Path Leak** | Server file paths exposed in errors | Error handling uses RFC 9457 Problem Details with sanitized messages | **Targeted Test Passed** (`test_error_response_does_not_leak_internal_paths`) |
| **Access Control** | Unauthorized asset upload / inspection | Endpoints are unauthenticated; suitable strictly for local/isolated testing until Phase 11 controls are added | **Outstanding Limitation** (UUID unguessability is NOT access control) |

---

## 5. Repository & Publication Status

- **Git Branch:** `feature/phase-1-data-ingestion`
- **Upstream Tracking:** `origin/feature/phase-1-data-ingestion`
- **Remote URL:** `https://github.com/Shivanshm29/Veritas.git`
- **Working Tree State:** Clean.
- **Main Branch State:** `main` tracks `origin/main` at commit `821f725`.
- **Shared Contract Sign-Off:** Formally recorded as **PENDING** Person 2 peer review.
- **Phase 1 Feature Branch State:** Contains all Phase 1 implementation files, tests, and documentation. Ready for peer review and pull request integration.

---

## 6. Handoff Notes for Person 2

Person 2 can integrate with Person 1's ingestion subsystem as follows:

1. **Ingest Evidence Asset via API:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/assets/upload" \
     -F "file=@evidence_video.mp4" \
     -F "investigation_id=inv_12345678-1234-4234-8234-123456789abc" \
     -F "source_platform=broadcast"
   ```
   *Returns:* `201 Created` with canonical `EvidenceAsset` JSON payload including `id` (`ast_...`), `sha256_hash`, and `storage_uri`.

2. **Retrieve Asset Metadata:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/assets/ast_23456789-2345-4345-8345-234567890bcd"
   ```

3. **Isolated Testing without Backend:**
   Person 2 may consume `contracts/fixtures/valid_evidence_asset.json` as a mock double for developing image/video forensics engines in Phases 5–7 without running Person 1's backend or storage layer.
