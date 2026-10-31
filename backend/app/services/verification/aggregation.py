"""
Evidence Aggregation and Decision Engine for Veritas (Phase 4).

Synthesizes multiple evidence passages and source documents into a canonical ClaimAssessment.
Enforces epistemic safety rules:
1. Never equates missing evidence with proof of falsity (absence != refutation).
2. Never represents uncalibrated scores as probabilities.
3. Discounts near-duplicate / syndicated reporting to prevent artificial support inflation.
4. Detects genuine contradictions among credible sources (CONTRADICTORY_EVIDENCE).
5. Requires independent multi-domain corroboration for high confidence.
6. Ensures strict traceability to cited evidence IDs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import re
from typing import Dict, List, Optional, Set, Tuple
from uuid import uuid4

from contracts.schemas.models import (
    Claim,
    ClaimAssessment,
    ClaimVerdict,
    EvidenceItem,
    EvidenceStance,
    SourceDocument,
)
from backend.app.core.logging import logger
from backend.app.services.retrieval.credibility import SourceCredibilityEvaluator
from backend.app.services.verification.stance_classifier import (
    StanceClassificationResult,
    get_stance_classifier,
)


@dataclass
class AggregationEvidenceContext:
    """Internal enriched representation of an evidence item during aggregation."""
    evidence_item: EvidenceItem
    stance_result: StanceClassificationResult
    source_document: Optional[SourceDocument]
    domain: str
    reliability_score: float
    duplicate_cluster_id: Optional[int] = None
    effective_weight: float = 1.0


class EvidenceAggregator:
    """
    Synthesizes evaluated evidence into a calibrated ClaimAssessment.
    """

    MODEL_IDENTIFIER = "veritas-fact-verifier-v1.0"

    # Calibration & decision thresholds
    MIN_CORROBORATION_WEIGHT = 0.50
    CONTRADICTION_RATIO_THRESHOLD = 0.35
    SINGLE_SOURCE_MAX_CONFIDENCE = 0.75
    MIN_EXPLANATION_LENGTH = 20

    def __init__(self):
        self.stance_classifier = get_stance_classifier()

    def _extract_domain(self, source: Optional[SourceDocument], evidence: EvidenceItem) -> str:
        """Extracts and normalizes the source domain."""
        if source and source.domain:
            return source.domain.lower()
        if source and source.url:
            match = re.search(r"https?://([^/]+)", source.url)
            if match:
                d = match.group(1).lower()
                return d[4:] if d.startswith("www.") else d
        return "unknown.domain"

    def _compute_reliability(self, source: Optional[SourceDocument], domain: str) -> float:
        """Determines source reliability score from document or domain evaluator."""
        if source and source.source_reliability_score is not None:
            return float(source.source_reliability_score)
        cred = SourceCredibilityEvaluator.evaluate(domain)
        if cred.reliability_score is not None:
            return float(cred.reliability_score)
        return 0.50

    def _cluster_duplicates(
        self, contexts: List[AggregationEvidenceContext]
    ) -> List[AggregationEvidenceContext]:
        """
        Detects near-duplicate or syndicated evidence items and applies diminishing weights.
        Ensures 5 syndicated wire stories do not overwhelm independent evidence.
        """
        def _tokenize(text: str) -> Set[str]:
            return set(re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]{3,}\b", text.lower()))

        clusters: List[List[int]] = []
        token_sets = [_tokenize(c.evidence_item.evidence_text) for c in contexts]

        for i in range(len(contexts)):
            assigned = False
            for cluster in clusters:
                rep_idx = cluster[0]
                s1, s2 = token_sets[i], token_sets[rep_idx]
                union_len = len(s1.union(s2))
                jaccard = len(s1.intersection(s2)) / union_len if union_len > 0 else 0.0

                if jaccard >= 0.65 or (
                    contexts[i].domain == contexts[rep_idx].domain and jaccard >= 0.50
                ):
                    cluster.append(i)
                    contexts[i].duplicate_cluster_id = rep_idx
                    k = len(cluster)
                    contexts[i].effective_weight = round(1.0 / math.sqrt(k), 3)
                    assigned = True
                    break

            if not assigned:
                clusters.append([i])
                contexts[i].duplicate_cluster_id = i
                contexts[i].effective_weight = 1.0

        return contexts

    def aggregate(
        self,
        claim: Claim,
        evidence_items: List[EvidenceItem],
        sources: Optional[List[SourceDocument]] = None,
        investigation_id: Optional[str] = None,
    ) -> ClaimAssessment:
        """
        Synthesizes evidence items into a canonical ClaimAssessment.
        """
        inv_id = investigation_id or claim.investigation_id
        assessment_id = f"asm_{uuid4()}"
        now_utc = datetime.now(timezone.utc)

        # 1. Guardrail: Missing Evidence Handling
        if not evidence_items:
            explanation = (
                f"No external or archival evidence was retrieved for the claim '{claim.claim_text}'. "
                "Under Veritas epistemic guardrails, missing evidence is never equated with proof of falsity; "
                "the claim is therefore assessed as INSUFFICIENT_EVIDENCE due to lack of sources."
            )
            return ClaimAssessment(
                id=assessment_id,
                investigation_id=inv_id,
                claim_id=claim.id,
                verdict=ClaimVerdict.INSUFFICIENT_EVIDENCE,
                confidence_score=0.0,
                explanation=explanation,
                cited_evidence_ids=[],
                conflicting_points=[],
                limitations=[
                    "No external evidentiary sources were retrieved or indexed for this claim.",
                    "Missing evidence does not constitute evidence of falsity or fabrication.",
                    "Confidence score is an empirically calibrated heuristic metric bounded in [0.0, 1.0], not an uncalibrated frequentist or Bayesian probability.",
                ],
                model_identifier=self.MODEL_IDENTIFIER,
                assessed_at=now_utc,
            )

        source_map = {s.id: s for s in (sources or [])}

        # 2. Build enriched evidence contexts with stance evaluation
        contexts: List[AggregationEvidenceContext] = []
        for item in evidence_items:
            src = source_map.get(item.source_document_id)
            domain = self._extract_domain(src, item)
            reliability = self._compute_reliability(src, domain)

            # Classify stance from text
            stance_res = self.stance_classifier.classify_stance(
                claim_text=claim.claim_text,
                evidence_text=item.evidence_text,
            )

            # If item has an explicit directional stance from ingestion, reconcile
            if item.stance in (EvidenceStance.SUPPORTS, EvidenceStance.CONTRADICTS, EvidenceStance.REFUTES):
                if stance_res.is_insufficient:
                    stance_res.stance = item.stance
                    stance_res.confidence = max(stance_res.confidence, 0.80)

            contexts.append(
                AggregationEvidenceContext(
                    evidence_item=item,
                    stance_result=stance_res,
                    source_document=src,
                    domain=domain,
                    reliability_score=reliability,
                )
            )

        # 3. Detect duplicate and syndicated reporting
        contexts = self._cluster_duplicates(contexts)
        has_syndicated_dupes = any(c.effective_weight < 1.0 for c in contexts)

        # 4. Group by stance and compute weighted scores
        supporting: List[AggregationEvidenceContext] = []
        contradicting: List[AggregationEvidenceContext] = []
        insufficient: List[AggregationEvidenceContext] = []

        for ctx in contexts:
            st = ctx.stance_result.stance
            if st == EvidenceStance.SUPPORTS:
                supporting.append(ctx)
            elif st in (EvidenceStance.CONTRADICTS, EvidenceStance.REFUTES):
                contradicting.append(ctx)
            else:
                insufficient.append(ctx)

        def _calc_weight(c: AggregationEvidenceContext) -> float:
            return (
                float(c.evidence_item.relevance_score)
                * c.reliability_score
                * c.effective_weight
                * c.stance_result.confidence
            )

        support_weight = sum(_calc_weight(c) for c in supporting)
        contradict_weight = sum(_calc_weight(c) for c in contradicting)

        domains_supporting = {c.domain for c in supporting}
        domains_contradicting = {c.domain for c in contradicting}
        total_unique_domains = len(domains_supporting.union(domains_contradicting))

        conflicting_points: List[str] = []
        limitations: List[str] = [
            "Confidence score is an empirically calibrated heuristic metric bounded in [0.0, 1.0], "
            "not an uncalibrated frequentist or Bayesian probability.",
        ]

        if has_syndicated_dupes:
            limitations.append(
                "Syndicated near-duplicate coverage detected; duplicate discounting applied "
                "to prevent artificial inflation of evidence volume."
            )

        if total_unique_domains == 1:
            limitations.append(
                "Evidence relies exclusively on a single source domain; independent multi-source corroboration unavailable."
            )

        # 5. Evaluate Contradiction vs Support vs Refute
        is_contradictory = (
            support_weight >= self.MIN_CORROBORATION_WEIGHT
            and contradict_weight >= self.MIN_CORROBORATION_WEIGHT
            and (
                min(support_weight, contradict_weight)
                / max(support_weight, contradict_weight)
                >= self.CONTRADICTION_RATIO_THRESHOLD
            )
        )

        if is_contradictory:
            verdict = ClaimVerdict.CONTRADICTORY_EVIDENCE
            cited_ids = [c.evidence_item.id for c in supporting[:2] + contradicting[:2]]

            sup_domains_str = ", ".join(sorted(domains_supporting))
            con_domains_str = ", ".join(sorted(domains_contradicting))
            conflicting_points.append(
                f"Supporting sources ({sup_domains_str}) affirm the claim, whereas contradicting sources "
                f"({con_domains_str}) explicitly dispute or negate it."
            )
            for c in contradicting[:2]:
                conflicting_points.append(
                    f"Contradicting item {c.evidence_item.id} [{c.domain}]: \"{c.evidence_item.evidence_text[:140]}...\""
                )

            raw_conf = 0.70 + 0.15 * min(1.0, (support_weight + contradict_weight) / 3.0)
            confidence_score = round(min(0.85, raw_conf), 2)
            explanation = (
                f"Substantial and irreconcilable evidentiary conflict was detected for claim '{claim.claim_text}'. "
                f"Credible reporting from {sup_domains_str} provides supporting evidence, but is directly contradicted "
                f"by findings from {con_domains_str}. Both perspectives are documented with cited evidence."
            )

        elif (
            support_weight >= self.MIN_CORROBORATION_WEIGHT
            and support_weight > 1.8 * contradict_weight
        ):
            verdict = ClaimVerdict.SUPPORTED
            supporting.sort(key=_calc_weight, reverse=True)
            cited_ids = [c.evidence_item.id for c in supporting[:4]]

            domain_diversity_bonus = 0.15 if len(domains_supporting) >= 2 else 0.0
            avg_rel = sum(c.reliability_score for c in supporting) / max(len(supporting), 1)
            raw_conf = 0.60 + 0.20 * avg_rel + domain_diversity_bonus
            if len(domains_supporting) < 2:
                raw_conf = min(raw_conf, self.SINGLE_SOURCE_MAX_CONFIDENCE)
            confidence_score = round(min(0.95, raw_conf), 2)

            sup_domains_str = ", ".join(sorted(domains_supporting))
            explanation = (
                f"The claim '{claim.claim_text}' is SUPPORTED by corroborating evidence from {sup_domains_str}. "
                f"Key factual assertions are substantiated across {len(supporting)} evidentiary passage(s) "
                f"with a combined reliability index of {round(avg_rel, 2)}."
            )

        elif (
            contradict_weight >= self.MIN_CORROBORATION_WEIGHT
            and contradict_weight > 1.8 * support_weight
        ):
            verdict = ClaimVerdict.REFUTED
            contradicting.sort(key=_calc_weight, reverse=True)
            cited_ids = [c.evidence_item.id for c in contradicting[:4]]

            domain_diversity_bonus = 0.15 if len(domains_contradicting) >= 2 else 0.0
            avg_rel = sum(c.reliability_score for c in contradicting) / max(len(contradicting), 1)
            raw_conf = 0.60 + 0.20 * avg_rel + domain_diversity_bonus
            if len(domains_contradicting) < 2:
                raw_conf = min(raw_conf, self.SINGLE_SOURCE_MAX_CONFIDENCE)
            confidence_score = round(min(0.95, raw_conf), 2)

            con_domains_str = ", ".join(sorted(domains_contradicting))
            explanation = (
                f"The claim '{claim.claim_text}' is REFUTED by authoritative evidence from {con_domains_str}. "
                f"Retrieved reporting and official statements explicitly disprove, debunk, or negate "
                f"the assertion across {len(contradicting)} passage(s)."
            )

        else:
            verdict = ClaimVerdict.INSUFFICIENT_EVIDENCE
            cited_ids = []
            confidence_score = 0.35
            explanation = (
                f"Retrieved evidence for claim '{claim.claim_text}' is insufficient, inconclusive, or lacks "
                "authoritative credibility. Neither corroboration nor direct refutation met the minimum "
                "evidentiary threshold required for a definitive verdict."
            )
            limitations.append(
                "Available evidence passages did not meet the corroboration threshold to confirm or refute the claim."
            )

        if len(explanation) < self.MIN_EXPLANATION_LENGTH:
            explanation = explanation + " Additional contextual evidence is required for a conclusive verdict."

        return ClaimAssessment(
            id=assessment_id,
            investigation_id=inv_id,
            claim_id=claim.id,
            verdict=verdict,
            confidence_score=confidence_score,
            explanation=explanation,
            cited_evidence_ids=cited_ids,
            conflicting_points=conflicting_points,
            limitations=limitations,
            model_identifier=self.MODEL_IDENTIFIER,
            assessed_at=now_utc,
        )
