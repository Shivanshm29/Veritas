# Veritas — Dataset Manifests

> **Project:** Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network  
> **Directory:** `datasets/manifests/`  
> **Purpose:** Versioned Metadata Manifests for Evaluation Datasets  

---

## 1. Overview

In Phase 0, no multi-gigabyte media datasets are stored in Git. Instead, this directory holds JSON/YAML manifest schemas that document:
1. Dataset Name and Version.
2. Canonical Source URLs and Research Paper Citations.
3. Media Modalities (Image, Video, Audio, Speech).
4. Ground Truth Labels (Authentic vs. Synthetic, Manipulation Techniques).
5. Cryptographic Checksums (SHA-256) for verifying downloaded benchmark files.

---

## 2. Benchmark Manifest Standards (Phases 11–12)

Future benchmark evaluation files will adhere to:
```json
{
  "dataset_id": "faceforensics_c23_benchmark_v1",
  "modalities": ["VIDEO"],
  "total_items": 1000,
  "license": "Research Non-Commercial",
  "samples": [
    {
      "sample_id": "ff_sample_001.mp4",
      "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
      "ground_truth_verdict": "SYNTHETIC",
      "manipulation_technique": "DEEPFAKES_FACIAL_REENACTMENT"
    }
  ]
}
```

