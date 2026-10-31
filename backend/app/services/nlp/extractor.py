"""
Claim extraction and traceability pipeline for Veritas.

Orchestrates input validation, language identification, text normalization,
candidate proposition extraction, span alignment, entity recognition,
deduplication, confidence scoring, and abstention handling.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import List, Optional
import uuid

from contracts.schemas.models import Claim, ClaimCategory, ClaimModalityOrigin, ClaimStatus
from backend.app.core.errors import EmptyTextError, PayloadTooLargeError
from backend.app.core.logging import logger
from backend.app.services.nlp.language import LanguageDetector, LanguageResult
from backend.app.services.nlp.normalization import TextNormalizer, NormalizationResult
from backend.app.services.nlp.provider import NLPProvider, LocalRuleBasedProvider, RawClaimProposal


MAX_INPUT_TEXT_CHARS = 50_000


@dataclass
class UnprocessedSegment:
    """Represents text spans identified as non-factual, opinions, questions, or fragments."""
    text: str
    reason: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None


@dataclass
class ClaimExtractionBatch:
    """Structured output from the claim extraction pipeline."""
    original_text: str
    normalized_text: str
    detected_language: str
    language_confidence: float
    claims: List[Claim]
    unprocessed_segments: List[UnprocessedSegment]
    total_claims: int
    execution_time_ms: int
    extraction_method: str
    warnings: List[str] = field(default_factory=list)


class ClaimExtractionService:
    """
    Modular, multilingual claim extraction service.
    Guarantees strict source-text traceability without inferring truth values.
    """

    def __init__(
        self,
        provider: Optional[NLPProvider] = None,
        language_detector: Optional[LanguageDetector] = None,
        method_version: str = "veritas-claim-nlp-v1",
    ):
        self.provider = provider or LocalRuleBasedProvider()
        self.language_detector = language_detector or LanguageDetector()
        self.method_version = method_version

    def extract_claims(
        self,
        text: str,
        investigation_id: Optional[str] = None,
        source_asset_id: Optional[str] = None,
        modality_origin: Optional[ClaimModalityOrigin] = None,
        source_timecode_start_ms: Optional[int] = None,
        source_timecode_end_ms: Optional[int] = None,
        speaker_tag: Optional[str] = None,
    ) -> ClaimExtractionBatch:
        """
        Executes end-to-end claim extraction over the supplied text.
        """
        start_time = time.perf_counter()
        warnings: List[str] = []

        # 1. Input validation & bounded limits
        if not text or not text.strip():
            raise EmptyTextError("Supplied text is empty or contains only whitespace.")

        if len(text) > MAX_INPUT_TEXT_CHARS:
            raise PayloadTooLargeError(
                max_size_bytes=MAX_INPUT_TEXT_CHARS,
                actual_size_bytes=len(text),
            )

        # 2. Multilingual Language Identification
        lang_res: LanguageResult = self.language_detector.detect(text)
        if lang_res.language == "und":
            warnings.append(
                "Language could not be reliably determined; processed with fallback multilingual heuristics."
            )
        if lang_res.is_code_switched:
            warnings.append(
                "Code-switching or mixed-script content detected; processing with adaptive script boundaries."
            )

        # 3. Deterministic Text Normalization
        norm_res: NormalizationResult = TextNormalizer.normalize(text)

        # 4. Candidate Proposition Extraction via NLP Provider
        proposals: List[RawClaimProposal] = self.provider.extract_propositions(
            norm_res.normalized_text, lang_res.language
        )

        claims: List[Claim] = []
        unprocessed: List[UnprocessedSegment] = []
        seen_texts = set()

        inv_id = investigation_id or f"inv_{uuid.uuid4()}"
        origin = modality_origin or ClaimModalityOrigin.USER_PROMPT

        for prop in proposals:
            # Locate exact character span in original text
            span = TextNormalizer.find_span_in_original(text, prop.text)
            char_start = span[0] if span else None
            char_end = span[1] if span else None

            if not span:
                warnings.append(
                    f"Exact source-span alignment unavailable for segment: '{prop.text[:30]}...'"
                )

            if not prop.is_assessable:
                unprocessed.append(
                    UnprocessedSegment(
                        text=prop.text,
                        reason=prop.abstention_reason or "Non-factual or subjective utterance",
                        char_start=char_start,
                        char_end=char_end,
                    )
                )
                continue

            # Deduplication: suppress duplicate assertions within the same extraction batch
            norm_key = prop.text.strip().lower()
            if norm_key in seen_texts:
                continue
            seen_texts.add(norm_key)

            # Enforce canonical ClaimCategory
            cat = None
            if prop.category_hint:
                try:
                    cat = ClaimCategory(prop.category_hint)
                except ValueError:
                    cat = ClaimCategory.GENERAL

            # Construct canonical Claim object
            claim_id = f"clm_{uuid.uuid4()}"
            now = datetime.now(timezone.utc)

            # Ensure minimum text length requirement (5 chars)
            clean_claim_text = prop.text.strip()
            if len(clean_claim_text) < 5:
                unprocessed.append(
                    UnprocessedSegment(
                        text=clean_claim_text,
                        reason="Claim text below minimum length constraint (5 characters)",
                        char_start=char_start,
                        char_end=char_end,
                    )
                )
                continue

            # Bound maximum length (2000 chars)
            if len(clean_claim_text) > 2000:
                clean_claim_text = clean_claim_text[:1997] + "..."

            claim_obj = Claim(
                id=claim_id,
                investigation_id=inv_id,
                source_asset_id=source_asset_id,
                claim_text=clean_claim_text,
                modality_origin=origin,
                extraction_confidence=max(0.0, min(1.0, round(prop.confidence, 2))),
                source_timecode_start_ms=source_timecode_start_ms,
                source_timecode_end_ms=source_timecode_end_ms,
                speaker_tag=speaker_tag,
                claim_entities=prop.entities,
                category=cat,
                status=ClaimStatus.EXTRACTED,
                source_char_start=char_start,
                source_char_end=char_end,
                language=lang_res.language if lang_res.language != "und" else None,
                extraction_method=self.method_version,
                created_at=now,
            )
            claims.append(claim_obj)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        logger.info(
            f"Extracted {len(claims)} claims ({len(unprocessed)} non-factual segments) "
            f"from text in {elapsed_ms}ms [Language: {lang_res.language}, Method: {self.method_version}]"
        )

        return ClaimExtractionBatch(
            original_text=text,
            normalized_text=norm_res.normalized_text,
            detected_language=lang_res.language,
            language_confidence=lang_res.confidence,
            claims=claims,
            unprocessed_segments=unprocessed,
            total_claims=len(claims),
            execution_time_ms=elapsed_ms,
            extraction_method=self.method_version,
            warnings=warnings,
        )


# Singleton instance
_default_claim_service: Optional[ClaimExtractionService] = None


def get_claim_service() -> ClaimExtractionService:
    global _default_claim_service
    if _default_claim_service is None:
        _default_claim_service = ClaimExtractionService()
    return _default_claim_service
