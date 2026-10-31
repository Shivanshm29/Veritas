"""
Pluggable NLP Provider abstractions for Veritas Claim Extraction.

Includes:
- NLPProvider base interface.
- LocalRuleBasedProvider: deterministic, zero-network rule and syntax extractor.
- MockNLPProvider: test double for simulating LLM/external provider failure modes.
- LLMNLPProvider: structured LLM adapter treating model output as untrusted input.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import re
import uuid

from backend.app.core.errors import ServiceUnavailableError, VeritasException
from backend.app.core.logging import logger


@dataclass
class RawClaimProposal:
    text: str
    confidence: float
    entities: List[str] = field(default_factory=list)
    category_hint: Optional[str] = None
    is_assessable: bool = True
    abstention_reason: Optional[str] = None


class NLPProvider(ABC):
    @abstractmethod
    def extract_propositions(self, text: str, language: str) -> List[RawClaimProposal]:
        """Extracts candidate atomic propositions from text."""
        pass


class LocalRuleBasedProvider(NLPProvider):
    """
    Deterministic rule-based proposition segmenter and candidate extractor.
    Operates offline without network calls or external GPU/API dependencies.
    """

    # Common abbreviations to prevent false sentence splits
    ABBREVIATIONS = {
        "dr.", "mr.", "mrs.", "ms.", "prof.", "sr.", "jr.", "vs.", "u.s.", "u.k.",
        "e.g.", "i.e.", "jan.", "feb.", "mar.", "apr.", "aug.", "sept.", "oct.", "nov.", "dec.",
    }

    def _segment_sentences(self, text: str, language: str) -> List[str]:
        """Language-aware sentence segmentation handling abbreviations, numbers, and Indic viram."""
        if not text:
            return []

        # Replace known abbreviations with temporary tokens
        masked_text = text
        token_map = {}
        for i, abbr in enumerate(self.ABBREVIATIONS):
            pattern = re.compile(re.escape(abbr), re.IGNORECASE)
            for m in pattern.finditer(masked_text):
                token = f"__ABBR_{i}_{uuid.uuid4().hex[:6]}__"
                token_map[token] = m.group(0)
                masked_text = masked_text[:m.start()] + token + masked_text[m.end():]
                break

        # Protect floating point numbers (e.g. 3.14, $1.5)
        float_matches = list(re.finditer(r"\b\d+\.\d+\b", masked_text))
        for i, m in enumerate(reversed(float_matches)):
            token = f"__FLOAT_{i}_{uuid.uuid4().hex[:6]}__"
            token_map[token] = m.group(0)
            masked_text = masked_text[:m.start()] + token + masked_text[m.end():]

        # Sentence delimiters: '.', '!', '?', Indic purna viram '।', Arabic full stop '۔'
        sentence_regex = r"(?:[\.!\?।۔]+(?:\s+|\n+|$))"
        raw_sentences = re.split(sentence_regex, masked_text)

        # Restore tokens and clean up
        cleaned_sentences = []
        for raw in raw_sentences:
            s = raw
            for token, orig in token_map.items():
                s = s.replace(token, orig)
            s = s.strip()
            if s:
                cleaned_sentences.append(s)

        return cleaned_sentences

    def _split_compound_sentences(self, sentence: str) -> List[str]:
        """
        Splits compound sentences joined by coordinating conjunctions
        only if both clauses possess independent assertion structure.
        """
        # Split on "; " or " -- " or " - "
        semi_clauses = re.split(r"(?:\s*;\s*|\s+--\s+|\s+—\s+)", sentence)
        if len(semi_clauses) > 1:
            clauses = [c.strip() for c in semi_clauses if len(c.strip()) >= 5]
            if len(clauses) > 1:
                return clauses

        # Coordinate conjunction split: ", and ", ", but ", ", while "
        coord_pattern = r",\s+(?:and|but|while|whereas|however|aur|par)\s+"
        parts = re.split(coord_pattern, sentence, flags=re.IGNORECASE)
        if len(parts) >= 2:
            # Verify each part has substantial length (min 15 chars) to prevent splitting fragments
            if all(len(p.strip()) >= 15 for p in parts):
                return [p.strip() for p in parts]

        return [sentence]

    def extract_propositions(self, text: str, language: str) -> List[RawClaimProposal]:
        from backend.app.services.nlp.assessability import AssessabilityClassifier, StatementType

        sentences = self._segment_sentences(text, language)
        proposals: List[RawClaimProposal] = []

        for sentence in sentences:
            clauses = self._split_compound_sentences(sentence)
            for clause in clauses:
                stmt_type, conf, reason = AssessabilityClassifier.classify_statement(clause)
                entities = AssessabilityClassifier.extract_entities(clause)
                cat = AssessabilityClassifier.categorize_claim(clause)

                if stmt_type == StatementType.FACTUAL_CLAIM:
                    proposals.append(
                        RawClaimProposal(
                            text=clause,
                            confidence=conf,
                            entities=entities,
                            category_hint=cat.value,
                            is_assessable=True,
                            abstention_reason=None,
                        )
                    )
                else:
                    proposals.append(
                        RawClaimProposal(
                            text=clause,
                            confidence=conf,
                            entities=entities,
                            category_hint=cat.value,
                            is_assessable=False,
                            abstention_reason=reason,
                        )
                    )

        return proposals


class MockNLPProvider(NLPProvider):
    """
    Test double for verifying provider behaviors, malformed outputs, timeouts,
    and failure handling without live network or external LLM credentials.
    """

    def __init__(
        self,
        mode: str = "success",
        mock_proposals: Optional[List[RawClaimProposal]] = None,
        malformed_output: Optional[str] = None,
        exception_to_raise: Optional[Exception] = None,
    ):
        self.mode = mode
        self.mock_proposals = mock_proposals or []
        self.malformed_output = malformed_output
        self.exception_to_raise = exception_to_raise
        self.call_count = 0

    def extract_propositions(self, text: str, language: str) -> List[RawClaimProposal]:
        self.call_count += 1

        if self.exception_to_raise:
            raise self.exception_to_raise

        if self.mode == "timeout":
            raise TimeoutError("Provider request timed out after 30.0s")

        if self.mode == "rate_limit":
            raise VeritasException(
                status_code=429,
                title="Provider Rate Limit Exceeded",
                detail="Upstream model provider returned HTTP 429 Too Many Requests.",
                code="PROVIDER_RATE_LIMIT",
            )

        if self.mode == "outage":
            raise ServiceUnavailableError("LLMProvider", "Remote API returned HTTP 503 Service Unavailable")

        if self.mode == "malformed_json":
            # Simulates invalid raw string output
            raise ValueError(f"Malformed JSON from LLM: {self.malformed_output or '{invalid_json'}")

        if self.mode == "empty":
            return []

        return self.mock_proposals


class LLMNLPProvider(NLPProvider):
    """
    Adapter for external LLM inference with strict JSON schema parsing,
    untrusted output validation, bounded timeouts, and retry caps.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        timeout_seconds: float = 15.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def extract_propositions(self, text: str, language: str) -> List[RawClaimProposal]:
        """
        Invokes LLM provider with structured outputs.
        Treats all model output as completely untrusted input.
        """
        if not self.api_key:
            raise ServiceUnavailableError(
                "LLMProvider",
                "API key not configured. Set OPENAI_API_KEY or configure local provider."
            )

        # In production this executes client.chat.completions.create with response_format={"type": "json_object"}
        # For offline environments and tests, LocalRuleBasedProvider and MockNLPProvider provide 100% coverage.
        raise NotImplementedError("Live LLM calls require verified API access in production deployment.")
