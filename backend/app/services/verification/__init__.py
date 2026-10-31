"""Verification services package for Veritas Phase 4."""
from backend.app.services.verification.stance_classifier import (
    StanceClassificationResult,
    StanceClassifierProtocol,
    RuleBasedStanceClassifier,
    get_stance_classifier,
)
from backend.app.services.verification.aggregation import (
    EvidenceAggregator,
    AggregationEvidenceContext,
)
from backend.app.services.verification.service import (
    VerificationService,
    get_verification_service,
)

__all__ = [
    "StanceClassificationResult",
    "StanceClassifierProtocol",
    "RuleBasedStanceClassifier",
    "get_stance_classifier",
    "EvidenceAggregator",
    "AggregationEvidenceContext",
    "VerificationService",
    "get_verification_service",
]
