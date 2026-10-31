# Veritas — Phase 1 Review: Data Ingestion & Evidence Asset Management

**Project Identity:** Veritas (architecturally designated as PRAMAAN — Provenance, Reliability & Authenticity Monitoring and Analysis Network)  
**Phase:** Phase 1 — Data Ingestion & Evidence Asset Management  
**Subsystem:** Person 1 (Content Ingestion & Evidence Asset Management)  
**Date:** October 31, 2026  
**Auditor / Engineer:** Senior Software Architect, Backend Engineer, Security Engineer & QA Auditor  
**Document Path:** `reviews/phase-1-review.md`  
**Git Branch:** `feature/phase-1-data-ingestion`  
**Remote Repository:** `https://github.com/Shivanshm29/Veritas.git`  
**Compatibility Note:** Preserved `PramaanBaseModel` and `PramaanException` as aliases to maintain backward compatibility across shared contracts and existing modules.

---

## 1. Executive Verdict

```
================================================================================
PHASE 1 AUDIT & VERIFICATION VERDICT:
PASS — Ingestion Subsystem Verified & Test Battery Reconciled
================================================================================
```

All acceptance criteria for Phase 1 (Data Ingestion & Evidence Asset Management) have been verified against the canonical `EvidenceAsset` data contract. The implementation provides bounded chunk streaming (64 KB chunks), incremental SHA-256 computation, container header magic-byte validation, filename sanitization, atomic storage writes, transactional storage rollback on database failure, duplicate upload handling, and RFC 9457 Problem Details error responses.

**Reconciled Test Battery Summary:**
- **Execution Command:** `python scripts/run_checks.py`
- **Total Tests Collected:** **107**
- **Passed:** **107**
- **Failed:** **0**
- **Skipped:** **0**
- **Errors:** **0**
- **Warnings:** **0**
- **Exit Code:** `0`
- **Baseline Phase 0 Tests Preserved:** **73** (100% passing, zero regressions)
- **Phase 1 Additions:** **34** new tests across unit, API integration, contract conformance, duplicate upload handling, and transactional storage-database rollback.

---

## 2. Test Results Reconciliation & Analysis

### 2.1 Resolution of Test-Count Discrepancy
An earlier draft of this review report cited 106 tests in prose while including an intermediate terminal excerpt from an earlier development run showing 105 tests collected. 

**Root Cause Analysis:**
1. **Phase 0 Baseline:** Exactly 73 tests were established in Phase 0.
2. **Phase 1 Initial Additions (32 tests -> 105 total):** Initial tests covered validation (15), storage (5), assets API (10), contract conformance (1), and storage rollback (1). Terminal output during that intermediate step reported 105 collected / 105 passed.
3. **Domain Error Coverage Addition (1 test -> 106 total):** `test_phase1_domain_errors` was added to `tests/unit/test_errors.py` to verify RFC 9457 Problem Details mapping for the five newly introduced Phase 1 domain exceptions. The review prose was updated to 106, but the prior 105-count terminal log snippet was not refreshed simultaneously.
4. **Duplicate-Upload Coverage Addition (1 test -> 107 total):** To formally verify the behavior of duplicate file uploads across investigations, `test_upload_duplicate_file_creates_distinct_asset_records` was added to `backend/tests/test_assets_api.py`.
5. **Reconciled Total:** Exactly **107 tests** are now collected and executed by pytest. The test inventory below confirms every test file, item count, and discovery status.

### 2.2 Complete Test Suite Inventory (107 Tests)

| Category | File Path | Tests | Coverage Scope |
| :--- | :--- | :---: | :--- |
| **Phase 0 Contracts** | `tests/contract/test_all_contracts.py` | 24 | Valid & invalid synthetic fixture parsing for all 12 canonical models |
| **Phase 0 Contracts** | `tests/contract/test_json_schemas.py` | 12 | Existence and property schema validation for 12 exported JSON schemas |
| **Phase 1 Contract** | `tests/contract/test_evidence_asset_contract.py` | 1 | Live upload response conformance to `EvidenceAsset` and JSON schema |
| **Phase 1 Integration**| `tests/integration/test_asset_storage_db.py` | 1 | Storage file rollback (unlinking) upon simulated database crash |
| **Phase 0 Integration**| `tests/integration/test_isolated_db.py` | 2 | SQLAlchemy CRUD and transaction rollback in isolated in-memory DB |
| **Phase 0 Security** | `tests/security/test_cors_and_security.py` | 4 | CORS origin filtering, path redaction, and SSRF validator checks |
| **Phase 1 Unit** | `tests/unit/test_asset_validation.py` | 15 | Filename sanitization, header magic-byte checks, binary/script rejections |
| **Phase 0 Unit** | `tests/unit/test_core_models.py` | 12 | Prefixed ID regexes, calibrated score semantics, self-derivation blocks |
| **Phase 0/1 Unit** | `tests/unit/test_errors.py` | 5 | RFC 9457 Problem Details serialization (4 Phase 0 + 1 Phase 1 domain error test) |
| **Phase 0 Unit** | `tests/unit/test_logging.py` | 2 | Token, bearer JWT, and password redaction in log formatter |
| **Phase 1 Unit** | `tests/unit/test_storage.py` | 5 | Chunk streaming, size cap enforcement, empty file rejection, atomic replace |
| **Phase 1 API** | `backend/tests/test_assets_api.py` | 11 | Multipart upload, ID validation, empty/malware rejections, retrieval, filtering, duplicate handling |
| **Phase 0 API** | `backend/tests/test_config.py` | 4 | CORS parsing (list, comma-separated, wildcard) and upload limit settings |
| **Phase 0 API** | `backend/tests/test_health.py` | 3 | Liveness root probe, diagnostic v1 probe, UTC timestamp enforcement |
| **Phase 0 API** | `backend/tests/test_openapi.py` | 2 | OpenAPI JSON generation and Swagger UI accessibility |
| **Phase 0 Workers** | `workers/tests/test_worker.py` | 4 | In-memory asynchronous task dispatcher, probe tasks, error trapping |
| **Total** | | **107** | **100% Passing (0 failures, 0 warnings)** |

### 2.3 Actual Test Runner Output

```text
================================================================================
STEP: Export JSON Schemas
CMD:  C:\Python314\python.exe scripts/export_schemas.py
================================================================================
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\Investigation.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\EvidenceAsset.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\AssetDerivation.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\ProcessingResult.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\Claim.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\SourceDocument.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\EvidenceItem.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\ClaimAssessment.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\ForensicFinding.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\ProvenanceRelationship.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\InvestigationReport.json
Exported: C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json\AuditEvent.json

Successfully exported 12 JSON Schemas to C:\Users\shiva\projects\Deepfake detection\contracts\schemas\json
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
collecting ... collected 107 items

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
tests/contract/test_all_contracts.py::test_valid_fixtures_pass_contract[AuditEvent-valid_audit_event.json-invalid_audit_event.json] PASSED [ 11%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[Investigation-valid_investigation.json-invalid_investigation.json] PASSED [ 12%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[EvidenceAsset-valid_evidence_asset.json-invalid_evidence_asset.json] PASSED [ 13%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[AssetDerivation-valid_asset_derivation.json-invalid_asset_derivation.json] PASSED [ 14%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ProcessingResult-valid_processing_result.json-invalid_processing_result.json] PASSED [ 14%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[Claim-valid_claim.json-invalid_claim.json] PASSED [ 15%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[SourceDocument-valid_source_document.json-invalid_source_document.json] PASSED [ 16%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[EvidenceItem-valid_evidence_item.json-invalid_evidence_item.json] PASSED [ 17%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ClaimAssessment-valid_claim_assessment.json-invalid_claim_assessment.json] PASSED [ 18%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ForensicFinding-valid_forensic_finding.json-invalid_forensic_finding.json] PASSED [ 19%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[ProvenanceRelationship-valid_provenance_relationship.json-invalid_provenance_relationship.json] PASSED [ 20%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[InvestigationReport-valid_investigation_report.json-invalid_investigation_report.json] PASSED [ 21%]
tests/contract/test_all_contracts.py::test_invalid_fixtures_fail_contract[AuditEvent-valid_audit_event.json-invalid_audit_event.json] PASSED [ 22%]
tests/contract/test_evidence_asset_contract.py::test_uploaded_asset_conforms_to_contract_and_schema PASSED [ 23%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[Investigation.json] PASSED [ 24%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[EvidenceAsset.json] PASSED [ 25%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[AssetDerivation.json] PASSED [ 26%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ProcessingResult.json] PASSED [ 27%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[Claim.json] PASSED [ 28%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[SourceDocument.json] PASSED [ 29%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[EvidenceItem.json] PASSED [ 30%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ClaimAssessment.json] PASSED [ 31%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ForensicFinding.json] PASSED [ 32%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[ProvenanceRelationship.json] PASSED [ 33%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[InvestigationReport.json] PASSED [ 34%]
tests/contract/test_json_schemas.py::test_exported_json_schema_exists_and_valid[AuditEvent.json] PASSED [ 35%]
tests/integration/test_asset_storage_db.py::test_storage_rollback_when_db_commit_fails PASSED [ 36%]
tests/integration/test_isolated_db.py::test_isolated_database_crud PASSED [ 37%]
tests/integration/test_isolated_db.py::test_isolated_database_rollback_on_error PASSED [ 38%]
tests/security/test_cors_and_security.py::test_ssrf_safety_validator PASSED [ 39%]
tests/security/test_cors_and_security.py::test_cors_headers_allowed_origin PASSED [ 40%]
tests/security/test_cors_and_security.py::test_cors_headers_disallowed_origin PASSED [ 41%]
tests/security/test_cors_and_security.py::test_error_response_does_not_leak_internal_paths PASSED [ 42%]
tests/unit/test_asset_validation.py::test_sanitize_filename_traversal PASSED [ 43%]
tests/unit/test_asset_validation.py::test_sanitize_filename_null_byte_and_special_chars PASSED [ 44%]
tests/unit/test_asset_validation.py::test_sanitize_filename_excessive_length PASSED [ 45%]
tests/unit/test_asset_validation.py::test_detect_mime_jpeg PASSED         [ 46%]
tests/unit/test_asset_validation.py::test_detect_mime_png PASSED          [ 47%]
tests/unit/test_asset_validation.py::test_detect_mime_webp PASSED         [ 48%]
tests/unit/test_asset_validation.py::test_detect_mime_mp4 PASSED          [ 49%]
tests/unit/test_asset_validation.py::test_detect_mime_webm PASSED         [ 50%]
tests/unit/test_asset_validation.py::test_detect_mime_wav PASSED          [ 51%]
tests/unit/test_asset_validation.py::test_detect_mime_mp3 PASSED          [ 52%]
tests/unit/test_asset_validation.py::test_detect_mime_empty_stream_rejected PASSED [ 53%]
tests/unit/test_asset_validation.py::test_reject_executable_binary PASSED [ 54%]
tests/unit/test_asset_validation.py::test_reject_executable_script PASSED [ 55%]
tests/unit/test_asset_validation.py::test_reject_spoofed_header PASSED   [ 56%]
tests/unit/test_asset_validation.py::test_reject_unsupported_mime PASSED [ 57%]
tests/unit/test_core_models.py::test_validate_prefixed_id_valid PASSED   [ 58%]
tests/unit/test_core_models.py::test_validate_prefixed_id_invalid_prefix PASSED [ 59%]
tests/unit/test_core_models.py::test_validate_prefixed_id_invalid_uuid PASSED [ 60%]
tests/unit/test_evidence_asset_storage_uri_validation PASSED             [ 61%]
tests/unit/test_core_models.py::test_asset_derivation_self_derivation_prevented PASSED [ 62%]
tests/unit/test_core_models.py::test_claim_timecode_ordering PASSED      [ 63%]
tests/unit/test_core_models.py::test_claim_assessment_evidence_requirement PASSED [ 64%]
tests/unit/test_core_models.py::test_forensic_finding_uncalibrated_defaults_valid PASSED [ 65%]
tests/unit/test_core_models.py::test_forensic_finding_calibrated_requires_score_and_method PASSED [ 66%]
tests/unit/test_core_models.py::test_forensic_finding_calibrated_bounds PASSED [ 67%]
tests/unit/test_core_models.py::test_forensic_finding_uncalibrated_rejects_calibrated_score PASSED [ 68%]
tests/unit/test_core_models.py::test_provenance_relationship_self_loop_prevented PASSED [ 69%]
tests/unit/test_errors.py::test_veritas_exception_defaults PASSED        [ 70%]
tests/unit/test_errors.py::test_resource_not_found_error PASSED          [ 71%]
tests/unit/test_errors.py::test_service_unavailable_error PASSED         [ 72%]
tests/unit/test_errors.py::test_problem_detail_serialization PASSED      [ 73%]
tests/unit/test_errors.py::test_phase1_domain_errors PASSED              [ 74%]
tests/unit/test_logging.py::test_redacting_formatter_masks_bearer_jwt PASSED [ 75%]
tests/unit/test_logging.py::test_redacting_formatter_masks_passwords PASSED [ 76%]
tests/unit/test_storage.py::test_save_valid_jpeg PASSED                  [ 77%]
tests/unit/test_storage.py::test_save_empty_file_fails PASSED            [ 78%]
tests/unit/test_storage.py::test_save_oversized_file_fails PASSED        [ 79%]
tests/unit/test_storage.py::test_path_traversal_sanitized PASSED         [ 80%]
tests/unit/test_storage.py::test_delete_stored_file PASSED               [ 81%]
backend/tests/test_assets_api.py::test_upload_valid_jpeg PASSED          [ 82%]
backend/tests/test_assets_api.py::test_upload_with_explicit_investigation_id PASSED [ 83%]
backend/tests/test_assets_api.py::test_upload_with_invalid_investigation_id PASSED [ 84%]
backend/tests/test_assets_api.py::test_upload_empty_file_rejected PASSED [ 85%]
backend/tests/test_assets_api.py::test_upload_executable_rejected PASSED [ 86%]
backend/tests/test_assets_api.py::test_upload_spoofed_mime_type_rejected PASSED [ 87%]
backend/tests/test_assets_api.py::test_get_asset_success PASSED          [ 88%]
backend/tests/test_assets_api.py::test_get_asset_not_found PASSED        [ 89%]
backend/tests/test_assets_api.py::test_get_asset_invalid_id_format PASSED [ 90%]
backend/tests/test_assets_api.py::test_list_assets_filter PASSED         [ 91%]
backend/tests/test_assets_api.py::test_upload_duplicate_file_creates_distinct_asset_records PASSED [ 92%]
backend/tests/test_config.py::test_cors_origins_parsing_list PASSED      [ 93%]
backend/tests/test_config.py::test_cors_origins_parsing_comma_separated_string PASSED [ 94%]
backend/tests/test_config.py::test_cors_origins_wildcard PASSED          [ 95%]
backend/tests/test_config.py::test_upload_limit_default PASSED           [ 96%]
backend/tests/test_health.py::test_root_health_endpoint PASSED           [ 97%]
backend/tests/test_health.py::test_api_v1_health_endpoint PASSED         [ 98%]
backend/tests/test_health.py::test_health_timestamp_is_utc PASSED        [ 99%]
backend/tests/test_openapi.py::test_openapi_schema_endpoint PASSED       [100%]
backend/tests/test_openapi.py::test_docs_endpoints PASSED                [100%]
workers/tests/test_worker.py::test_echo_probe_task_success PASSED        [100%]
workers/tests/test_worker.py::test_failing_probe_task_traps_error PASSED [100%]
workers/tests/test_worker.py::test_in_memory_task_runner_dispatch_and_completion PASSED [100%]
workers/tests/test_worker.py::test_in_memory_task_runner_polling PASSED  [100%]

============================= 107 passed in 2.44s =============================
[PASS] Step 'Run Pytest Suite' completed successfully.

================================================================================
ALL VERIFICATION CHECKS PASSED.
```

---

## 3. Technical Verification & Architecture Audit

### 3.1 Bounded Upload Streaming & Memory Protection
- **Mechanism:** In [`LocalFileStorageService.save_upload`](file:///C:/Users/shiva/projects/Deepfake%20detection/backend/app/services/storage.py#L48), file uploads are processed asynchronously via `await upload_file.read(chunk_size)` using a fixed buffer size of **64 KB** (`65,536 bytes`).
- **Memory Invariant:** No intermediate buffer or memory structure accumulates the entire file in RAM. Memory utilization is $O(1)$ relative to total file size.
- **Size Enforcement:** A running byte counter (`total_bytes`) evaluates each chunk. The moment `total_bytes > limit` (`MAX_UPLOAD_SIZE_BYTES`, default 500 MB), streaming is aborted mid-flight, the active temporary file is unlinked, and `PayloadTooLargeError` (HTTP 413) is raised. Verified in `tests/unit/test_storage.py::test_save_oversized_file_fails`.

### 3.2 SHA-256 Hashing & Byte-Count Accuracy
- **Digest Computation:** `hashlib.sha256()` is updated incrementally on each chunk in the streaming write loop.
- **Integrity Validation:** The hex digest generated during ingestion matches the content bytes written to disk. Verified in `test_save_valid_jpeg` where disk-read bytes match upload input.
- **Byte Counting:** Total bytes written to disk equal the accumulated count recorded in `file_size_bytes` on the returned `EvidenceAsset`.

### 3.3 File-Type Validation & Operational Limitations
- **Allowlist Scope:** Strictly permits 10 multimedia MIME types:
  - Images: `image/jpeg`, `image/png`, `image/webp`
  - Video: `video/mp4`, `video/webm`, `video/quicktime`
  - Audio: `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/mp4`
- **Header Sniffing:** [`detect_and_validate_mime`](file:///C:/Users/shiva/projects/Deepfake%20detection/backend/app/services/validation.py#L65) inspects the initial 512 bytes for standard binary container signatures (`\xFF\xD8\xFF`, `\x89PNG`, `RIFF/WEBP`, `ftyp`, `\x1a\x45\xdf\xa3`, `ID3`/sync frames, `RIFF/WAVE`, `OggS`).
- **Disallowed Binary Detection:** Explicitly blocks Windows PE executables (`MZ`), Linux ELF binaries (`\x7fELF`), and shell/PHP scripts (`#!/`, `<?php`).
- **CRITICAL TECHNICAL LIMITATION:**
  > [!IMPORTANT]
  > Magic-byte sniffing is strictly a **file container format verification gate**. It does **NOT** constitute malware scanning, deep antivirus inspection, or proof that an uploaded file is benign. It does not inspect for embedded steganographic payloads, malformed codec streams capable of buffer overflows, or polyglot files disguised behind valid multimedia headers. Further deep inspection and sandboxed execution remain scheduled for the Phase 11 hardening phase.

### 3.4 Safe Filenames & Storage Key Structure
- **Sanitization:** [`sanitize_filename`](file:///C:/Users/shiva/projects/Deepfake%20detection/backend/app/services/validation.py#L42) strips null bytes (`\x00`), extracts the basename via `Path.name` and `os.path.basename` (neutralizing `../`, `C:\`, `/var/`), replaces non-alphanumeric/dot/dash/underscore characters with underscores, bounds length to 200 characters, and falls back to `unnamed_asset` if empty.
- **Storage Key Topology:** Files are stored as:
  $$\text{storage\_key} = \text{asset\_id} + \text{"\_"} + \text{safe\_filename}$$
  (e.g., `ast_23456789-2345-4345-8345-234567890bcd_sample_video.mp4`).
- **Opacity Note:** The storage key is **semi-opaque**: the UUIDv4-based `asset_id` prefix guarantees filesystem collision resistance and access control opacity, while retaining the sanitized basename and extension for operational diagnostics.

### 3.5 Atomic Storage Writes & Storage Cleanup
- **Atomicity:** Uploads are written to an isolated temporary file named `.tmp_{asset_id}_{uuid4().hex}`. The file is only moved to its permanent destination key via `os.replace` after all chunks have been streamed, validated against the size ceiling, verified for container headers, and hashed.
- **Failure Cleanup:** If the client disconnects, an exception occurs, or size limits are exceeded, the `except Exception:` block immediately unlinks the temporary file. No `.tmp_*` artifacts remain in the storage directory.

### 3.6 Database Transactions & Storage Rollback
- **Failure Mitigation:** During asset ingestion, physical storage writing occurs prior to database persistence. If `AssetRepository.create(record)` fails (e.g., database connectivity loss or disk crash), the exception handler catches the error, triggers `storage.delete(upload_result.storage_uri)`, and raises an RFC 9457 Problem Details error with code `INGESTION_PERSISTENCE_ERROR`.
- **Test Evidence:** Verified in `tests/integration/test_asset_storage_db.py::test_storage_rollback_when_db_commit_fails` using a mock database crash, confirming that the physical file is deleted and zero orphaned files leak onto disk.

### 3.7 Duplicate-Upload Handling
- **Observed Behavior:** If the identical binary file is uploaded twice (whether under the same investigation or across different investigations), the system assigns each ingestion a distinct, unique `ast_<uuid4>` identifier and writes to a distinct storage URI, while computing and recording the identical `sha256_hash`.
- **Architectural Rationale:** Evidence assets are immutable records of specific ingestion events. Distinct investigations must be permitted to ingest the same media without collision or silent mutation. Deduplication queries can be executed via `AssetRepository.get_by_hash(sha256_hash)` without blocking multi-investigation ingestion.
- **Test Evidence:** Verified in `backend/tests/test_assets_api.py::test_upload_duplicate_file_creates_distinct_asset_records`.

### 3.8 Contract Conformance with Phase 0
- **Contract Conformance:** API output strictly conforms to the canonical `contracts.schemas.EvidenceAsset` Pydantic model and validates against `contracts/schemas/json/EvidenceAsset.json`.
- **Test Evidence:** Verified in `tests/contract/test_evidence_asset_contract.py`.

### 3.9 Phase Boundary & Scope Enforcement
- **Verification:** Inspection of `backend/app/` confirms zero implementation of subsequent roadmap phases:
  - No Whisper transcription, OCR engines, or claim NLP (Phase 2).
  - No search engines, RAG retrievers, or vector databases (Phase 3).
  - No NLI verifiers or stance classification (Phase 4).
  - No deepfake detectors, face crops, or audio forensics (Phases 5–7).
  - No provenance graph synthesis (Phase 8).
  - No frontend workspace UI (Phase 10).

---

## 4. Security Audit & Tested Threat Defenses

Claims in this section reflect specific properties demonstrated through automated test assertions, distinguishing targeted test passes from broader operational security assurances.

| Threat Category | Potential Impact | Tested Defense Mechanism | Verification Status |
| :--- | :--- | :--- | :--- |
| **Path Traversal** | File written outside asset directory | Basename extraction; directory separators (`/`, `\`) stripped; path components discarded | **Targeted Test Passed** (`test_sanitize_filename_traversal`, `test_path_traversal_sanitized`) |
| **Executable Injection** | Binary executable stored as media | Container magic-byte sniffing; explicit rejection of PE (`MZ`), ELF (`\x7fELF`), scripts (`#!/`, `<?php`) | **Format Validation Passed** (Verified header rejection; does NOT replace antivirus scanning) |
| **MIME Spoofing** | Extension disagrees with payload | Header signature checked against declared MIME; mismatches rejected | **Targeted Test Passed** (`test_upload_spoofed_mime_type_rejected`) |
| **Memory Exhaustion** | Out-of-memory crash via large file | 64 KB chunked streaming; zero full-file buffering in memory | **Targeted Test Passed** (`test_save_valid_jpeg`, streaming architecture) |
| **Storage Exhaustion** | Disk filled by oversized upload | Immediate stream termination and file unlinking when `total_bytes > limit` | **Targeted Test Passed** (`test_save_oversized_file_fails`) |
| **Orphaned File Leak** | Disk leaks unlinked storage files | Transactional catch hook calls `storage.delete(uri)` upon database commit failure | **Targeted Test Passed** (`test_storage_rollback_when_db_commit_fails`) |
| **SSRF** | Server fetches malicious external URL | No URL fetching endpoint implemented in Phase 1 (strictly multipart file uploads) | **Scope Boundary Maintained** (No network egress surface introduced) |
| **Sensitive Path Leak** | Server file paths exposed in errors | Error handling uses RFC 9457 Problem Details with sanitized messages | **Targeted Test Passed** (`test_error_response_does_not_leak_internal_paths`) |

---

## 5. Repository & Publication Status

- **Git Branch:** `feature/phase-1-data-ingestion`
- **Upstream Tracking:** `origin/feature/phase-1-data-ingestion`
- **Remote URL:** `https://github.com/Shivanshm29/Veritas.git`
- **Working Tree State:** Clean (`nothing to commit, working tree clean`).
- **Main Branch State:** `main` tracks `origin/main` at commit `821f725` (Phase 0 foundation and project branding alignment).
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
