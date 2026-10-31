"""
Unit tests for text normalization, Unicode handling, and span alignment.
"""

from backend.app.services.nlp.normalization import TextNormalizer, NormalizationResult


def test_empty_normalization():
    res = TextNormalizer.normalize("")
    assert res.normalized_text == ""
    assert res.char_count_original == 0
    assert not res.was_modified


def test_unicode_nfc_normalization():
    # Combining character vs precomposed: 'e' + '\u0301' (combining acute) vs '\u00e9'
    decomposed = "e\u0301"
    precomposed = "\u00e9"
    res = TextNormalizer.normalize(decomposed)
    assert res.normalized_text == precomposed
    assert res.was_modified


def test_whitespace_regularization():
    text = "  The   minister    announced     a reform.  \n\n\n  New   budget approved.   "
    res = TextNormalizer.normalize(text)
    assert res.normalized_text == "The minister announced a reform.\nNew budget approved."
    assert res.was_modified


def test_control_character_stripping():
    # ASCII bell \x07 and null \x00 should be stripped, newline preserved
    dirty = "Line 1\x07\x00 with bell.\nLine 2\x1b."
    res = TextNormalizer.normalize(dirty)
    assert "\x07" not in res.normalized_text
    assert "\x00" not in res.normalized_text
    assert "Line 1 with bell.\nLine 2." == res.normalized_text


def test_preservation_of_negation_and_numbers():
    text = "The committee did NOT approve the $5.4 billion subsidy on October 12, 2026."
    res = TextNormalizer.normalize(text)
    assert "NOT" in res.normalized_text
    assert "$5.4 billion" in res.normalized_text
    assert "October 12, 2026" in res.normalized_text


def test_span_alignment_exact():
    original = "Breaking report: The Central Bank raised interest rates by 0.5% today."
    phrase = "The Central Bank raised interest rates by 0.5% today"
    span = TextNormalizer.find_span_in_original(original, phrase)
    assert span is not None
    start, end = span
    assert original[start:end] == phrase


def test_span_alignment_multilingual_hindi():
    original = "मुख्य समाचार: सरकार ने नई शिक्षा नीति को मंजूरी दे दी है।"
    phrase = "सरकार ने नई शिक्षा नीति को मंजूरी दे दी है"
    span = TextNormalizer.find_span_in_original(original, phrase)
    assert span is not None
    start, end = span
    assert original[start:end] == phrase


def test_span_alignment_whitespace_flexible():
    original = "The   senate   passed\n   the  bill."
    phrase = "The senate passed the bill"
    span = TextNormalizer.find_span_in_original(original, phrase)
    assert span is not None
    start, end = span
    # Matches the exact character slice in original
    assert "senate" in original[start:end]
    assert "bill" in original[start:end]


def test_span_alignment_unavailable_returns_none():
    original = "The president arrived in Tokyo yesterday."
    missing_phrase = "The prime minister visited London"
    span = TextNormalizer.find_span_in_original(original, missing_phrase)
    assert span is None
