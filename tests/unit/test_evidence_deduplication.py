"""
Unit tests for Evidence and Source Document deduplication (Phase 3).
"""

import pytest
from backend.app.services.retrieval.deduplication import EvidenceDeduplicator


def test_sha256_computation():
    text = "The Federal Reserve raised interest rates."
    h1 = EvidenceDeduplicator.compute_sha256(text)
    h2 = EvidenceDeduplicator.compute_sha256(text)
    assert h1 == h2
    assert len(h1) == 64
    assert h1 == h1.lower()


def test_jaccard_similarity():
    text_a = "The Federal Reserve raised benchmark interest rates by 50 basis points on Wednesday."
    text_b = "The Federal Reserve raised benchmark interest rates by 50 basis points on Wednesday afternoon."
    sim = EvidenceDeduplicator.compute_jaccard_similarity(text_a, text_b)
    assert sim >= 0.80

    text_c = "A severe earthquake struck the coastal province yesterday destroying bridges."
    sim_distinct = EvidenceDeduplicator.compute_jaccard_similarity(text_a, text_c)
    assert sim_distinct < 0.10


def test_exact_hash_deduplication():
    doc1 = {
        "id": "doc_11111111-1111-4111-8111-111111111111",
        "title": "Story A",
        "content": "Exact content matching across syndicate publisher outlets.",
    }
    doc2 = {
        "id": "doc_22222222-2222-4222-8222-222222222222",
        "title": "Story B (Syndicated copy)",
        "content": "Exact content matching across syndicate publisher outlets.",
    }

    unique_docs, dup_docs, count = EvidenceDeduplicator.deduplicate_documents([doc1, doc2])
    assert len(unique_docs) == 1
    assert len(dup_docs) == 1
    assert count == 1
    assert dup_docs[0]["is_duplicate"] is True
    assert dup_docs[0]["duplicate_of_id"] == doc1["id"]
    assert dup_docs[0]["duplicate_type"] == "EXACT_HASH_MATCH"


def test_syndicated_wire_near_duplicate():
    doc1 = {
        "id": "doc_11111111-1111-4111-8111-111111111111",
        "title": "Reuters Dispatch",
        "content": (
            "Health authorities in the capital confirmed twelve hundred new viral cases "
            "following rapid testing across major metropolitan hospitals on Monday."
        ),
    }
    doc2 = {
        "id": "doc_22222222-2222-4222-8222-222222222222",
        "title": "Affiliate Morning Report",
        "content": (
            "Health authorities in the capital confirmed twelve hundred new viral cases "
            "following rapid testing across major metropolitan hospitals on Monday morning."
        ),
    }

    unique_docs, dup_docs, count = EvidenceDeduplicator.deduplicate_documents([doc1, doc2])
    assert len(unique_docs) == 1
    assert len(dup_docs) == 1
    assert count == 1
    assert dup_docs[0]["duplicate_type"] == "SYNDICATED_WIRE_RECOPY"
    assert dup_docs[0]["duplicate_of_id"] == doc1["id"]
    assert dup_docs[0]["similarity_score"] >= 0.80


def test_indic_unicode_token_similarity():
    hindi_1 = "भारतीय रिजर्व बैंक ने आज रेपो दर में पच्चीस आधार अंकों की वृद्धि की।"
    hindi_2 = "भारतीय रिजर्व बैंक ने आज रेपो दर में पच्चीस आधार अंकों की वृद्धि की घोषणा की।"
    sim = EvidenceDeduplicator.compute_jaccard_similarity(hindi_1, hindi_2)
    assert sim >= 0.70

