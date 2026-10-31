"""
Natural Language Processing & Claim Intelligence Services for Veritas.
"""

from backend.app.services.nlp.language import LanguageDetector, LanguageResult
from backend.app.services.nlp.normalization import TextNormalizer, NormalizationResult
from backend.app.services.nlp.assessability import (
    AssessabilityClassifier,
    StatementType,
)
from backend.app.services.nlp.provider import (
    NLPProvider,
    LocalRuleBasedProvider,
    MockNLPProvider,
    LLMNLPProvider,
    RawClaimProposal,
)
from backend.app.services.nlp.extractor import (
    ClaimExtractionService,
    ClaimExtractionBatch,
    UnprocessedSegment,
    get_claim_service,
)

__all__ = [
    "LanguageDetector",
    "LanguageResult",
    "TextNormalizer",
    "NormalizationResult",
    "AssessabilityClassifier",
    "StatementType",
    "NLPProvider",
    "LocalRuleBasedProvider",
    "MockNLPProvider",
    "LLMNLPProvider",
    "RawClaimProposal",
    "ClaimExtractionService",
    "ClaimExtractionBatch",
    "UnprocessedSegment",
    "get_claim_service",
]
