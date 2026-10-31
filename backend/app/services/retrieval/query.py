"""
Query generation, refinement, and expansion service for Veritas Evidence Retrieval.
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional
from contracts.schemas.models import Claim


@dataclass
class EvidenceQuery:
    """Structured representation of a retrieval query derived from a claim or input text."""
    raw_query: str
    search_terms: List[str]
    claim_id: Optional[str] = None
    entities: List[str] = field(default_factory=list)
    language: Optional[str] = None
    category: Optional[str] = None
    temporal_anchor: Optional[str] = None
    domain_filter: Optional[List[str]] = None


class QueryGenerator:
    """
    Transforms claims and propositions into optimized lexical and semantic retrieval queries.
    Strips noise words while preserving named entities, numbers, dates, and negation.
    """

    STOPWORDS = {
        "a", "an", "the", "and", "or", "but", "if", "then", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "that", "this", "these", "those", "to", "from", "in", "on", "at", "by",
        "for", "with", "about", "into", "through", "during", "before", "after",
        "above", "below", "up", "down", "in", "out", "off", "over", "under",
    }

    @classmethod
    def from_claim(cls, claim: Claim) -> EvidenceQuery:
        """Constructs an EvidenceQuery directly from a verified Claim object."""
        category_val = None
        if claim.category is not None:
            category_val = claim.category.value if hasattr(claim.category, "value") else str(claim.category)

        return cls.generate(
            text=claim.claim_text,
            claim_id=claim.id,
            entities=claim.claim_entities or [],
            language=claim.language,
            category=category_val,
        )

    @classmethod
    def generate(
        cls,
        text: str,
        claim_id: Optional[str] = None,
        entities: Optional[List[str]] = None,
        language: Optional[str] = None,
        category: Optional[str] = None,
        domain_filter: Optional[List[str]] = None,
    ) -> EvidenceQuery:
        """Generates a refined EvidenceQuery from input text and contextual metadata."""
        cleaned_text = text.strip()
        entities = entities or []

        # Extract temporal anchors (years, months, dates)
        temporal_match = re.search(
            r"\b(19\d\d|20\d\d|january|february|march|april|may|june|july|august|september|october|november|december)\b",
            cleaned_text,
            re.IGNORECASE,
        )
        temporal_anchor = temporal_match.group(0) if temporal_match else None

        # Tokenize and extract significant search keywords
        raw_words = [w.strip(".,;:!?\"'()[]{}") for w in cleaned_text.split()]
        search_terms = []
        for word in raw_words:
            if not word:
                continue
            w_lower = word.lower()
            if w_lower not in cls.STOPWORDS and len(w_lower) > 2:
                search_terms.append(word)

        # Ensure entities are prominently represented in search terms
        for ent in entities:
            if ent not in search_terms:
                search_terms.insert(0, ent)

        return EvidenceQuery(
            raw_query=cleaned_text,
            search_terms=search_terms,
            claim_id=claim_id,
            entities=entities,
            language=language,
            category=category,
            temporal_anchor=temporal_anchor,
            domain_filter=domain_filter,
        )
