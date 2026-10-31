"""
Unit tests for query generation, refinement, and expansion (Phase 3).
"""

from datetime import datetime, timezone
import pytest
from backend.app.core.errors import EmptyTextError, PayloadTooLargeError
from backend.app.services.retrieval.query import QueryGenerator
from backend.app.services.retrieval.service import EvidenceRetrievalService
from contracts.schemas.models import Claim, ClaimCategory, ClaimModalityOrigin, ClaimStatus


def test_query_generation_from_text():
    text = "The Federal Reserve raised interest rates by 0.5% in September 2026."
    query = QueryGenerator.generate(text)
    assert query.raw_query == text
    assert "Federal" in query.search_terms
    assert "Reserve" in query.search_terms
    assert "0.5%" in query.search_terms
    assert query.temporal_anchor.lower() == "september"


def test_query_generation_from_claim():
    claim = Claim(
        id="clm_12345678-1234-4234-8234-123456789abc",
        investigation_id="inv_12345678-1234-4234-8234-123456789abc",
        claim_text="The Ministry of Health confirmed 1,200 new cases of the virus across the capital on Monday.",
        modality_origin=ClaimModalityOrigin.USER_PROMPT,
        extraction_confidence=0.92,
        claim_entities=["Ministry of Health", "1,200", "Monday"],
        category=ClaimCategory.PUBLIC_HEALTH,
        status=ClaimStatus.EXTRACTED,
        language="en",
        created_at=datetime.now(timezone.utc),
    )
    query = QueryGenerator.from_claim(claim)
    assert query.claim_id == claim.id
    assert query.category == "PUBLIC_HEALTH"
    assert "Ministry of Health" in query.entities
    assert any("Ministry" in t or "Ministry of Health" in t for t in query.search_terms)


def test_empty_query_raises_empty_text_error():
    service = EvidenceRetrievalService()
    with pytest.raises(EmptyTextError):
        service.retrieve_for_text("")
    with pytest.raises(EmptyTextError):
        service.retrieve_for_text("   \n\t  ")


def test_oversized_query_raises_payload_too_large():
    service = EvidenceRetrievalService()
    huge_text = "evidence " * 1000  # > 5000 chars
    with pytest.raises(PayloadTooLargeError):
        service.retrieve_for_text(huge_text)

