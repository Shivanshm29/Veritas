"""
Evaluation script for Phase 2 Claim Intelligence & Multilingual NLP.

Evaluates precision, recall, F1, span alignment accuracy, schema validity,
non-factual abstention rate, and processing latency over datasets/eval/phase2_claims_eval.json.
"""

import json
from pathlib import Path
import sys
import time
from typing import Dict, Any

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from contracts.schemas.models import Claim
from backend.app.services.nlp.extractor import ClaimExtractionService


def run_evaluation(dataset_path: str = "datasets/eval/phase2_claims_eval.json") -> Dict[str, Any]:
    full_path = REPO_ROOT / dataset_path
    with open(full_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    service = ClaimExtractionService()

    total_cases = len(cases)
    total_expected_claims = 0
    total_extracted_claims = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    span_alignment_checks = 0
    span_alignment_successes = 0

    schema_valid_claims = 0
    total_claims_created = 0

    non_factual_cases = 0
    correct_abstentions = 0

    latencies_ms = []

    print(f"Running Phase 2 NLP evaluation on {total_cases} test cases...")
    print("-" * 70)

    for case in cases:
        text = case["text"]
        expected_assessable = case["expected_assessable"]
        expected_count = case.get("expected_claim_count", 0)

        t0 = time.perf_counter()
        batch = service.extract_claims(text)
        latency = (time.perf_counter() - t0) * 1000
        latencies_ms.append(latency)

        extracted_count = batch.total_claims
        total_claims_created += extracted_count
        total_extracted_claims += extracted_count
        total_expected_claims += expected_count

        if not expected_assessable:
            non_factual_cases += 1
            if extracted_count == 0 and len(batch.unprocessed_segments) >= 1:
                correct_abstentions += 1
            elif extracted_count > 0:
                false_positives += extracted_count
        else:
            if extracted_count > 0:
                # Match extracted with expected count
                tp = min(expected_count, extracted_count)
                true_positives += tp
                if extracted_count > expected_count:
                    false_positives += (extracted_count - expected_count)
                elif extracted_count < expected_count:
                    false_negatives += (expected_count - extracted_count)
            else:
                false_negatives += expected_count

        # Span alignment & Schema validity
        for claim in batch.claims:
            # Validate schema
            try:
                Claim.model_validate(claim.model_dump())
                schema_valid_claims += 1
            except Exception as e:
                print(f"Schema validation error on claim {claim.id}: {e}")

            # Check span alignment
            span_alignment_checks += 1
            if claim.source_char_start is not None and claim.source_char_end is not None:
                orig_slice = text[claim.source_char_start:claim.source_char_end]
                if orig_slice == claim.claim_text:
                    span_alignment_successes += 1

    precision = true_positives / max(1, (true_positives + false_positives))
    recall = true_positives / max(1, (true_positives + false_negatives))
    f1 = (2 * precision * recall) / max(1e-9, (precision + recall))

    span_accuracy = span_alignment_successes / max(1, span_alignment_checks)
    schema_valid_rate = schema_valid_claims / max(1, total_claims_created)
    abstention_rate = correct_abstentions / max(1, non_factual_cases)
    avg_latency = sum(latencies_ms) / max(1, len(latencies_ms))

    results = {
        "total_test_cases": total_cases,
        "total_expected_claims": total_expected_claims,
        "total_extracted_claims": total_extracted_claims,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "span_alignment_accuracy": round(span_accuracy, 4),
        "schema_validity_rate": round(schema_valid_rate, 4),
        "non_factual_abstention_rate": round(abstention_rate, 4),
        "average_latency_ms": round(avg_latency, 2),
    }

    print("EVALUATION RESULTS:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("-" * 70)

    return results


if __name__ == "__main__":
    run_evaluation()
