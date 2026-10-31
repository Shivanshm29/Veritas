# PRAMAAN — Local Development Infrastructure

**Project:** PRAMAAN (Provenance, Reliability & Authenticity Monitoring and Analysis Network)  
**Directory:** `infra/`  
**Purpose:** Multi-Container Infrastructure for Local Development & Integration Testing  

---

## 1. Services Defined in `docker-compose.yml`

| Service | Image | Internal Port | Host Port | Purpose | Health Check |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **postgres** | `postgres:16-alpine` | 5432 | 5432 | Relational metadata, claims, sources, and audit logs. | `pg_isready` |
| **redis** | `redis:7-alpine` | 6379 | 6379 | Async task broker and state cache for ingestion workers. | `redis-cli ping` |
| **minio** | `minio/minio` | 9000, 9001 | 9000, 9001 | S3-compatible evidence asset and derivation storage. | `mc ready local` |

---

## 2. Infrastructure Commands

### Start All Services
```bash
docker compose -f infra/docker-compose.yml up -d
```

### Inspect Container Health
```bash
docker compose -f infra/docker-compose.yml ps
```

### View Service Logs
```bash
docker compose -f infra/docker-compose.yml logs -f
```

### Stop & Teardown (Preserving Volumes)
```bash
docker compose -f infra/docker-compose.yml down
```

### Reset & Erase Local Volumes
```bash
docker compose -f infra/docker-compose.yml down -v
```

---

## 3. Decoupled / No-Docker Fallback

If Docker Desktop is offline or unavailable on a developer workstation:
- **Database:** SQLAlchemy falls back automatically to SQLite (`sqlite:///:memory:` or local `pramaan_dev.db`).
- **Cache / Queue:** Worker tests execute via the in-process `InMemoryTaskRunner`.
- **Object Storage:** File storage uses standard local filesystem paths (`./storage`).

Tests do not require Docker to pass Phase 0 exit gates.

