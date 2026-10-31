"""
Unit tests for Passage Extraction and Relevance Scoring (Phase 3).
"""

import pytest
from backend.app.services.retrieval.passage_extractor import PassageExtractor
from contracts.schemas.models import EvidenceStance


def test_passage_extraction_and_relevance_ranking():
    doc_text = (
        "The Federal Reserve announced on Wednesday that benchmark interest rates were raised by 0.5%.\n\n"
        "In international sports news, the national cricket team won the championship match in London.\n\n"
        "Officials confirmed that the monetary policy tightening aims to curb persistent inflation."
    )
    query_terms = ["Federal", "Reserve", "rates", "interest", "0.5%"]
    passages = PassageExtractor.extract_passages(doc_text, query_terms=query_terms, max_passages=2)

    assert len(passages) == 2
    # The top passage should be the monetary policy paragraph with highest overlap
    assert "Federal Reserve" in passages[0].text
    assert passages[0].relevance_score >= 0.50
    assert passages[0].stance_hint in [EvidenceStance.SUPPORTS, EvidenceStance.NEUTRAL]
    assert passages[0].page_number is None


def test_passage_length_bounds():
    short_text = "Hi"  # Less than 10 characters
    assert PassageExtractor.extract_passages(short_text, ["test"]) == []

    huge_para = "A" * 5000
    passages = PassageExtractor.extract_passages(huge_para, ["A"])
    assert len(passages) == 1
    assert len(passages[0].text) <= PassageExtractor.MAX_PASSAGE_CHARS
    assert passages[0].text.endswith("...")


def test_passage_stance_heuristics():
    support_text = "The health ministry officially confirmed and verified that cases have fallen by 20%."
    refute_text = "The authorities denied the viral rumors and confirmed the story was a complete hoax."
    neutral_text = "The committee held its standard scheduled meeting on Tuesday morning."

    p_sup = PassageExtractor.extract_passages(support_text, ["ministry", "cases"])
    p_ref = PassageExtractor.extract_passages(refute_text, ["rumors", "hoax"])
    p_neu = PassageExtractor.extract_passages(neutral_text, ["committee", "meeting"])

    assert p_sup[0].stance_hint == EvidenceStance.SUPPORTS
    assert p_ref[0].stance_hint == EvidenceStance.REFUTES
    assert p_neu[0].stance_hint == EvidenceStance.NEUTRAL


def test_empty_or_whitespace_document():
    assert PassageExtractor.extract_passages("", ["query"]) == []
    assert PassageExtractor.extract_passages("   \n\n\t   ", ["query"]) == []

