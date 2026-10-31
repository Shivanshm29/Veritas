"""
ClaimAssessment repository for database interactions in Veritas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.claim_assessment import ClaimAssessmentRecord


class ClaimAssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, assessment: ClaimAssessmentRecord) -> ClaimAssessmentRecord:
        """Persists a new claim assessment record."""
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_by_id(self, assessment_id: str) -> Optional[ClaimAssessmentRecord]:
        """Retrieves a claim assessment record by its prefixed id (asm_...)."""
        return (
            self.db.query(ClaimAssessmentRecord)
            .filter(ClaimAssessmentRecord.id == assessment_id)
            .first()
        )

    def get_by_claim_id(self, claim_id: str) -> List[ClaimAssessmentRecord]:
        """Retrieves assessments for a specific claim ordered by most recent."""
        return (
            self.db.query(ClaimAssessmentRecord)
            .filter(ClaimAssessmentRecord.claim_id == claim_id)
            .order_by(ClaimAssessmentRecord.assessed_at.desc())
            .all()
        )

    def get_latest_by_claim_id(self, claim_id: str) -> Optional[ClaimAssessmentRecord]:
        """Retrieves the most recent assessment for a claim."""
        return (
            self.db.query(ClaimAssessmentRecord)
            .filter(ClaimAssessmentRecord.claim_id == claim_id)
            .order_by(ClaimAssessmentRecord.assessed_at.desc())
            .first()
        )

    def list(
        self,
        investigation_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        verdict: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ClaimAssessmentRecord]:
        """Lists claim assessments with optional filtering."""
        query = self.db.query(ClaimAssessmentRecord)
        if investigation_id:
            query = query.filter(ClaimAssessmentRecord.investigation_id == investigation_id)
        if claim_id:
            query = query.filter(ClaimAssessmentRecord.claim_id == claim_id)
        if verdict:
            query = query.filter(ClaimAssessmentRecord.verdict == verdict)
        return query.order_by(ClaimAssessmentRecord.assessed_at.desc()).offset(offset).limit(limit).all()
