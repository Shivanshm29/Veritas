"""
Unit tests for assessability classification, entity extraction, and claim categorization.
"""

from contracts.schemas.models import ClaimCategory
from backend.app.services.nlp.assessability import (
    AssessabilityClassifier,
    StatementType,
)


def test_classify_factual_statement():
    stmt = "The World Health Organization confirmed 450 new cases of the virus in October 2026."
    stmt_type, conf, reason = AssessabilityClassifier.classify_statement(stmt)
    assert stmt_type == StatementType.FACTUAL_CLAIM
    assert conf >= 0.75


def test_classify_question():
    stmt1 = "Did the finance minister announce a tax increase yesterday?"
    stmt_type1, conf1, _ = AssessabilityClassifier.classify_statement(stmt1)
    assert stmt_type1 == StatementType.QUESTION
    assert conf1 >= 0.85

    stmt2 = "What caused the power outage across the northern region"
    stmt_type2, conf2, _ = AssessabilityClassifier.classify_statement(stmt2)
    assert stmt_type2 == StatementType.QUESTION


def test_classify_pure_opinion():
    stmt = "In my opinion, this is the worst tax reform bill ever proposed."
    stmt_type, conf, reason = AssessabilityClassifier.classify_statement(stmt)
    assert stmt_type == StatementType.OPINION
    assert "opinion" in reason.lower()


def test_classify_command_or_request():
    stmt = "Please share this urgent alert with everyone immediately!"
    stmt_type, conf, reason = AssessabilityClassifier.classify_statement(stmt)
    assert stmt_type == StatementType.COMMAND_OR_REQUEST
    assert "command" in reason.lower() or "imperative" in reason.lower()


def test_classify_greeting_or_fragment():
    stmt1 = "Hello good morning everyone"
    stmt_type1, _, _ = AssessabilityClassifier.classify_statement(stmt1)
    assert stmt_type1 == StatementType.INCOMPLETE_OR_FRAGMENT

    stmt2 = "breaking news!!"
    stmt_type2, _, _ = AssessabilityClassifier.classify_statement(stmt2)
    assert stmt_type2 == StatementType.INCOMPLETE_OR_FRAGMENT


def test_categorize_claims():
    assert (
        AssessabilityClassifier.categorize_claim("The prime minister and parliament passed the law")
        == ClaimCategory.POLITICAL
    )
    assert (
        AssessabilityClassifier.categorize_claim("The central bank raised interest rates to combat inflation")
        == ClaimCategory.FINANCIAL
    )
    assert (
        AssessabilityClassifier.categorize_claim("The hospital confirmed the vaccine prevented virus infections")
        == ClaimCategory.PUBLIC_HEALTH
    )
    assert (
        AssessabilityClassifier.categorize_claim("The 6.8 magnitude earthquake caused severe flooding and casualties")
        == ClaimCategory.DISASTER
    )
    assert (
        AssessabilityClassifier.categorize_claim("The famous Hollywood actress was married in secret")
        == ClaimCategory.CELEBRITY_IDENTITY
    )


def test_extract_entities():
    text = "The Ministry of Finance announced on October 25, 2026 that $15 billion would be allocated to Mumbai."
    entities = AssessabilityClassifier.extract_entities(text)
    assert any("Ministry of Finance" in e for e in entities)
    assert any("15 billion" in e or "$15 billion" in e for e in entities)
    assert any("2026" in e or "October 25, 2026" in e for e in entities)


def test_classify_conversational_greeting_with_temporal_filler():
    # Regression test for conversational broadcast greeting false-positive
    stmt = "Hello good morning to everyone tuning in today!"
    stmt_type, conf, reason = AssessabilityClassifier.classify_statement(stmt)
    assert stmt_type == StatementType.INCOMPLETE_OR_FRAGMENT
    assert conf >= 0.85
    assert "greeting" in reason.lower()
