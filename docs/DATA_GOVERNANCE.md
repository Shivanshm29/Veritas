# Veritas — Data Governance & Privacy Policy

> **Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
> **Document:** Data Governance, Evidence Retention, Privacy & Compliance Policy  
> **Classification:** Digital Forensics Chain of Custody & Privacy Protection  

---

## 1. Principles of Forensic Data Governance

Veritas processes potentially sensitive multimodal media, including broadcast recordings, leaked surveillance, viral social uploads, and biometric facial/voice data. The architecture enforces four core tenets:

1. **Chain of Custody Integrity:** Evidence must be forensically preserved and timestamped without loss of provenance.
2. **Data Minimization:** Only media features necessary for forensic analysis (audio tracks, keyframe crops, spectrograms, text transcripts) are retained.
3. **Privacy by Design:** Personally Identifiable Information (PII) not directly pertinent to an active investigation is automatically masked or redacted.
4. **Transparent Epistemic Lineage:** Evidence must not be fabricated, synthesized without explicit labeling, or commingled with ground-truth assets.

---

## 2. Evidence Asset Retention & Lifecycle

| Lifecycle State | Description | Retention Window | Storage Medium |
| :--- | :--- | :--- | :--- |
| **Active Investigation** | Ingested primary evidence assets (`ast_`), derivations (`drv_`), and claims (`clm_`). | Duration of inquiry + 90 days. | High-durability encrypted S3/MinIO bucket. |
| **Archived Case** | Completed case reports (`rpt_`), verified claims, and immutable audit logs (`adt_`). | 3 years (configurable by jurisdiction). | WORM (Write Once, Read Many) cold storage. |
| **Quarantined Asset** | Ingested file containing confirmed malware, decompression bombs, or illicit content. | Immediate isolation; purged within 24h of review. | Air-gapped quarantine storage with disabled execute permissions. |
| **Purged Asset** | Explicitly expunged asset following right-to-be-forgotten or legal expungement order. | Zero retention; cryptographic proof of deletion logged. | Deleted via multi-pass cryptographic erasure. |

---

## 3. Sensitive Metadata & Biometric Safeguards

1. **EXIF & Geolocation Stripping:** Unless an investigator explicitly tags geolocation metadata as essential to proving provenance, location coordinates (GPS tags) are stripped from public preview endpoints to safeguard source whistleblowers.
2. **Face & Voice Embeddings:** Facial vector representations and voice acoustic prints generated during deepfake analysis are classified as sensitive biometric derivatives. They are stored as anonymized hash keys and never shared across external third-party search APIs.
3. **Witness & Minor Protection:** Investigator tools support automatic facial blurring and pitch-shifting for vulnerable witnesses cited in media evidence.

---

## 4. Structured Logging Restrictions

Under strict compliance with privacy standards, application logs (`backend/app/core/logging.py`) must adhere to strict redaction policies:

- **FORBIDDEN IN LOGS:**
  - Raw authentication tokens, JWT strings, or API secrets.
  - Full biometric vector embeddings.
  - Cleartext passwords or credentials.
  - Raw binary image/video streams.
- **PERMITTED IN LOGS:**
  - Correlation IDs (`trace_id`, `request_id`).
  - Standard entity identifiers (`inv_...`, `ast_...`, `clm_...`).
  - SHA-256 hashes of ingested media.
  - HTTP method, path, response status, and duration in milliseconds.

---

## 5. Dataset Licensing & Intellectual Property

Training, benchmarking, and evaluation datasets (configured under `datasets/manifests/`) must comply with open research licenses:

- **Synthetic Benchmarks:** Derived exclusively from publicly licensed datasets (e.g., FaceForensics++, DFDC Public Preview, FakeAVCeleb, In-The-Wild Voice Cloning Benchmark) under academic or permissive commercial licenses.
- **No Scraping of Restricted PII:** Scrapers or ingestion adapters must respect `robots.txt`, platform terms of service, and fair-use provisions for fact-checking and public-interest forensic journalism.

