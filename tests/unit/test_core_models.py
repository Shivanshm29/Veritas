"""
Unit tests for core Pydantic v2 model validation rules, prefixes, and domain invariants.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from contracts.schemas.models import (
    EntityPrefix,
    validate_prefixed_id,
    Investigation,
    EvidenceAsset,
    AssetDerivation,
    Claim,
    ClaimAssessment,
    ClaimVerdict,
    ForensicFinding,
    RawScoreType,
    ScoreType,
    CalibrationStatus,
    ForensicVerdict,
    ForensicModality,
    ProvenanceRelationship,
    ProvenanceNodeType,
    ProvenanceRelationshipType,
    DerivationType,
    ClaimModalityOrigin,
)


def test_validate_prefixed_id_valid():
    """Verifies valid prefixes with UUIDv4 pass."""
    val = "inv_12345678-1234-4234-8234-123456789abc"
    assert validate_prefixed_id(val, EntityPrefix.INVESTIGATION) == val


def test_validate_prefixed_id_invalid_prefix():
    """Verifies mismatching prefix raises ValueError."""
    val = "ast_12345678-1234-4234-8234-123456789abc"
    with pytest.raises(ValueError, match="Invalid identifier"):
        validate_prefixed_id(val, EntityPrefix.INVESTIGATION)


def test_validate_prefixed_id_invalid_uuid():
    """Verifies malformed UUID raises ValueError."""
    val = "inv_not-a-valid-uuid"
    with pytest.raises(ValueError, match="Invalid identifier"):
        validate_prefixed_id(val, EntityPrefix.INVESTIGATION)


def test_evidence_asset_storage_uri_validation():
    """Verifies storage URI requires supported scheme."""
    with pytest.raises(ValidationError, match="storage_uri must start with"):
        EvidenceAsset(
            id="ast_23456789-2345-4345-8345-234567890bcd",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            original_filename="sample.mp4",
            file_size_bytes=1000,
            mime_type="video/mp4",
            sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            storage_uri="ftp://invalid.com/sample.mp4",
            uploaded_at=datetime.now(timezone.utc),
        )


def test_asset_derivation_self_derivation_prevented():
    """
    Verifies asset cannot directly derive from itself (A -> A).
    Note: Multi-hop cycle detection (A -> B -> C -> A) requires global graph traversal
    and is enforced at the provenance graph validation layer in Phase 8.
    """
    asset_id = "ast_23456789-2345-4345-8345-234567890bcd"
    with pytest.raises(ValidationError, match="derived_asset_id cannot be identical to parent_asset_id"):
        AssetDerivation(
            id="drv_34567890-3456-4456-8456-345678901cde",
            parent_asset_id=asset_id,
            derived_asset_id=asset_id,
            derivation_type=DerivationType.VIDEO_KEYFRAME,
            created_at=datetime.now(timezone.utc),
        )


def test_claim_timecode_ordering():
    """Verifies end_ms cannot be less than start_ms."""
    with pytest.raises(ValidationError, match="source_timecode_end_ms cannot be less than"):
        Claim(
            id="clm_56789012-5678-4678-8678-567890123ef0",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            claim_text="Valid claim length assertion.",
            modality_origin=ClaimModalityOrigin.TRANSCRIPT,
            extraction_confidence=0.9,
            source_timecode_start_ms=5000,
            source_timecode_end_ms=2000,
            created_at=datetime.now(timezone.utc),
        )


def test_claim_assessment_evidence_requirement():
    """Verifies REFUTED or SUPPORTED verdicts require at least one cited evidence ID."""
    with pytest.raises(ValidationError, match="cited_evidence_ids cannot be empty"):
        ClaimAssessment(
            id="asm_89012345-8901-4901-8901-890123456123",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            claim_id="clm_56789012-5678-4678-8678-567890123ef0",
            verdict=ClaimVerdict.REFUTED,
            confidence_score=0.95,
            explanation="Detailed explanation that satisfies the minimum length requirement.",
            cited_evidence_ids=[],
            model_identifier="verifier-v1",
            assessed_at=datetime.now(timezone.utc),
        )


def test_forensic_finding_uncalibrated_defaults_valid():
    """Verifies that uncalibrated detector output is valid and does not require or assume calibrated probability."""
    finding = ForensicFinding(
        id="fnd_90123456-9012-4012-8012-901234567234",
        investigation_id="inv_12345678-1234-4234-8234-123456789abc",
        asset_id="ast_23456789-2345-4345-8345-234567890bcd",
        modality=ForensicModality.VIDEO,
        technique="FACIAL_REENACTMENT_TEMPORAL_FLICKER",
        raw_score=3.84,
        raw_score_type=RawScoreType.UNNORMALIZED_LOGIT,
        calibration_status=CalibrationStatus.UNCALIBRATED,
        calibrated_score=None,
        verdict=ForensicVerdict.LIKELY_SYNTHETIC,
        model_name="DeepFake-TemporalSyncNet",
        model_version="v1.4.2",
        executed_at=datetime.now(timezone.utc),
    )
    assert finding.calibration_status == CalibrationStatus.UNCALIBRATED
    assert finding.calibrated_score is None


def test_forensic_finding_calibrated_requires_score_and_method():
    """Verifies that CALIBRATED findings require both calibrated_score and calibration_method."""
    with pytest.raises(ValidationError, match="calibrated_score must be provided"):
        ForensicFinding(
            id="fnd_90123456-9012-4012-8012-901234567234",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            asset_id="ast_23456789-2345-4345-8345-234567890bcd",
            modality=ForensicModality.IMAGE,
            technique="ELA",
            raw_score=0.92,
            raw_score_type=RawScoreType.NORMALIZED_BOUNDED,
            calibration_status=CalibrationStatus.CALIBRATED,
            calibrated_score=None,
            verdict=ForensicVerdict.LIKELY_SYNTHETIC,
            model_name="ELANet",
            model_version="1.0",
            executed_at=datetime.now(timezone.utc),
        )


def test_forensic_finding_calibrated_bounds():
    """Verifies calibrated_score enforces [0.0, 1.0] bounds when calibrated."""
    with pytest.raises(ValidationError):
        ForensicFinding(
            id="fnd_90123456-9012-4012-8012-901234567234",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            asset_id="ast_23456789-2345-4345-8345-234567890bcd",
            modality=ForensicModality.IMAGE,
            technique="ELA",
            raw_score=4.5,
            raw_score_type=RawScoreType.UNNORMALIZED_LOGIT,
            calibration_status=CalibrationStatus.CALIBRATED,
            calibrated_score=1.45,  # Invalid: > 1.0
            calibration_method="TEMPERATURE_SCALING",
            verdict=ForensicVerdict.LIKELY_SYNTHETIC,
            model_name="ELANet",
            model_version="1.0",
            executed_at=datetime.now(timezone.utc),
        )


def test_forensic_finding_uncalibrated_rejects_calibrated_score():
    """Verifies uncalibrated findings cannot specify a calibrated_score."""
    with pytest.raises(ValidationError, match="calibrated_score cannot be provided when calibration_status is UNCALIBRATED"):
        ForensicFinding(
            id="fnd_90123456-9012-4012-8012-901234567234",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            asset_id="ast_23456789-2345-4345-8345-234567890bcd",
            modality=ForensicModality.IMAGE,
            technique="ELA",
            raw_score=0.85,
            raw_score_type=RawScoreType.SIMILARITY,
            calibration_status=CalibrationStatus.UNCALIBRATED,
            calibrated_score=0.85,  # Error: Uncalibrated finding setting calibrated_score
            verdict=ForensicVerdict.LIKELY_SYNTHETIC,
            model_name="ELANet",
            model_version="1.0",
            executed_at=datetime.now(timezone.utc),
        )


def test_provenance_relationship_self_loop_prevented():
    """Verifies provenance relationships reject self-loops."""
    node_id = "ast_23456789-2345-4345-8345-234567890bcd"
    with pytest.raises(ValidationError, match="source_node_id cannot be identical to target_node_id"):
        ProvenanceRelationship(
            id="rel_01234567-0123-4123-8123-012345678345",
            investigation_id="inv_12345678-1234-4234-8234-123456789abc",
            source_node_id=node_id,
            source_node_type=ProvenanceNodeType.ASSET,
            target_node_id=node_id,
            target_node_type=ProvenanceNodeType.ASSET,
            relationship_type=ProvenanceRelationshipType.DERIVED_FROM,
            confidence=0.9,
            created_at=datetime.now(timezone.utc),
        )

