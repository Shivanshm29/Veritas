"""
Unit tests for NLP Providers (LocalRuleBasedProvider, MockNLPProvider, LLMNLPProvider).
"""

import pytest
from backend.app.core.errors import ServiceUnavailableError, VeritasException
from backend.app.services.nlp.provider import (
    LocalRuleBasedProvider,
    MockNLPProvider,
    LLMNLPProvider,
    RawClaimProposal,
)


def test_rule_based_abbreviation_protection():
    provider = LocalRuleBasedProvider()
    text = "Dr. Smith met with Prof. Jones at the U.S. Capitol. They approved the $3.5 million grant."
    proposals = provider.extract_propositions(text, "en")
    # Should not split on "Dr.", "Prof.", "U.S.", or "3.5"
    assert len(proposals) == 2


def test_mock_provider_timeout_handling():
    mock_p = MockNLPProvider(mode="timeout")
    with pytest.raises(TimeoutError) as exc_info:
        mock_p.extract_propositions("Test text", "en")
    assert "timed out" in str(exc_info.value)


def test_mock_provider_rate_limit_handling():
    mock_p = MockNLPProvider(mode="rate_limit")
    with pytest.raises(VeritasException) as exc_info:
        mock_p.extract_propositions("Test text", "en")
    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "PROVIDER_RATE_LIMIT"


def test_mock_provider_outage_handling():
    mock_p = MockNLPProvider(mode="outage")
    with pytest.raises(ServiceUnavailableError):
        mock_p.extract_propositions("Test text", "en")


def test_mock_provider_malformed_json_handling():
    mock_p = MockNLPProvider(mode="malformed_json", malformed_output="{incomplete_json")
    with pytest.raises(ValueError) as exc_info:
        mock_p.extract_propositions("Test text", "en")
    assert "Malformed JSON" in str(exc_info.value)


def test_llm_provider_missing_key_safe_rejection():
    llm_p = LLMNLPProvider(api_key=None)
    with pytest.raises(ServiceUnavailableError):
        llm_p.extract_propositions("Test text", "en")
