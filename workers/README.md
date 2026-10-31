# Veritas — Asynchronous Worker Subsystem

**Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
**Directory:** `workers/`  
**Purpose:** Asynchronous Background Processing Scaffold for Person 1 Pipeline Operations  

---

## 1. Subsystem Architecture

Person 1 is responsible for media ingestion, normalization, claim extraction, and source retrieval. These operations are computationally or network-intensive and must run asynchronously behind an event queue rather than blocking HTTP request threads.

### Task Status State Machine
$$\text{PENDING} \longrightarrow \text{RUNNING} \longrightarrow \begin{cases} \text{SUCCESS} \\ \text{FAILURE} \longrightarrow \text{RETRY} \end{cases}$$

---

## 2. Decoupled Execution for Local & CI Testing

To ensure Person 1 and Person 2 can develop and test independently without requiring a live Redis daemon:
- **Production Mode:** Tasks are scheduled via Celery/RQ through Redis.
- **Test Mode (`InMemoryTaskRunner`):** Tasks execute asynchronously in-process via `asyncio.to_thread()`, storing results in a thread-safe dictionary for polling and validation.

---

## 3. Demonstration Tasks

In Phase 0, no media inference or real NLP is executed:
- `echo_probe_task`: Harmless verification probe computing SHA-256 payload checksum and measuring execution duration.
- `failing_probe_task`: Verifies error trapping, structured error serialization, and non-blocking failure status.

---

## 4. Test Commands

```bash
# Run worker unit tests
pytest workers/tests -v
```

