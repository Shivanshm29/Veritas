"""
SQLAlchemy ORM model for ClaimAssessment records in Veritas.

Persists multi-source synthesis, stance aggregation, and factuality assessments
generated during Phase 4: Evidence-Based Claim Verification.
"""

from datetime import datetime, timezone
import json
from typing import List, Optional
from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, JSON
from backend.app.db.base import Base
from contracts.schemas.models import ClaimAssessment, ClaimVerdict


class ClaimAssessmentRecord(Base):
    """ORM representation of a synthesized semantic claim assessment."""
    __tablename__ = "claim_assessments"

    id = Column(String(64), primary_key=True, index=True)
    investigation_id = Column(String(64), nullable=False, index=True)
    claim_id = Column(
        String(64),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verdict = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    cited_evidence_ids = Column(JSON, nullable=False, default=list)
    conflicting_points = Column(JSON, nullable=False, default=list)
    limitations = Column(JSON, nullable=False, default=list)
    model_identifier = Column(String(100), nullable=False)
    assessed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_schema(self) -> ClaimAssessment:
        """Converts the ORM record to the canonical ClaimAssessment Pydantic model."""
        a_at = self.assessed_at
        if a_at is not None and a_at.tzinfo is None:
            a_at = a_at.replace(tzinfo=timezone.utc)

        def _parse_list(val):
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return []
            elif val is None:
                return []
            return list(val)

        cited_ids = _parse_list(self.cited_evidence_ids)
        conflicts = _parse_list(self.conflicting_points)
        limits = _parse_list(self.limitations)

        vrd = ClaimVerdict(self.verdict) if self.verdict else ClaimVerdict.INSUFFICIENT_EVIDENCE

        return ClaimAssessment(
            id=self.id,
            investigation_id=self.investigation_id,
            claim_id=self.claim_id,
            verdict=vrd,
            confidence_score=self.confidence_score,
            explanation=self.explanation,
            cited_evidence_ids=cited_ids,
            conflicting_points=conflicts,
            limitations=limits,
            model_identifier=self.model_identifier,
            assessed_at=a_at,
        )
