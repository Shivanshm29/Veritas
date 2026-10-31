"""
Unit tests for Evidence Aggregation and Epistemic Decision Engine (Phase 4).
"""

from datetime import datetime, timezone
import pytest
from uuid import uuid4

from contracts.schemas.models import (
    Claim,
    ClaimAssessment,
    ClaimCategory,
    ClaimModalityOrigin,
    ClaimStatus,
    ClaimVerdict,
    EvidenceItem,
    EvidenceStance,
    SourceDocument,
)
from backend.app.services.verification.aggregation import EvidenceAggregator


@pytest.fixture
def aggregator():
    return EvidenceAggregator()


@pytest.fixture
def sample_claim():
    return Claim(
        id=f"clm_{uuid4()}",
        investigation_id=f"inv_{uuid4()}",
        claim_text="The Federal Reserve raised interest rates by 50 basis points in September 2026.",
        modality_origin=ClaimModalityOrigin.USER_PROMPT,
        extraction_confidence=0.95,
        status=ClaimStatus.EXTRACTED,
        created_at=datetime.now(timezone.utc),
    )


def test_missing_evidence_guardrail(aggregator, sample_claim):
    """STRICT GUARDRAIL: Absence of evidence must NEVER be equated with REFUTED."""
    assessment: ClaimAssessment = aggregator.aggregate(
        claim=sample_claim,
        evidence_items=[],
        sources=[],
    )
    assert assessment.verdict == ClaimVerdict.INSUFFICIENT_EVIDENCE
    assert assessment.confidence_score == 0.0
    assert assessment.cited_evidence_ids == []
    assert "missing evidence is never equated with proof of falsity" in assessment.explanation


def test_multi_source_supported_with_diversity(aggregator, sample_claim):
    """Corroboration from 2 independent domains yields SUPPORTED with high calibrated confidence."""
    d1 = f"doc_{uuid4()}"
    d2 = f"doc_{uuid4()}"

    sources = [
        SourceDocument(
            id=d1,
            title="Federal Reserve Announcement",
            url="https://federalreserve.gov/release/1",
            domain="federalreserve.gov",
            retrieval_timestamp=datetime.now(timezone.utc),
            content_snippet="Federal Reserve raised interest rates by 50 basis points.",
            content_sha256="0" * 64,
            source_reliability_score=0.95,
            is_simulated=True,
        ),
        SourceDocument(
            id=d2,
            title="Reuters Economic Report",
            url="https://reuters.com/markets/1",
            domain="reuters.com",
            retrieval_timestamp=datetime.now(timezone.utc),
            content_snippet="Fed confirmed 50 bps rate hike in September 2026.",
            content_sha256="0" * 64,
            source_reliability_score=0.92,
            is_simulated=True,
        ),
    ]

    items = [
        EvidenceItem(
            id=f"evi_{uuid4()}",
            claim_id=sample_claim.id,
            source_document_id=d1,
            evidence_text="The Federal Reserve officially confirmed a 50 basis point increase in the federal funds rate.",
            stance=EvidenceStance.SUPPORTS,
            relevance_score=0.95,
            created_at=datetime.now(timezone.utc),
        ),
        EvidenceItem(
            id=f"evi_{uuid4()}",
            claim_id=sample_claim.id,
            source_document_id=d2,
            evidence_text="Reuters verified that the Federal Reserve raised benchmark interest rates by 50 basis points.",
            stance=EvidenceStance.SUPPORTS,
            relevance_score=0.90,
            created_at=datetime.now(timezone.utc),
        ),
    ]

    assessment = aggregator.aggregate(sample_claim, items, sources)
    assert assessment.verdict == ClaimVerdict.SUPPORTED
    assert assessment.confidence_score >= 0.85
    assert len(assessment.cited_evidence_ids) == 2
    assert len(assessment.explanation) >= 20


def test_single_source_confidence_cap(aggregator, sample_claim):
    """A single source domain caps confidence at <= 0.75 and documents limitation."""
    d1 = f"doc_{uuid4()}"
    sources = [
        SourceDocument(
            id=d1,
            title="Single Source",
            url="https://apnews.com/fed-story",
            domain="apnews.com",
            retrieval_timestamp=datetime.now(timezone.utc),
            content_snippet="Federal Reserve raised rates.",
            content_sha256="0" * 64,
            source_reliability_score=0.90,
            is_simulated=True,
        )
    ]
    items = [
        EvidenceItem(
            id=f"evi_{uuid4()}",
            claim_id=sample_claim.id,
            source_document_id=d1,
            evidence_text="AP confirmed that the Federal Reserve raised interest rates by 50 basis points.",
            stance=EvidenceStance.SUPPORTS,
            relevance_score=0.95,
            created_at=datetime.now(timezone.utc),
        )
    ]

    assessment = aggregator.aggregate(sample_claim, items, sources)
    assert assessment.verdict == ClaimVerdict.SUPPORTED
    assert assessment.confidence_score <= 0.75
    assert any("single source domain" in l.lower() for l in assessment.limitations)


def test_genuine_contradiction_detection(aggregator, sample_claim):
    """When credible sources disagree, output CONTRADICTORY_EVIDENCE with conflicting points."""
    d1 = f"doc_{uuid4()}"
    d2 = f"doc_{uuid4()}"

    sources = [
        SourceDocument(
            id=d1,
            title="Commerce Report",
            url="https://commerce.gov/report",
            domain="commerce.gov",
            retrieval_timestamp=datetime.now(timezone.utc),
            content_snippet="Confirmed 50 bps increase.",
            content_sha256="0" * 64,
            source_reliability_score=0.92,
            is_simulated=True,
        ),
        SourceDocument(
            id=d2,
            title="Fed Release",
            url="https://federalreserve.gov/statement",
            domain="federalreserve.gov",
            retrieval_timestamp=datetime.now(timezone.utc),
            content_snippet="Denied rate hike; rates held steady.",
            content_sha256="0" * 64,
            source_reliability_score=0.95,
            is_simulated=True,
        ),
    ]

    items = [
        EvidenceItem(
            id=f"evi_{uuid4()}",
            claim_id=sample_claim.id,
            source_document_id=d1,
            evidence_text="Provisional government bulletins confirmed interest rates increased by 50 basis points.",
            stance=EvidenceStance.SUPPORTS,
            relevance_score=0.90,
            created_at=datetime.now(timezone.utc),
        ),
        EvidenceItem(
            id=f"evi_{uuid4()}",
            claim_id=sample_claim.id,
            source_document_id=d2,
            evidence_text="Official Federal Reserve transcripts denied interest rates increased, confirming rates were held unchanged.",
            stance=EvidenceStance.CONTRADICTS,
            relevance_score=0.95,
            created_at=datetime.now(timezone.utc),
        ),
    ]

    assessment = aggregator.aggregate(sample_claim, items, sources)
    assert assessment.verdict == ClaimVerdict.CONTRADICTORY_EVIDENCE
    assert len(assessment.conflicting_points) >= 1
    assert len(assessment.cited_evidence_ids) >= 2


def test_syndicated_duplicate_discounting(aggregator, sample_claim):
    """Near-duplicate syndicated articles are discounted to prevent consensus inflation."""
    sources = []
    items = []
    for i in range(4):
        d_id = f"doc_{uuid4()}"
        sources.append(
            SourceDocument(
                id=d_id,
                title=f"Syndicated {i}",
                url=f"https://syndicate{i}.com/wire",
                domain=f"syndicate{i}.com",
                retrieval_timestamp=datetime.now(timezone.utc),
                content_snippet="Identical wire dispatch.",
                content_sha256="0" * 64,
                source_reliability_score=0.80,
                is_simulated=True,
            )
        )
        items.append(
            EvidenceItem(
                id=f"evi_{uuid4()}",
                claim_id=sample_claim.id,
                source_document_id=d_id,
                evidence_text="The Federal Reserve officially confirmed a 50 basis point increase in benchmark borrowing rates.",
                stance=EvidenceStance.SUPPORTS,
                relevance_score=0.90,
                created_at=datetime.now(timezone.utc),
            )
        )

    assessment = aggregator.aggregate(sample_claim, items, sources)
    assert assessment.verdict == ClaimVerdict.SUPPORTED
    assert any("syndicated" in l.lower() or "duplicate" in l.lower() for l in assessment.limitations)


def test_epistemic_calibration_disclaimer_present(aggregator, sample_claim):
    """Verifies that uncalibrated scores are never represented as probabilities without disclaimer."""
    assessment = aggregator.aggregate(sample_claim, [], [])
    assert any("calibrated heuristic" in l.lower() or "probability" in l.lower() for l in assessment.limitations)
