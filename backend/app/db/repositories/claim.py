"""
Claim repository for database interactions in Veritas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.claim import ClaimRecord


class ClaimRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, claim: ClaimRecord) -> ClaimRecord:
        """Persists a new claim record."""
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def create_batch(self, claims: List[ClaimRecord]) -> List[ClaimRecord]:
        """Persists a batch of claim records in a single transaction."""
        if not claims:
            return []
        self.db.add_all(claims)
        self.db.commit()
        for c in claims:
            self.db.refresh(c)
        return claims

    def get_by_id(self, claim_id: str) -> Optional[ClaimRecord]:
        """Retrieves a claim record by its prefixed id (clm_...)."""
        return self.db.query(ClaimRecord).filter(ClaimRecord.id == claim_id).first()

    def list_by_investigation(
        self,
        investigation_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ClaimRecord]:
        """Lists claims belonging to an investigation with optional filters."""
        query = self.db.query(ClaimRecord).filter(ClaimRecord.investigation_id == investigation_id)
        if category:
            query = query.filter(ClaimRecord.category == category)
        if status:
            query = query.filter(ClaimRecord.status == status)
        return query.order_by(ClaimRecord.created_at.desc()).offset(offset).limit(limit).all()

    def list_by_asset(
        self,
        source_asset_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ClaimRecord]:
        """Lists claims derived from a specific source asset."""
        return (
            self.db.query(ClaimRecord)
            .filter(ClaimRecord.source_asset_id == source_asset_id)
            .order_by(ClaimRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete(self, claim_id: str) -> bool:
        """Deletes a claim record by id."""
        record = self.get_by_id(claim_id)
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False
