# Veritas — Core Backend Subsystem

**Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
**Directory:** `backend/`  
**Purpose:** FastAPI REST Services for Person 1 Pipeline Endpoints  

---

## 1. Quickstart

### Start Development Server
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Interactive Documentation
- OpenAPI Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc UI: `http://localhost:8000/api/v1/redoc`
- OpenAPI JSON Spec: `http://localhost:8000/api/v1/openapi.json`

---

## 2. Health Endpoints

- **Root Liveness Probe:** `GET http://localhost:8000/health`  
  Returns:
  ```json
  {
    "status": "healthy",
    "service": "Veritas Core Backend",
    "version": "0.1.0",
    "environment": "development",
    "timestamp": "2026-10-31T11:46:05.000000Z"
  }
  ```

- **Detailed Diagnostic Probe:** `GET http://localhost:8000/api/v1/health`  
  Returns dependency probe results for PostgreSQL, Redis, and Object Storage.

---

## 3. Evidence Asset Endpoints (Phase 1)

- **Upload Asset:** `POST http://localhost:8000/api/v1/assets/upload`  
  Accepts multipart/form-data (`file`, optional `investigation_id`, `source_url`, `source_platform`, `captured_at`).  
  Performs bounded chunk streaming, concurrent SHA-256 calculation, magic-byte MIME validation, and atomic filesystem storage.  
  Returns: `201 Created` with canonical `EvidenceAsset` payload.

- **Get Asset Metadata:** `GET http://localhost:8000/api/v1/assets/{asset_id}`  
  Returns metadata for `asset_id` (e.g. `ast_<uuid4>`). Returns RFC 9457 Problem Details on 404 or 422.

- **List Assets:** `GET http://localhost:8000/api/v1/assets?investigation_id={inv_id}`  
  Lists assets optionally filtered by investigation ID.

---

## 4. Running Backend Tests

```bash
pytest backend/tests -v
```

