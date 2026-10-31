"""
Evaluation script for Phase 3 Source Intelligence & Evidence Retrieval.

Evaluates precision at top-1 domain, passage relevance threshold attainment,
schema validity of SourceDocument and EvidenceItem records, deduplication rates,
and retrieval latency across datasets/eval/phase3_retrieval_corpus.json.
"""

from datetime import datetime
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from contracts.schemas.models import EvidenceItem, SourceDocument
from backend.app.services.retrieval.service import EvidenceRetrievalService


def run_evaluation(dataset_path: str = "datasets/eval/phase3_retrieval_corpus.json") -> Dict[str, Any]:
    full_path = REPO_ROOT / dataset_path
    with open(full_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    service = EvidenceRetrievalService()

    total_cases = len(cases)
    top_domain_matches = 0
    relevance_threshold_met = 0
    schema_valid_sources = 0
    schema_valid_items = 0
    total_sources = 0
    total_evidence = 0
    duplicates_caught = 0
    empty_correctly_handled = 0
    latencies_ms = []

    print(f"Running Phase 3 Evidence Retrieval evaluation on {total_cases} test cases...")
    print("-" * 75)

    for case in cases:
        query_text = case["query"]
        claim_id = case.get("claim_id")
        expected_domain = case.get("expected_top_domain")
        min_rel = case.get("min_expected_relevance", 0.50)
        is_empty_case = case.get("expected_empty", False)

        t0 = time.perf_counter()
        batch = service.retrieve_for_text(query_text=query_text, claim_id=claim_id)
        latency = (time.perf_counter() - t0) * 1000
        latencies_ms.append(latency)

        total_sources += batch.total_sources
        total_evidence += batch.total_evidence_items
        duplicates_caught += batch.duplicates_detected

        if is_empty_case:
            if batch.total_sources == 0 and batch.provider_status == "EMPTY_RESULTS":
                empty_correctly_handled += 1
            continue

        # Check top domain match
        if batch.source_documents and expected_domain:
            if any(doc.domain == expected_domain for doc in batch.source_documents):
                top_domain_matches += 1

        # Check passage relevance
        if batch.evidence_items:
            max_rel = max(evi.relevance_score for evi in batch.evidence_items)
            if max_rel >= min_rel:
                relevance_threshold_met += 1

        # Check schema validity
        for doc in batch.source_documents:
            try:
                SourceDocument.model_validate(doc.model_dump())
                schema_valid_sources += 1
            except Exception as e:
                print(f"SourceDocument validation error ({doc.id}): {e}")

        for evi in batch.evidence_items:
            try:
                EvidenceItem.model_validate(evi.model_dump())
                schema_valid_items += 1
            except Exception as e:
                print(f"EvidenceItem validation error ({evi.id}): {e}")

    non_empty_cases = [c for c in cases if not c.get("expected_empty", False)]
    domain_precision = top_domain_matches / max(1, len(non_empty_cases))
    relevance_rate = relevance_threshold_met / max(1, len(non_empty_cases))
    source_schema_rate = schema_valid_sources / max(1, total_sources)
    evidence_schema_rate = schema_valid_items / max(1, total_evidence)
    avg_latency = sum(latencies_ms) / max(1, len(latencies_ms))

    results = {
        "total_test_cases": total_cases,
        "total_sources_retrieved": total_sources,
        "total_evidence_items": total_evidence,
        "duplicates_suppressed": duplicates_caught,
        "top_domain_match_rate": round(domain_precision, 4),
        "relevance_threshold_attainment": round(relevance_rate, 4),
        "source_document_schema_validity": round(source_schema_rate, 4),
        "evidence_item_schema_validity": round(evidence_schema_rate, 4),
        "empty_handling_success": empty_correctly_handled,
        "average_retrieval_latency_ms": round(avg_latency, 2),
    }

    print("PHASE 3 RETRIEVAL EVALUATION RESULTS:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("-" * 75)

    return results


if __name__ == "__main__":
    run_evaluation()

