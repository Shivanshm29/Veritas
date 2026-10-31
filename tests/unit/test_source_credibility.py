"""
Unit tests for Source Credibility and Domain Reliability evaluation (Phase 3).
"""

import pytest
from backend.app.services.retrieval.credibility import (
    DomainCategory,
    SourceCredibilityEvaluator,
    SourceCredibilityResult,
)


def test_government_domain_evaluation():
    urls = [
        "https://www.cdc.gov/flu/weekly",
        "https://pib.gov.in/PressReleasePage.aspx",
        "https://www.gov.uk/guidance/covid-19",
        "https://who.int/emergencies/disease-outbreak-news",
    ]
    for url in urls:
        res = SourceCredibilityEvaluator.evaluate(url)
        assert res.category == DomainCategory.GOVERNMENT_OFFICIAL
        assert res.reliability_score >= 0.90
        assert res.is_calibrated_probability is False
        assert "Heuristic domain credibility score" in res.limitations_disclaimer


def test_academic_domain_evaluation():
    urls = [
        "https://cs.stanford.edu/research",
        "https://www.ox.ac.uk/news",
        "https://iitd.ac.in/announcements",
    ]
    for url in urls:
        res = SourceCredibilityEvaluator.evaluate(url)
        assert res.category == DomainCategory.ACADEMIC_RESEARCH
        assert res.reliability_score >= 0.85
        assert res.is_calibrated_probability is False


def test_fact_check_domain_evaluation():
    urls = [
        "https://www.snopes.com/fact-check/example-claim",
        "https://factcheck.org/2026/09/investigation",
        "https://altnews.in/viral-video-verification",
    ]
    for url in urls:
        res = SourceCredibilityEvaluator.evaluate(url)
        assert res.category == DomainCategory.FACT_CHECKING_ORGANIZATION
        assert res.reliability_score >= 0.90
        assert res.is_calibrated_probability is False


def test_established_news_evaluation():
    urls = [
        "https://www.reuters.com/world/india/report",
        "https://apnews.com/article/financial-markets",
        "https://www.bbc.com/news/world",
    ]
    for url in urls:
        res = SourceCredibilityEvaluator.evaluate(url)
        assert res.category == DomainCategory.ESTABLISHED_NEWS
        assert res.reliability_score >= 0.80
        assert res.is_calibrated_probability is False


def test_user_generated_content_evaluation():
    urls = [
        "https://twitter.com/someuser/status/123456",
        "https://reddit.com/r/technology/comments/abc",
        "https://tiktok.com/@creator/video/123",
    ]
    for url in urls:
        res = SourceCredibilityEvaluator.evaluate(url)
        assert res.category == DomainCategory.USER_GENERATED_CONTENT
        assert res.reliability_score <= 0.50
        assert res.is_calibrated_probability is False


def test_unknown_novel_domain_evaluation():
    url = "https://unregistered-blog-2026-xyz.org/story"
    res = SourceCredibilityEvaluator.evaluate(url)
    assert res.category == DomainCategory.UNKNOWN_OR_UNCLASSIFIED
    assert res.reliability_score == 0.60
    assert res.is_calibrated_probability is False


def test_empty_or_invalid_domain():
    for invalid in ["", "   ", None]:
        res = SourceCredibilityEvaluator.evaluate(invalid or "")
        assert res.category == DomainCategory.UNKNOWN_OR_UNCLASSIFIED
        assert res.reliability_score is None
        assert res.is_calibrated_probability is False

