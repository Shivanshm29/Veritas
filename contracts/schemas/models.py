"""
Canonical Pydantic v2 Models for Veritas.

Shared contracts between Person 1 (Ingestion & Claims) and Person 2 (Forensics & Workspace).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ==============================================================================
# 1. IDENTIFIER CONSTANTS & VALIDATORS
# ==============================================================================

class EntityPrefix(str, Enum):
    INVESTIGATION = "inv"
    EVIDENCE_ASSET = "ast"
    ASSET_DERIVATION = "drv"
    PROCESSING_RESULT = "res"
    CLAIM = "clm"
    SOURCE_DOCUMENT = "doc"
    EVIDENCE_ITEM = "evi"
    CLAIM_ASSESSMENT = "asm"
    FORENSIC_FINDING = "fnd"
    PROVENANCE_RELATIONSHIP = "rel"
    INVESTIGATION_REPORT = "rpt"
    AUDIT_EVENT = "adt"


UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"

def validate_prefixed_id(id_val: str, expected_prefix: EntityPrefix) -> str:
    """Validates that id matches <prefix>_<uuid4> format."""
    pattern = rf"^{expected_prefix.value}_{UUID_PATTERN}$"
    if not re.match(pattern, id_val, re.IGNORECASE):
        raise ValueError(
            f"Invalid identifier '{id_val}'. Expected format '{expected_prefix.value}_<uuid4>'."
        )
    return id_val


# ==============================================================================
# 2. ENUM DEFINITIONS
# ==============================================================================

class InvestigationStatus(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    ANALYSIS_COMPLETE = "ANALYSIS_COMPLETE"
    REPORTED = "REPORTED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"


class PriorityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AssetStatus(str, Enum):
    INGESTED = "INGESTED"
    STORED = "STORED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"


class C2PAStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    ABSENT = "ABSENT"
    UNSUPPORTED = "UNSUPPORTED"


class DerivationType(str, Enum):
    VIDEO_AUDIO_EXTRACTION = "VIDEO_AUDIO_EXTRACTION"
    VIDEO_KEYFRAME = "VIDEO_KEYFRAME"
    IMAGE_FACE_CROP = "IMAGE_FACE_CROP"
    AUDIO_SEGMENT = "AUDIO_SEGMENT"
    SPECTROGRAM = "SPECTROGRAM"
    TEXT_TRANSCRIPTION = "TEXT_TRANSCRIPTION"


class PipelineStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


class ClaimModalityOrigin(str, Enum):
    TRANSCRIPT = "TRANSCRIPT"
    OCR = "OCR"
    USER_PROMPT = "USER_PROMPT"
    EXTERNAL_POST = "EXTERNAL_POST"


class ClaimStatus(str, Enum):
    EXTRACTED = "EXTRACTED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    UNVERIFIABLE = "UNVERIFIABLE"


class ClaimCategory(str, Enum):
    POLITICAL = "POLITICAL"
    FINANCIAL = "FINANCIAL"
    PUBLIC_HEALTH = "PUBLIC_HEALTH"
    DISASTER = "DISASTER"
    CELEBRITY_IDENTITY = "CELEBRITY_IDENTITY"
    GENERAL = "GENERAL"


class EvidenceStance(str, Enum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    NEUTRAL = "NEUTRAL"
    INSUFFICIENT = "INSUFFICIENT"


class RetrievalMethod(str, Enum):
    BM25 = "BM25"
    VECTOR_KNN = "VECTOR_KNN"
    HYBRID_RRF = "HYBRID_RRF"
    MANUAL = "MANUAL"


class ClaimVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ForensicModality(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class RawScoreType(str, Enum):
    UNNORMALIZED_LOGIT = "UNNORMALIZED_LOGIT"
    ANOMALY_INDEX = "ANOMALY_INDEX"
    SIMILARITY = "SIMILARITY"
    DISTANCE = "DISTANCE"
    NORMALIZED_BOUNDED = "NORMALIZED_BOUNDED"
    OTHER = "OTHER"


# Backward-compatibility alias for initial draft imports
ScoreType = RawScoreType


class CalibrationStatus(str, Enum):
    UNCALIBRATED = "UNCALIBRATED"
    CALIBRATED = "CALIBRATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ForensicVerdict(str, Enum):
    LIKELY_SYNTHETIC = "LIKELY_SYNTHETIC"
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    INCONCLUSIVE = "INCONCLUSIVE"


class ProvenanceNodeType(str, Enum):
    ASSET = "ASSET"
    CLAIM = "CLAIM"
    SOURCE_DOCUMENT = "SOURCE_DOCUMENT"
    FORENSIC_FINDING = "FORENSIC_FINDING"
    ENTITY = "ENTITY"


class ProvenanceRelationshipType(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    CONTRADICTS = "CONTRADICTS"
    SUPPORTS = "SUPPORTS"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    CORROBORATED_BY = "CORROBORATED_BY"
    DUPLICATE_OF = "DUPLICATE_OF"
    SHARES_PERCEPTUAL_HASH = "SHARES_PERCEPTUAL_HASH"


class ReportStatus(str, Enum):
    DRAFT = "DRAFT"
    FINAL = "FINAL"
    SUPERSEDED = "SUPERSEDED"


class OverallMediaAuthenticity(str, Enum):
    LIKELY_AUTHENTIC = "LIKELY_AUTHENTIC"
    LIKELY_MANIPULATED = "LIKELY_MANIPULATED"
    SYNTHETIC_ELEMENTS_DETECTED = "SYNTHETIC_ELEMENTS_DETECTED"
    INCONCLUSIVE = "INCONCLUSIVE"


class OverallClaimValidity(str, Enum):
    MOSTLY_TRUE = "MOSTLY_TRUE"
    MOSTLY_FALSE = "MOSTLY_FALSE"
    MIXED = "MIXED"
    UNVERIFIABLE = "UNVERIFIABLE"


class AuditEventType(str, Enum):
    INVESTIGATION_CREATED = "INVESTIGATION_CREATED"
    ASSET_INGESTED = "ASSET_INGESTED"
    PIPELINE_EXECUTED = "PIPELINE_EXECUTED"
    CLAIM_EXTRACTED = "CLAIM_EXTRACTED"
    CLAIM_ASSESSED = "CLAIM_ASSESSED"
    FORENSIC_ANALYSIS_COMPLETED = "FORENSIC_ANALYSIS_COMPLETED"
    REPORT_GENERATED = "REPORT_GENERATED"
    STATUS_CHANGED = "STATUS_CHANGED"


class ActorRole(str, Enum):
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    AUTOMATION_WORKER = "AUTOMATION_WORKER"
    ADMIN = "ADMIN"


# ==============================================================================
# 3. BASE CONFIGURATION MODEL
# ==============================================================================

class VeritasBaseModel(BaseModel):
    """Base model enforcing JSON snake_case and strict validation rules."""
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        extra="forbid",
    )


# Backward-compatibility alias
PramaanBaseModel = VeritasBaseModel


# ==============================================================================
# 4. SHARED CANONICAL DATA MODELS
# ==============================================================================

class Investigation(VeritasBaseModel):
    """Model 1: Top-level investigation grouping evidence and claims."""
    id: str = Field(..., description="ID with format inv_<uuid4>")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: InvestigationStatus = Field(default=InvestigationStatus.CREATED)
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    tags: List[str] = Field(default_factory=list)
    created_by: str = Field(..., min_length=1)
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)


class EvidenceAsset(VeritasBaseModel):
    """Model 2: Primary immutable evidence file."""
    id: str = Field(..., description="ID with format ast_<uuid4>")
    investigation_id: str
    original_filename: str = Field(..., min_length=1, max_length=500)
    file_size_bytes: int = Field(..., gt=0)
    mime_type: str = Field(..., pattern=r"^[a-z]+/[a-z0-9\.\+-]+$")
    sha256_hash: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    storage_uri: str = Field(..., min_length=5)
    source_url: Optional[str] = None
    source_platform: Optional[str] = None
    captured_at: Optional[datetime] = None
    c2pa_manifest_present: bool = Field(default=False)
    c2pa_status: C2PAStatus = Field(default=C2PAStatus.ABSENT)
    status: AssetStatus = Field(default=AssetStatus.INGESTED)
    quarantine_reason: Optional[str] = None
    uploaded_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ASSET)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

    @field_validator("storage_uri")
    @classmethod
    def check_uri(cls, v: str) -> str:
        if not re.match(r"^(file|s3|minio|memory)://", v):
            raise ValueError("storage_uri must start with file://, s3://, minio://, or memory://")
        return v


class AssetDerivation(VeritasBaseModel):
    """Model 3: Records derived child assets (keyframes, audio tracks)."""
    id: str = Field(..., description="ID with format drv_<uuid4>")
    parent_asset_id: str
    derived_asset_id: str
    derivation_type: DerivationType
    derivation_parameters: Dict[str, Any] = Field(default_factory=dict)
    operator_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.ASSET_DERIVATION)

    @field_validator("parent_asset_id", "derived_asset_id")
    @classmethod
    def check_asset_ids(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ASSET)

    @model_validator(mode="after")
    def check_direct_self_reference(self) -> "AssetDerivation":
        """
        Rejects immediate direct self-derivation (A -> A).
        Note: Multi-hop graph cycle detection (A -> B -> C -> A) requires global graph traversal
        and is enforced at the provenance graph validation layer in Phase 8.
        """
        if self.parent_asset_id == self.derived_asset_id:
            raise ValueError(
                "derived_asset_id cannot be identical to parent_asset_id "
                "(direct self-reference rejected; multi-hop cycle detection is enforced at the graph layer in Phase 8)."
            )
        return self


class ProcessingResult(VeritasBaseModel):
    """Model 4: Algorithmic processing output (OCR, ASR, embeddings)."""
    id: str = Field(..., description="ID with format res_<uuid4>")
    asset_id: str
    pipeline_name: str = Field(..., min_length=1)
    pipeline_version: str = Field(..., min_length=1)
    status: PipelineStatus
    execution_time_ms: int = Field(..., ge=0)
    extracted_text: Optional[str] = None
    face_bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list)
    transcript_segments: List[Dict[str, Any]] = Field(default_factory=list)
    raw_features_uri: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.PROCESSING_RESULT)

    @field_validator("asset_id")
    @classmethod
    def check_asset_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ASSET)

    @model_validator(mode="after")
    def check_error_on_failed(self) -> "ProcessingResult":
        if self.status == PipelineStatus.FAILED and not self.error_message:
            raise ValueError("error_message is required when status is FAILED.")
        return self


class Claim(VeritasBaseModel):
    """Model 5: Verifiable factual assertion extracted from media."""
    id: str = Field(..., description="ID with format clm_<uuid4>")
    investigation_id: str
    source_asset_id: Optional[str] = None
    claim_text: str = Field(..., min_length=5, max_length=2000)
    modality_origin: ClaimModalityOrigin
    extraction_confidence: float = Field(..., ge=0.0, le=1.0)
    source_timecode_start_ms: Optional[int] = Field(None, ge=0)
    source_timecode_end_ms: Optional[int] = Field(None, ge=0)
    speaker_tag: Optional[str] = None
    claim_entities: List[str] = Field(default_factory=list)
    category: Optional[ClaimCategory] = None
    status: ClaimStatus = Field(default=ClaimStatus.EXTRACTED)
    created_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.CLAIM)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

    @field_validator("source_asset_id")
    @classmethod
    def check_asset_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ASSET)
        return v

    @model_validator(mode="after")
    def check_timecode_ordering(self) -> "Claim":
        if self.source_timecode_start_ms is not None and self.source_timecode_end_ms is not None:
            if self.source_timecode_end_ms < self.source_timecode_start_ms:
                raise ValueError("source_timecode_end_ms cannot be less than source_timecode_start_ms.")
        return self


class SourceDocument(VeritasBaseModel):
    """Model 6: External reference material retrieved during verification."""
    id: str = Field(..., description="ID with format doc_<uuid4>")
    title: str = Field(..., min_length=1)
    url: str = Field(..., pattern=r"^https?://")
    domain: str = Field(..., min_length=1)
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[datetime] = None
    retrieval_timestamp: datetime
    content_snippet: str = Field(..., min_length=10)
    content_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    source_reliability_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    full_text_storage_uri: Optional[str] = None

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.SOURCE_DOCUMENT)


class EvidenceItem(VeritasBaseModel):
    """Model 7: Specific passage from a source document evaluated against a claim."""
    id: str = Field(..., description="ID with format evi_<uuid4>")
    claim_id: str
    source_document_id: str
    evidence_text: str = Field(..., min_length=10, max_length=4000)
    stance: EvidenceStance
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    page_number: Optional[int] = Field(None, ge=1)
    paragraph_index: Optional[int] = Field(None, ge=0)
    retrieval_method: Optional[RetrievalMethod] = None
    created_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ITEM)

    @field_validator("claim_id")
    @classmethod
    def check_claim_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.CLAIM)

    @field_validator("source_document_id")
    @classmethod
    def check_doc_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.SOURCE_DOCUMENT)


class ClaimAssessment(VeritasBaseModel):
    """Model 8: Synthesized semantic factuality assessment of a claim."""
    id: str = Field(..., description="ID with format asm_<uuid4>")
    investigation_id: str
    claim_id: str
    verdict: ClaimVerdict
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str = Field(..., min_length=20)
    cited_evidence_ids: List[str] = Field(default_factory=list)
    conflicting_points: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    model_identifier: str = Field(..., min_length=1)
    assessed_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.CLAIM_ASSESSMENT)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

    @field_validator("claim_id")
    @classmethod
    def check_claim_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.CLAIM)

    @field_validator("cited_evidence_ids")
    @classmethod
    def check_cited_ids(cls, v: List[str]) -> List[str]:
        for item in v:
            validate_prefixed_id(item, EntityPrefix.EVIDENCE_ITEM)
        return v

    @model_validator(mode="after")
    def check_evidence_requirement(self) -> "ClaimAssessment":
        if self.verdict in [ClaimVerdict.SUPPORTED, ClaimVerdict.REFUTED]:
            if not self.cited_evidence_ids:
                raise ValueError("cited_evidence_ids cannot be empty when verdict is SUPPORTED or REFUTED.")
        return self


class ForensicFinding(VeritasBaseModel):
    """Model 9: Signal manipulation detection finding from Person 2's forensic engines."""
    id: str = Field(..., description="ID with format fnd_<uuid4>")
    investigation_id: str
    asset_id: str
    modality: ForensicModality
    technique: str = Field(..., min_length=1)
    raw_score: float = Field(..., description="Raw quantitative score directly output by detector.")
    raw_score_type: RawScoreType = Field(
        default=RawScoreType.UNNORMALIZED_LOGIT,
        description="Type and scale of raw detector score (UNNORMALIZED_LOGIT, ANOMALY_INDEX, SIMILARITY, DISTANCE, NORMALIZED_BOUNDED, OTHER)."
    )
    calibration_status: CalibrationStatus = Field(
        default=CalibrationStatus.UNCALIBRATED,
        description="Explicit calibration status of the finding score."
    )
    calibrated_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Empirically calibrated probability in [0.0, 1.0], populated ONLY if formal calibration was performed."
    )
    calibration_method: Optional[str] = Field(
        None,
        description="Method used for calibration (e.g. TEMPERATURE_SCALING, PLATT_SCALING, ISOTONIC_REGRESSION)."
    )
    calibration_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Supporting empirical calibration metrics (e.g. calibration dataset ID, ECE, Brier score)."
    )
    verdict: ForensicVerdict
    score_interpretation: Optional[str] = Field(
        None,
        description="Investigator-facing explanation of raw/calibrated score interpretation and thresholds."
    )
    region_of_interest: Optional[Dict[str, Any]] = None
    heatmap_artifact_uri: Optional[str] = None
    detected_artifacts: List[str] = Field(default_factory=list)
    limitations_notes: Optional[str] = Field(
        None,
        description="Documented detector and operational limitations affecting finding accuracy."
    )
    model_name: str = Field(..., min_length=1)
    model_version: str = Field(..., min_length=1)
    executed_at: datetime

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_score_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "score_type" in data and "raw_score_type" not in data:
                data["raw_score_type"] = data.pop("score_type")
        return data

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.FORENSIC_FINDING)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

    @field_validator("asset_id")
    @classmethod
    def check_asset_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.EVIDENCE_ASSET)

    @model_validator(mode="after")
    def check_calibration_consistency(self) -> "ForensicFinding":
        if self.calibration_status == CalibrationStatus.CALIBRATED:
            if self.calibrated_score is None:
                raise ValueError("calibrated_score must be provided when calibration_status is CALIBRATED.")
            if not (0.0 <= self.calibrated_score <= 1.0):
                raise ValueError("calibrated_score must be bounded in [0.0, 1.0].")
            if not self.calibration_method:
                raise ValueError("calibration_method must be specified when calibration_status is CALIBRATED.")
        elif self.calibration_status == CalibrationStatus.UNCALIBRATED:
            if self.calibrated_score is not None:
                raise ValueError("calibrated_score cannot be provided when calibration_status is UNCALIBRATED.")
        return self


class ProvenanceRelationship(VeritasBaseModel):
    """Model 10: Directed relationship edge in the provenance graph."""
    id: str = Field(..., description="ID with format rel_<uuid4>")
    investigation_id: str
    source_node_id: str
    source_node_type: ProvenanceNodeType
    target_node_id: str
    target_node_type: ProvenanceNodeType
    relationship_type: ProvenanceRelationshipType
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_citation_id: Optional[str] = None
    edge_weight: float = Field(default=1.0, ge=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.PROVENANCE_RELATIONSHIP)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

    @model_validator(mode="after")
    def check_self_loop(self) -> "ProvenanceRelationship":
        """
        Rejects immediate direct self-loop (node -> node).
        Note: Multi-hop cycle detection requires global graph traversal and is enforced in Phase 8.
        """
        if self.source_node_id == self.target_node_id:
            raise ValueError(
                "source_node_id cannot be identical to target_node_id "
                "(direct self-loop rejected; multi-hop cycle detection is enforced at the graph layer in Phase 8)."
            )
        return self


class InvestigationReport(VeritasBaseModel):
    """Model 11: Final structured investigative report."""
    id: str = Field(..., description="ID with format rpt_<uuid4>")
    investigation_id: str
    version: int = Field(..., ge=1)
    report_status: ReportStatus = Field(default=ReportStatus.DRAFT)
    executive_summary: str = Field(..., min_length=50)
    overall_media_authenticity: OverallMediaAuthenticity
    overall_claim_validity: OverallClaimValidity
    included_finding_ids: List[str] = Field(default_factory=list)
    included_assessment_ids: List[str] = Field(default_factory=list)
    disclaimers: List[str] = Field(default_factory=list)
    lead_investigator_id: str = Field(..., min_length=1)
    exported_pdf_uri: Optional[str] = None
    generated_at: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION_REPORT)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

    @field_validator("included_finding_ids")
    @classmethod
    def check_finding_ids(cls, v: List[str]) -> List[str]:
        for item in v:
            validate_prefixed_id(item, EntityPrefix.FORENSIC_FINDING)
        return v

    @field_validator("included_assessment_ids")
    @classmethod
    def check_assessment_ids(cls, v: List[str]) -> List[str]:
        for item in v:
            validate_prefixed_id(item, EntityPrefix.CLAIM_ASSESSMENT)
        return v


class AuditEvent(VeritasBaseModel):
    """Model 12: Immutable cryptographic audit trail record."""
    id: str = Field(..., description="ID with format adt_<uuid4>")
    investigation_id: str
    event_type: AuditEventType
    actor_id: str = Field(..., min_length=1)
    actor_role: ActorRole
    target_entity_id: Optional[str] = None
    target_entity_type: Optional[str] = None
    action_details: Dict[str, Any] = Field(default_factory=dict)
    sha256_payload_hash: Optional[str] = Field(None, pattern=r"^[0-9a-f]{64}$")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.AUDIT_EVENT)

    @field_validator("investigation_id")
    @classmethod
    def check_inv_id(cls, v: str) -> str:
        return validate_prefixed_id(v, EntityPrefix.INVESTIGATION)

