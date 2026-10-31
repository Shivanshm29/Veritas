"""
Evidence Stance Classification Service for Veritas (Phase 4).

Classifies the epistemic stance of an evidentiary passage relative to a claim:
- SUPPORTS: Corroborates, entails, or affirms the claim assertion.
- CONTRADICTS / REFUTES: Directly negates, disproves, or debunks the claim assertion.
- INSUFFICIENT / NEUTRAL: Unrelated, inconclusive, ambiguous, or lacks sufficient grounding.

Provides transparent explanations and key phrase attribution for every classification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Set
from contracts.schemas.models import EvidenceStance


@dataclass
class StanceClassificationResult:
    """Output of stance classification between an evidence passage and a claim."""
    stance: EvidenceStance
    confidence: float  # [0.0, 1.0] stance confidence
    rationale: str
    key_phrases: List[str] = field(default_factory=list)
    is_calibrated: bool = False

    @property
    def is_support(self) -> bool:
        return self.stance == EvidenceStance.SUPPORTS

    @property
    def is_contradiction(self) -> bool:
        return self.stance in (EvidenceStance.CONTRADICTS, EvidenceStance.REFUTES)

    @property
    def is_insufficient(self) -> bool:
        return self.stance in (EvidenceStance.INSUFFICIENT, EvidenceStance.NEUTRAL)


class StanceClassifierProtocol(ABC):
    """Abstract interface for stance classification engines."""

    @abstractmethod
    def classify_stance(
        self,
        claim_text: str,
        evidence_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> StanceClassificationResult:
        """Classifies the stance of evidence_text against claim_text."""
        pass


class RuleBasedStanceClassifier(StanceClassifierProtocol):
    """
    Deterministic, transparent rule-based stance classifier.
    Combines lexical overlap, negation detection, and epistemic fact-checking markers.
    """

    REFUTATION_PATTERNS = [
        r"\bfalse\b", r"\bfake\b", r"\bhoax\b", r"\bdebunked?\b", r"\bdebunking\b",
        r"\buntrue\b", r"\bincorrect\b", r"\binaccurate\b", r"\bfabricated?\b",
        r"\bfabrication\b", r"\bdisproven\b", r"\bdisproved?\b", r"\bno evidence\b",
        r"\bbaseless\b", r"\bdenie[sd]\b", r"\bdenial\b", r"\bcontradicts?\b",
        r"\bcontradicted\b", r"\bcontradicting\b", r"\bcontradiction\b",
        r"\brefuted?\b", r"\brefutes\b", r"\brefuting\b", r"\bmisinformation\b",
        r"\bdisinformation\b", r"\bdistorted\b", r"\bdistortion\b",
        r"\bnever happened\b", r"\bnot true\b", r"\bfictitious\b", r"\bcounterfeit\b",
        r"\bunfounded\b", r"\bmyth\b", r"\bbogus\b", r"\bnever said\b",
        r"\bdid not say\b", r"\bfalsely claimed\b", r"\bmisleading\b",
        r"\bdisputed?\b", r"\bdisputes\b", r"\bcontrary to\b", r"\brather than\b",
    ]

    NEGATION_PATTERNS = [
        r"\bdid not\b", r"\bdoes not\b", r"\bdo not\b", r"\bnever\b",
        r"\bwas not\b", r"\bwere not\b", r"\bhas not\b", r"\bhave not\b",
        r"\bhad not\b", r"\bcannot\b", r"\bcan not\b", r"\bcould not\b",
        r"\bfailed to\b", r"\bno such\b", r"\brefused to\b", r"\brejected\b",
        r"\bdenied having\b", r"\bneither\b", r"\bwithout any\b",
    ]

    SUPPORT_PATTERNS = [
        r"\bconfirmed?\b", r"\bverified?\b", r"\bsubstantiated?\b",
        r"\bcorroborated?\b", r"\bannounced?\b", r"\bofficially stated\b",
        r"\bfound that\b", r"\bdocumented\b", r"\bindeed\b", r"\baccurate\b",
        r"\bauthentic\b", r"\bproves?\b", r"\bproven\b", r"\bdemonstrated?\b",
        r"\breleased data showing\b", r"\bconcluded that\b", r"\bestablished that\b",
        r"\breaffirmed\b", r"\bvalidated\b", r"\brecords show\b", r"\bevidence shows\b",
        r"\bhealing\b",
    ]

    INSUFFICIENT_PATTERNS = [
        r"\bunclear\b", r"\bunconfirmed\b", r"\balleged\b", r"\ballegedly\b",
        r"\bclaimed without proof\b", r"\bunder investigation\b",
        r"\byet to be verified\b", r"\bremains uncertain\b", r"\bspeculation\b",
        r"\brumored\b", r"\bhypothetical\b", r"\binconclusive\b",
        r"\bcannot be determined\b", r"\bpending investigation\b",
    ]

    STOPWORDS = {
        "a", "an", "the", "in", "on", "at", "to", "for", "of", "with", "by",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "and", "or", "but", "so", "that", "this", "these", "those", "it", "its",
        "as", "from", "into", "about", "against", "after", "before", "over",
    }

    def _tokenize_content_words(self, text: str) -> Set[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\u0900-\u097F]{3,}\b", text.lower())
        return {w for w in words if w not in self.STOPWORDS}

    def _find_matches(self, patterns: List[str], text: str) -> List[str]:
        matches = []
        for p in patterns:
            found = re.findall(p, text)
            if found:
                for match_item in found:
                    val = match_item.strip() if isinstance(match_item, str) else str(match_item).strip()
                    if val and val not in matches:
                        matches.append(val)
        return matches

    def classify_stance(
        self,
        claim_text: str,
        evidence_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> StanceClassificationResult:
        if not evidence_text or not evidence_text.strip():
            return StanceClassificationResult(
                stance=EvidenceStance.INSUFFICIENT,
                confidence=0.0,
                rationale="Empty evidence passage provided.",
                key_phrases=[],
            )

        claim_tokens = self._tokenize_content_words(claim_text)
        evidence_tokens = self._tokenize_content_words(evidence_text)

        overlap = claim_tokens.intersection(evidence_tokens)
        overlap_ratio = len(overlap) / max(len(claim_tokens), 1)

        evidence_lower = evidence_text.lower()

        # Find actual matched text for phrases
        found_refutations = self._find_matches(self.REFUTATION_PATTERNS, evidence_lower)
        found_negations = self._find_matches(self.NEGATION_PATTERNS, evidence_lower)
        found_supports = self._find_matches(self.SUPPORT_PATTERNS, evidence_lower)
        found_insufficient = self._find_matches(self.INSUFFICIENT_PATTERNS, evidence_lower)

        # Scenario A: Low overlap -> Evidence is not about the claim
        if overlap_ratio < 0.15 and len(overlap) < 2:
            return StanceClassificationResult(
                stance=EvidenceStance.INSUFFICIENT,
                confidence=0.35,
                rationale="Evidence text shares negligible semantic overlap with the target claim.",
                key_phrases=list(overlap),
            )

        # Scenario B: Explicit refutation/debunking markers override confirmation verbs
        if found_refutations and (overlap_ratio >= 0.15 or len(overlap) >= 2):
            key_items = found_refutations[:3]
            confidence = min(0.95, 0.70 + 0.10 * len(key_items) + 0.15 * overlap_ratio)
            return StanceClassificationResult(
                stance=EvidenceStance.CONTRADICTS,
                confidence=round(confidence, 3),
                rationale=(
                    f"Evidence contains explicit refutation/debunking markers ({', '.join(key_items)}) "
                    f"addressing the subject of the claim."
                ),
                key_phrases=key_items,
            )

        # Scenario C: Negation markers addressing key claim concepts
        if found_negations and (overlap_ratio >= 0.20 or len(overlap) >= 2):
            key_items = found_negations[:3]
            confidence = min(0.90, 0.65 + 0.15 * overlap_ratio)
            return StanceClassificationResult(
                stance=EvidenceStance.CONTRADICTS,
                confidence=round(confidence, 3),
                rationale=(
                    f"Evidence text negates core assertions of the claim using negation phrasing: "
                    f"({', '.join(key_items)})."
                ),
                key_phrases=key_items,
            )

        # Scenario D: Explicit support markers with topical overlap
        if found_supports and (overlap_ratio >= 0.15 or len(overlap) >= 2):
            key_items = found_supports[:3]
            confidence = min(0.95, 0.65 + 0.10 * len(key_items) + 0.15 * overlap_ratio)
            return StanceClassificationResult(
                stance=EvidenceStance.SUPPORTS,
                confidence=round(confidence, 3),
                rationale=(
                    f"Evidence directly substantiates the claim with corroborating markers: "
                    f"({', '.join(key_items)})."
                ),
                key_phrases=key_items,
            )

        # Scenario E: High semantic overlap without negation or refutation
        if overlap_ratio >= 0.50 and not found_negations and not found_refutations:
            confidence = min(0.85, 0.55 + 0.30 * overlap_ratio)
            return StanceClassificationResult(
                stance=EvidenceStance.SUPPORTS,
                confidence=round(confidence, 3),
                rationale=(
                    f"Evidence passage mirrors key factual assertions of the claim without contradicting qualifiers "
                    f"(overlap: {round(overlap_ratio * 100, 1)}%)."
                ),
                key_phrases=list(overlap)[:5],
            )

        # Scenario F: Ambiguity, uncertainty markers, or weak overlap
        if found_insufficient:
            return StanceClassificationResult(
                stance=EvidenceStance.INSUFFICIENT,
                confidence=0.60,
                rationale=(
                    f"Evidence discusses related concepts but expresses explicit uncertainty: "
                    f"({', '.join(found_insufficient[:2])})."
                ),
                key_phrases=found_insufficient[:3],
            )

        # Fallback: Moderate overlap without conclusive directional cues -> INSUFFICIENT
        return StanceClassificationResult(
            stance=EvidenceStance.INSUFFICIENT,
            confidence=0.50,
            rationale="Evidence is tangentially related but lacks definitive corroborating or contradictory statements.",
            key_phrases=list(overlap)[:3],
        )


_DEFAULT_CLASSIFIER: Optional[StanceClassifierProtocol] = None


def get_stance_classifier() -> StanceClassifierProtocol:
    """Returns the singleton stance classifier instance."""
    global _DEFAULT_CLASSIFIER
    if _DEFAULT_CLASSIFIER is None:
        _DEFAULT_CLASSIFIER = RuleBasedStanceClassifier()
    return _DEFAULT_CLASSIFIER
