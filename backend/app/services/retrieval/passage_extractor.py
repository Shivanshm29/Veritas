"""
Passage extraction and relevance scoring service for Veritas Evidence Retrieval.

Segments source document content into bounded passages (10 to 4000 characters),
scores relevance against candidate claims, and extracts paragraph/position offsets.
"""

from dataclasses import dataclass
import re
from typing import List, Optional, Set
from contracts.schemas.models import EvidenceStance


@dataclass
class CandidatePassage:
    """A scored excerpt extracted from a source document."""
    text: str
    relevance_score: float
    paragraph_index: int
    page_number: Optional[int] = None
    stance_hint: EvidenceStance = EvidenceStance.NEUTRAL


class PassageExtractor:
    """
    Extracts high-relevance evidence passages from source document full text or snippets.
    Strictly conforms to EvidenceItem length bounds (10 to 4000 characters).
    """

    MIN_PASSAGE_CHARS = 10
    MAX_PASSAGE_CHARS = 4000

    @classmethod
    def _tokenize(cls, text: str) -> Set[str]:
        return set(re.findall(r"\b[\w\-\$%\.]+\b", text.lower()))

    @classmethod
    def extract_passages(
        cls,
        document_text: str,
        query_terms: List[str],
        claim_text: Optional[str] = None,
        max_passages: int = 3,
    ) -> List[CandidatePassage]:
        """
        Segments text into paragraphs and ranks them by relevance to the query.
        """
        if not document_text or not document_text.strip() or len(document_text.strip()) < cls.MIN_PASSAGE_CHARS:
            return []

        # Segment by paragraphs or double-newlines
        raw_paragraphs = re.split(r"\n\s*\n|\r\n\s*\r\n", document_text.strip())
        paragraphs = [p.strip() for p in raw_paragraphs if len(p.strip()) >= cls.MIN_PASSAGE_CHARS]

        if not paragraphs:
            # Fall back to single lines or sentences if no paragraphs
            lines = [l.strip() for l in document_text.splitlines() if len(l.strip()) >= cls.MIN_PASSAGE_CHARS]
            paragraphs = lines

        if not paragraphs:
            return []

        query_tokens = set(t.lower() for t in query_terms if len(t) > 2)
        claim_tokens = cls._tokenize(claim_text) if claim_text else set()
        all_target_tokens = query_tokens | claim_tokens

        candidates: List[CandidatePassage] = []

        for idx, para in enumerate(paragraphs):
            # Enforce max length bound
            clean_para = para
            if len(clean_para) > cls.MAX_PASSAGE_CHARS:
                clean_para = clean_para[: cls.MAX_PASSAGE_CHARS - 3] + "..."

            para_tokens = cls._tokenize(clean_para)
            if not para_tokens:
                continue

            # Calculate token overlap score
            overlap = len(para_tokens & all_target_tokens)
            relevance = 0.0
            if all_target_tokens:
                relevance = min(1.0, round(overlap / max(1, len(all_target_tokens) * 0.5), 2))
            else:
                relevance = 0.50

            # Boost if query phrases or numbers match exactly
            for term in query_terms:
                if len(term) >= 3 and term.lower() in clean_para.lower():
                    relevance = min(1.0, round(relevance + 0.15, 2))

            # Minimal heuristic stance hint (verification belongs to Phase 4)
            stance = EvidenceStance.NEUTRAL
            lower_para = clean_para.lower()
            if any(kw in lower_para for kw in ["denied", "false", "refuted", "debunked", "incorrect", "hoax", "fabricated"]):
                stance = EvidenceStance.REFUTES
            elif any(kw in lower_para for kw in ["confirm", "verified", "announced", "officially stated", "records show"]):
                stance = EvidenceStance.SUPPORTS
            elif relevance < 0.40:
                stance = EvidenceStance.INSUFFICIENT

            candidates.append(
                CandidatePassage(
                    text=clean_para,
                    relevance_score=max(0.05, min(1.0, relevance)),
                    paragraph_index=idx,
                    page_number=None,
                    stance_hint=stance,
                )
            )

        # Sort by relevance score descending
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        return candidates[:max_passages]
