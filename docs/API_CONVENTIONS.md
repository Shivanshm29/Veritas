# Veritas — API & Contract Conventions

> **Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
> **Document:** API Design Standards, Serialization Conventions & Wire Protocol  
> **Compliance Standard:** RFC 9457 (Problem Details), ISO 8601 (Time), SemVer 2.0 (Versioning)  
> **Backward Compatibility Note:** Technical identifiers such as `PramaanBaseModel` and `PramaanException` are preserved as aliases for backward compatibility.  

---

## 1. API Versioning & Route Prefixes

All public HTTP endpoints must include explicit version path segments:

- Canonical Prefix: `/api/v1/`
- Diagnostics Prefix: `/health` (root health probe) and `/api/v1/health` (versioned diagnostic probe)
- Semantic Versioning: API releases adhere to SemVer `MAJOR.MINOR.PATCH`:
  - `MAJOR`: Breaking schema modifications, required parameter additions, or field removals.
  - `MINOR`: Backward-compatible additive changes (optional parameters, new endpoints).
  - `PATCH`: Bug fixes, security patches, documentation enhancements.

---

## 2. Naming & Serialization Conventions

- **JSON Keys:** Strictly lowercase `snake_case` (e.g., `file_size_bytes`, `investigation_id`, `created_at`). CamelCase or PascalCase is prohibited in JSON payloads.
- **Enums:** UPPERCASE string representations with underscores (e.g., `IN_PROGRESS`, `LIKELY_SYNTHETIC`, `SUPPORTED`).
- **Null Handling:** Optional fields with no value must be serialized as `null` or omitted where explicitly typed as `Optional[T] = None`.
- **Character Encoding:** UTF-8 is mandatory for all requests and responses (`Content-Type: application/json; charset=utf-8`).

---

## 3. Stable Identifier Formats

All entities utilize globally unique, stable string identifiers consisting of an entity-specific **3-letter lowercase prefix**, an underscore separator, and a standard RFC 4122 **UUIDv4**:

$$\text{Identifier} = \text{prefix} + \text{"\_"} + \text{UUIDv4}$$

| Entity | Prefix | Regex Validation Pattern | Example |
| :--- | :--- | :--- | :--- |
| **Investigation** | `inv_` | `^inv_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `inv_12345678-1234-4234-8234-123456789abc` |
| **EvidenceAsset** | `ast_` | `^ast_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `ast_23456789-2345-4345-8345-234567890bcd` |
| **AssetDerivation** | `drv_` | `^drv_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `drv_34567890-3456-4456-8456-345678901cde` |
| **ProcessingResult** | `res_` | `^res_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `res_45678901-4567-4567-8567-456789012def` |
| **Claim** | `clm_` | `^clm_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `clm_56789012-5678-4678-8678-567890123ef0` |
| **SourceDocument** | `doc_` | `^doc_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `doc_67890123-6789-4789-8789-678901234f01` |
| **EvidenceItem** | `evi_` | `^evi_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `evi_78901234-7890-4890-8890-789012345012` |
| **ClaimAssessment**| `asm_` | `^asm_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `asm_89012345-8901-4901-8901-890123456123` |
| **ForensicFinding** | `fnd_` | `^fnd_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `fnd_90123456-9012-4012-8012-901234567234` |
| **ProvenanceRelationship** | `rel_` | `^rel_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `rel_01234567-0123-4123-8123-012345678345` |
| **InvestigationReport** | `rpt_` | `^rpt_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `rpt_12345678-90ab-4cde-8f01-23456789abcd` |
| **AuditEvent** | `adt_` | `^adt_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` | `adt_23456789-01bc-4def-9012-3456789abcde` |

---

## 4. Timestamps & Timezones

- **Timezone Standard:** Strict **UTC** only. Local workstation timezones and naive datetimes are forbidden.
- **Format:** ISO 8601 with microsecond precision and an explicit `Z` suffix:
  $$\text{YYYY-MM-DDTHH:MM:SS.ffffffZ}$$
- **Example:** `2026-10-31T11:46:05.123456Z`

---

## 5. Error Responses: RFC 9457 Problem Details

All error responses (HTTP status codes 400 to 599) must be returned in RFC 9457 / RFC 7807 compliant structure (`Content-Type: application/problem+json`):

```json
{
  "type": "https://veritas.org/errors/RESOURCE_NOT_FOUND",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "EvidenceAsset with id 'ast_23456789-2345-4345-8345-234567890bcd' does not exist.",
  "instance": "/api/v1/assets/ast_23456789-2345-4345-8345-234567890bcd",
  "code": "ASSET_NOT_FOUND",
  "invalid_params": [],
  "timestamp": "2026-10-31T11:46:05.000000Z"
}
```

### Common HTTP Status Codes

| Code | Meaning | Usage in Veritas |
| :--- | :--- | :--- |
| **200 OK** | Success | Synchronous reads (`GET`) and idempotent updates (`PUT`). |
| **201 Created** | Resource Created | Synchronous resource creation (`POST /investigations`). |
| **202 Accepted** | Asynchronous Job | Long-running tasks (`POST /assets`, `POST /claims/verify`). Returns Job object with status polling URL. |
| **400 Bad Request** | Malformed Request | Syntax errors, unparseable JSON, illegal query parameters. |
| **401 Unauthorized** | Missing / Invalid Auth | Missing or expired Bearer token. |
| **403 Forbidden** | Insufficient Rights | Valid token, but actor role lacks permission for the resource. |
| **404 Not Found** | Missing Entity | Resource with the specified ID does not exist. |
| **409 Conflict** | State Conflict | Duplicate entity, hash collision, or illegal state transition. |
| **422 Unprocessable**| Validation Error | Syntactically valid JSON failing Pydantic business rules. |
| **500 Internal Error**| Server Fault | Unhandled exception (masked in production, correlation ID logged). |
| **503 Unavailable** | Dependency Offline | Required backend component (database, storage) is unreachable. |

---

## 6. Pagination & Filtering Standards

Collection endpoints returning lists of entities must support offset-based pagination:

### Query Parameters
- `limit` (integer, default: `20`, maximum: `100`): Maximum records to return.
- `offset` (integer, default: `0`, minimum: `0`): Zero-indexed record offset.
- `sort_by` (string, default: `"created_at"`): Attribute to sort by.
- `order` (string, enum: `["asc", "desc"]`, default: `"desc"`).

### Response Schema
```json
{
  "items": [],
  "total": 142,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

---

## 7. Backward-Compatibility & Contract Evolution

To maintain compatibility between Person 1 and Person 2 without forced synchronous deployments:

1. **Additive Compatibility:** Adding optional fields to request or response schemas is backward-compatible.
2. **Schema Freezing:** Existing fields and enum choices must not be renamed or removed within the same major version (`v1`).
3. **Strict Validation Mode:** Person 1 and Person 2 serializers must use `extra="ignore"` on inputs where appropriate or coordinate schema updates prior to enforcing `extra="forbid"`.
4. **Deprecation Strategy:** When replacing field semantics (e.g. `raw_score_type` replacing `score_type`), legacy aliases are maintained for at least one minor release cycle.

---

## 8. Forensic Scoring & Graph Invariant Conventions

1. **Forensic Detector Scores:**
   - Raw model scores (`raw_score`) represent unnormalized logits, distances, or anomaly scores and are typed by `RawScoreType`.
   - Calibrated scores (`calibrated_score`) are strictly bounded in $[0.0, 1.0]$ and must be accompanied by explicit `calibration_method` and non-fabricated `calibration_metadata`.
   - A bounded score is **never** implicitly assumed to be a well-calibrated probability without empirical validation (e.g., Platt scaling, isotonic regression).
2. **Graph Invariant Enforcement:**
   - Contract-level validators (e.g. `AssetDerivation.check_direct_self_reference`) only enforce single-record invariants such as preventing immediate self-loops (`derived != parent`).
   - Global graph acyclicity (DAG verification across paths $A \to B \to C \to A$) is strictly an algorithmic responsibility of the graph layer (Phase 8), not individual REST payload validators.


