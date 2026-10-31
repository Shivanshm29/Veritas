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

## 3. Running Backend Tests

```bash
pytest backend/tests -v
```

