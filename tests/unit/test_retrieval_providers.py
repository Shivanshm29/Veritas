"""
Unit tests for Retrieval Providers and Failure Modes (Phase 3).
"""

import pytest
from backend.app.core.errors import ServiceUnavailableError, VeritasException
from backend.app.services.retrieval.provider import (
    ExternalSearchProvider,
    HybridRetrievalProvider,
    LexicalBM25Provider,
    RawDocumentProposal,
    SimulatedRetrievalProvider,
)
from backend.app.services.retrieval.query import EvidenceQuery
from contracts.schemas.models import RetrievalMethod


def _make_query(terms: list[str]) -> EvidenceQuery:
    return EvidenceQuery(raw_query=" ".join(terms), search_terms=terms)


def test_simulated_provider_success():
    provider = SimulatedRetrievalProvider()
    query = _make_query(["Federal", "Reserve", "rates", "interest"])
    results = provider.retrieve(query, max_results=5)

    assert len(results) > 0
    top = results[0]
    assert isinstance(top, RawDocumentProposal)
    assert top.is_simulated is True
    assert "Federal Reserve" in top.title
    assert "fed.gov.example" in top.domain


def test_simulated_provider_failure_modes():
    # 1. Timeout
    provider_timeout = SimulatedRetrievalProvider(mode="timeout")
    with pytest.raises(TimeoutError):
        provider_timeout.retrieve(_make_query(["test"]))

    # 2. Rate limit (HTTP 429)
    provider_rate = SimulatedRetrievalProvider(mode="rate_limit")
    with pytest.raises(VeritasException) as exc_info:
        provider_rate.retrieve(_make_query(["test"]))
    assert exc_info.value.status_code == 429

    # 3. Outage (HTTP 503)
    provider_outage = SimulatedRetrievalProvider(mode="outage")
    with pytest.raises(ServiceUnavailableError):
        provider_outage.retrieve(_make_query(["test"]))

    # 4. Malformed payload
    provider_malformed = SimulatedRetrievalProvider(mode="malformed")
    with pytest.raises(ValueError):
        provider_malformed.retrieve(_make_query(["test"]))

    # 5. Empty results
    provider_empty = SimulatedRetrievalProvider(mode="empty")
    res = provider_empty.retrieve(_make_query(["test"]))
    assert res == []


def test_lexical_bm25_provider():
    corpus = [
        {
            "title": "Quantum Computing Advances",
            "url": "https://example.com/quantum",
            "domain": "example.com",
            "content": "Superconducting qubits demonstrate fault-tolerant quantum error correction.",
        },
        {
            "title": "Deep Sea Marine Biology",
            "url": "https://example.com/marine",
            "domain": "example.com",
            "content": "Hydrothermal vents support diverse chemosynthetic ecosystems in abyssal trenches.",
        },
    ]
    bm25 = LexicalBM25Provider(corpus=corpus)
    query = _make_query(["quantum", "qubits"])
    results = bm25.retrieve(query)

    assert len(results) == 1
    assert results[0].title == "Quantum Computing Advances"
    assert results[0].retrieval_method == RetrievalMethod.BM25
    assert "bm25_score" in results[0].metadata


def test_hybrid_rrf_retrieval_provider():
    corpus_a = [
        {
            "title": "Doc A",
            "url": "https://a.org/1",
            "domain": "a.org",
            "content": "Solar power generation increased significantly in 2026.",
            "keywords": ["solar", "power", "2026"],
        }
    ]
    corpus_b = [
        {
            "title": "Doc B",
            "url": "https://b.org/2",
            "domain": "b.org",
            "content": "Wind turbine efficiency reached record highs across Europe.",
            "keywords": ["wind", "turbine", "europe"],
        }
    ]
    p_a = SimulatedRetrievalProvider(corpus=corpus_a)
    p_b = SimulatedRetrievalProvider(corpus=corpus_b)

    hybrid = HybridRetrievalProvider(lexical_provider=p_a, secondary_provider=p_b)
    query = _make_query(["solar", "wind", "power"])
    results = hybrid.retrieve(query)

    assert len(results) == 2
    assert results[0].retrieval_method == RetrievalMethod.HYBRID_RRF
    assert "rrf_score" in results[0].metadata


def test_external_search_provider_unconfigured_raises_service_unavailable():
    provider = ExternalSearchProvider(api_key=None, endpoint_url=None)
    with pytest.raises(ServiceUnavailableError):
        provider.retrieve(_make_query(["test"]))

