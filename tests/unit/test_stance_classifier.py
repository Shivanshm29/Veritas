"""
Unit tests for Evidence Stance Classification Service (Phase 4).
"""

import pytest
from contracts.schemas.models import EvidenceStance
from backend.app.services.verification.stance_classifier import (
    RuleBasedStanceClassifier,
    StanceClassificationResult,
    get_stance_classifier,
)


@pytest.fixture
def classifier():
    return RuleBasedStanceClassifier()


def test_classify_explicit_support(classifier):
    claim = "The European Space Agency confirmed water on Mars."
    evidence = "The European Space Agency officially confirmed that new satellite radar verified liquid water on Mars."
    result = classifier.classify_stance(claim, evidence)
    assert result.stance == EvidenceStance.SUPPORTS
    assert result.confidence >= 0.70
    assert "confirmed" in result.key_phrases or "verified" in result.key_phrases
    assert len(result.rationale) >= 10


def test_classify_explicit_refutation_debunking(classifier):
    claim = "Drinking bleach eliminates the influenza virus."
    evidence = "Public health authorities debunked the dangerous rumor, confirming drinking bleach is false and life-threatening."
    result = classifier.classify_stance(claim, evidence)
    assert result.stance == EvidenceStance.CONTRADICTS
    assert result.confidence >= 0.70
    assert any(k in ["debunked", "false"] for k in result.key_phrases)


def test_classify_fact_check_confirmation_of_misinformation(classifier):
    """Verifies that 'WHO confirmed that claims are misinformation' correctly classifies as CONTRADICTS."""
    claim = "Drinking saltwater cures infectious viral disease."
    evidence = "The World Health Organization confirmed that claims suggesting drinking saltwater cures disease are dangerous misinformation."
    result = classifier.classify_stance(claim, evidence)
    assert result.stance == EvidenceStance.CONTRADICTS
    assert "misinformation" in result.key_phrases


def test_classify_negation_contradiction(classifier):
    claim = "The Prime Minister resigned from office this morning."
    evidence = "The Prime Minister did not resign and reiterated commitment to serving the full parliamentary term."
    result = classifier.classify_stance(claim, evidence)
    assert result.stance == EvidenceStance.CONTRADICTS
    assert any("did not" in k for k in result.key_phrases)


def test_classify_insufficient_unclear(classifier):
    claim = "The company will be acquired by an international conglomerate next month."
    evidence = "Industry analysts noted that acquisition speculation remains unconfirmed and highly uncertain."
    result = classifier.classify_stance(claim, evidence)
    assert result.stance == EvidenceStance.INSUFFICIENT


def test_classify_irrelevant_low_overlap(classifier):
    claim = "The regional railway network announced a twenty percent fare reduction."
    evidence = "Marine biologists studied the migration patterns of humpback whales in the North Atlantic."
    result = classifier.classify_stance(claim, evidence)
    assert result.stance == EvidenceStance.INSUFFICIENT
    assert "negligible semantic overlap" in result.rationale


def test_classify_empty_evidence(classifier):
    claim = "Interest rates were raised by fifty basis points."
    result = classifier.classify_stance(claim, "")
    assert result.stance == EvidenceStance.INSUFFICIENT
    assert result.confidence == 0.0


def test_singleton_accessor():
    c1 = get_stance_classifier()
    c2 = get_stance_classifier()
    assert c1 is c2
