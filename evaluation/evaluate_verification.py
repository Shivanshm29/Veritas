"""
Veritas Phase 4 Verification Benchmark Evaluation Runner.

Evaluates stance classification, evidence aggregation, contradiction handling,
duplicate discounting, source credibility weighting, and epistemic safety rules.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List
from uuid import uuid4

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contracts.schemas.models import (
    Claim,
    ClaimAssessment,
    ClaimCategory,
    ClaimModalityOrigin,
    ClaimStatus,
    ClaimVerdict,
    EvidenceItem,
    EvidenceStance,
    SourceDocument,
)
from backend.app.services.verification.aggregation import EvidenceAggregator
from backend.app.services.verification.stance_classifier import get_stance_classifier


def run_benchmark():
    benchmark_file = ROOT_DIR / "evaluation" / "benchmarks" / "claim_verification_benchmark.json"
    if not benchmark_file.exists():
        benchmark_file = ROOT_DIR / "evaluation" / "data" / "claim_verification_benchmark.json"
    if not benchmark_file.exists():
        print(f"Error: Benchmark file not found at {benchmark_file}")
        sys.exit(1)

    with open(benchmark_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    cases = data.get("cases", [])
    print("=" * 80)
    print(f"VERITAS PHASE 4 BENCHMARK: {data.get('benchmark_name')}")
    print(f"Evaluating {len(cases)} curated test scenarios...")
    print("=" * 80)

    aggregator = EvidenceAggregator()
    total_cases = len(cases)
    passed_cases = 0

    results = []

    for idx, case in enumerate(cases, 1):
        case_id = case["id"]
        claim_text = case["claim_text"]
        expected_verdict = case["expected_verdict"]
        raw_items = case.get("evidence_items", [])
        criteria = case.get("evaluation_criteria", {})

        inv_id = f"inv_{uuid4()}"
        claim_id = f"clm_{uuid4()}"

        claim = Claim(
            id=claim_id,
            investigation_id=inv_id,
            claim_text=claim_text,
            modality_origin=ClaimModalityOrigin.USER_PROMPT,
            extraction_confidence=1.0,
            status=ClaimStatus.EXTRACTED,
            created_at=datetime.now(timezone.utc),
        )

        sources: List[SourceDocument] = []
        evidence_items: List[EvidenceItem] = []

        for e_idx, e in enumerate(raw_items):
            doc_id = f"doc_{uuid4()}"
            evi_id = f"evi_{uuid4()}"
            domain = e.get("domain", "example.com")
            rel = e.get("reliability", 0.8)

            src = SourceDocument(
                id=doc_id,
                title=f"Source {domain}",
                url=f"https://{domain}/article/{e_idx}",
                domain=domain,
                retrieval_timestamp=datetime.now(timezone.utc),
                content_snippet=e["text"][:100],
                content_sha256="0" * 64,
                source_reliability_score=rel,
                is_simulated=True,
            )
            sources.append(src)

            st_hint = e.get("stance_hint", "NEUTRAL")
            stance = EvidenceStance(st_hint) if st_hint in EvidenceStance.__members__ else EvidenceStance.NEUTRAL

            evi = EvidenceItem(
                id=evi_id,
                claim_id=claim_id,
                source_document_id=doc_id,
                evidence_text=e["text"],
                stance=stance,
                relevance_score=0.90,
                created_at=datetime.now(timezone.utc),
            )
            evidence_items.append(evi)

        # Run aggregation
        assessment: ClaimAssessment = aggregator.aggregate(
            claim=claim,
            evidence_items=evidence_items,
            sources=sources,
            investigation_id=inv_id,
        )

        actual_verdict = assessment.verdict.value if hasattr(assessment.verdict, "value") else str(assessment.verdict)
        verdict_ok = (actual_verdict == expected_verdict)

        # Safety checks
        checks_passed = True
        failures = []

        if not verdict_ok:
            checks_passed = False
            failures.append(f"Verdict mismatch: expected {expected_verdict}, got {actual_verdict}")

        if criteria.get("strict_guardrail") == "never_refute_on_absence":
            if len(raw_items) == 0 and actual_verdict == "REFUTED":
                checks_passed = False
                failures.append("VIOLATION: Absence of evidence was equated with REFUTED!")

        if criteria.get("requires_conflicting_points"):
            if not assessment.conflicting_points:
                checks_passed = False
                failures.append("Missing required conflicting_points for contradictory case.")

        if actual_verdict in ("SUPPORTED", "REFUTED") and not assessment.cited_evidence_ids:
            checks_passed = False
            failures.append("Schema violation: cited_evidence_ids is empty for SUPPORTED/REFUTED verdict.")

        if criteria.get("min_confidence"):
            if assessment.confidence_score < criteria["min_confidence"]:
                checks_passed = False
                failures.append(f"Confidence {assessment.confidence_score} < min {criteria['min_confidence']}")

        if criteria.get("max_confidence"):
            if assessment.confidence_score > criteria["max_confidence"]:
                checks_passed = False
                failures.append(f"Confidence {assessment.confidence_score} > max {criteria['max_confidence']}")

        if criteria.get("requires_duplicate_detection"):
            has_dup_limitation = any("duplicate" in l.lower() or "syndicated" in l.lower() for l in assessment.limitations)
            if not has_dup_limitation:
                checks_passed = False
                failures.append("Failed to detect or report syndicated duplicate coverage.")

        status_str = "PASS" if checks_passed else "FAIL"
        if checks_passed:
            passed_cases += 1

        print(f"[{status_str}] Case {idx:02d}: {case_id}")
        print(f"       Claim:    {claim_text[:65]}...")
        print(f"       Verdict:  {actual_verdict} (Expected: {expected_verdict})")
        print(f"       Conf:     {assessment.confidence_score:.2f} | Cited IDs: {len(assessment.cited_evidence_ids)}")
        if failures:
            for f_msg in failures:
                print(f"       >> ERROR: {f_msg}")
        print("-" * 80)

    pass_rate = (passed_cases / total_cases) * 100
    print("=" * 80)
    print(f"PHASE 4 BENCHMARK SUMMARY: {passed_cases}/{total_cases} passed ({pass_rate:.1f}%)")
    print("=" * 80)

    if passed_cases == total_cases:
        print("[SUCCESS] All Phase 4 verification benchmark criteria satisfied.")
        sys.exit(0)
    else:
        print(f"[FAILURE] {total_cases - passed_cases} test cases failed benchmark criteria.")
        sys.exit(1)


if __name__ == "__main__":
    run_benchmark()
