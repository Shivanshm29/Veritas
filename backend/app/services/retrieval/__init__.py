"""
Source Intelligence & Evidence Retrieval service package for Veritas.
"""

from backend.app.services.retrieval.credibility import (
    DomainCategory,
    SourceCredibilityEvaluator,
    SourceCredibilityResult,
)
from backend.app.services.retrieval.deduplication import EvidenceDeduplicator
from backend.app.services.retrieval.passage_extractor import (
    CandidatePassage,
    PassageExtractor,
)
from backend.app.services.retrieval.provider import (
    EvidenceRetrievalProvider,
    ExternalSearchProvider,
    HybridRetrievalProvider,
    LexicalBM25Provider,
    RawDocumentProposal,
    SimulatedRetrievalProvider,
)
from backend.app.services.retrieval.query import EvidenceQuery, QueryGenerator
from backend.app.services.retrieval.service import (
    EvidenceRetrievalBatch,
    EvidenceRetrievalService,
    get_retrieval_service,
)

__all__ = [
    "EvidenceQuery",
    "QueryGenerator",
    "SourceCredibilityEvaluator",
    "SourceCredibilityResult",
    "DomainCategory",
    "EvidenceDeduplicator",
    "PassageExtractor",
    "CandidatePassage",
    "EvidenceRetrievalProvider",
    "RawDocumentProposal",
    "SimulatedRetrievalProvider",
    "LexicalBM25Provider",
    "HybridRetrievalProvider",
    "ExternalSearchProvider",
    "EvidenceRetrievalBatch",
    "EvidenceRetrievalService",
    "get_retrieval_service",
]

