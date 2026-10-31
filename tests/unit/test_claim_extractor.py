"""
Unit tests for ClaimExtractionService pipeline, span tracking, and abstentions.
"""

import pytest
from contracts.schemas.models import ClaimCategory, ClaimModalityOrigin, ClaimStatus
from backend.app.core.errors import EmptyTextError, PayloadTooLargeError
from backend.app.services.nlp.extractor import ClaimExtractionService


@pytest.fixture
def service():
    return ClaimExtractionService()


def test_empty_text_raises_empty_text_error(service):
    with pytest.raises(EmptyTextError):
        service.extract_claims("")

    with pytest.raises(EmptyTextError):
        service.extract_claims("   \t\n  ")


def test_oversized_text_raises_payload_too_large(service):
    huge_text = "Statement. " * 6000  # > 50,000 chars
    with pytest.raises(PayloadTooLargeError):
        service.extract_claims(huge_text)


def test_extract_single_factual_claim(service):
    text = "The Ministry of Health announced a nationwide vaccination campaign on October 15, 2026."
    batch = service.extract_claims(text)

    assert batch.total_claims == 1
    assert len(batch.claims) == 1
    claim = batch.claims[0]

    assert claim.id.startswith("clm_")
    assert claim.investigation_id.startswith("inv_")
    assert claim.modality_origin == ClaimModalityOrigin.USER_PROMPT
    assert claim.category == ClaimCategory.PUBLIC_HEALTH
    assert claim.status == ClaimStatus.EXTRACTED
    assert claim.source_char_start is not None
    assert claim.source_char_end is not None
    assert text[claim.source_char_start:claim.source_char_end] == claim.claim_text
    assert claim.language == "en"
    assert claim.extraction_confidence >= 0.70


def test_extract_multiple_claims_with_span_alignment(service):
    text = (
        "The Federal Reserve increased benchmark rates by 25 basis points yesterday. "
        "Meanwhile, unemployment dropped to 3.8% across metropolitan districts."
    )
    batch = service.extract_claims(text)

    assert batch.total_claims == 2
    for claim in batch.claims:
        assert claim.source_char_start is not None
        assert claim.source_char_end is not None
        # Assert exact span slice in original text
        extracted_slice = text[claim.source_char_start:claim.source_char_end]
        assert extracted_slice == claim.claim_text


def test_compound_sentence_handling(service):
    text = (
        "The transport minister resigned after the inquiry, "
        "and the cabinet announced emergency railway safety audits."
    )
    batch = service.extract_claims(text)
    assert batch.total_claims >= 1


def test_non_factual_utterances_recorded_as_unprocessed(service):
    text = (
        "Hello everyone! "
        "Did the president sign the executive order today? "
        "In my opinion, this policy is completely terrible. "
        "The Treasury confirmed the budget surplus reached $4 billion in September 2026."
    )
    batch = service.extract_claims(text)

    # Only the factual treasury statement should be extracted as a Claim
    assert batch.total_claims == 1
    assert "Treasury confirmed" in batch.claims[0].claim_text

    # The greeting, question, and opinion should be captured in unprocessed_segments
    assert len(batch.unprocessed_segments) >= 3
    reasons = [u.reason.lower() for u in batch.unprocessed_segments]
    assert any("interrogative" in r or "question" in r for r in reasons)
    assert any("opinion" in r or "subjective" in r for r in reasons)


def test_deduplication_of_identical_claims(service):
    text = (
        "The state highway authority closed Bridge 4 for emergency repairs today. "
        "The state highway authority closed Bridge 4 for emergency repairs today."
    )
    batch = service.extract_claims(text)
    assert batch.total_claims == 1


def test_multilingual_hindi_extraction(service):
    text = "भारतीय रिजर्व बैंक ने आज रेपो दर में 25 आधार अंकों की वृद्धि की घोषणा की।"
    batch = service.extract_claims(text)

    assert batch.detected_language == "hi"
    assert batch.total_claims == 1
    claim = batch.claims[0]
    assert claim.language == "hi"
    assert claim.source_char_start is not None
    assert text[claim.source_char_start:claim.source_char_end] == claim.claim_text
