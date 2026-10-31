"""
EvidenceItem repository for database interactions in Veritas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.evidence_item import EvidenceItemRecord


class EvidenceItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, item: EvidenceItemRecord, commit: bool = True) -> EvidenceItemRecord:
        """Persists a new EvidenceItem record."""
        self.db.add(item)
        if commit:
            self.db.commit()
            self.db.refresh(item)
        return item

    def create_batch(
        self, items: List[EvidenceItemRecord], commit: bool = True
    ) -> List[EvidenceItemRecord]:
        """Persists a batch of EvidenceItem records in a transaction."""
        if not items:
            return []
        self.db.add_all(items)
        if commit:
            self.db.commit()
            for i in items:
                self.db.refresh(i)
        else:
            self.db.flush()
        return items

    def get_by_id(self, item_id: str) -> Optional[EvidenceItemRecord]:
        """Retrieves an EvidenceItem record by prefixed ID (evi_...)."""
        return self.db.query(EvidenceItemRecord).filter(EvidenceItemRecord.id == item_id).first()

    def list_by_claim(
        self,
        claim_id: str,
        min_relevance: Optional[float] = None,
        stance: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvidenceItemRecord]:
        """Lists evidence items evaluated for a specific claim."""
        query = self.db.query(EvidenceItemRecord).filter(EvidenceItemRecord.claim_id == claim_id)
        if min_relevance is not None:
            query = query.filter(EvidenceItemRecord.relevance_score >= min_relevance)
        if stance is not None:
            query = query.filter(EvidenceItemRecord.stance == stance)
        return (
            query.order_by(EvidenceItemRecord.relevance_score.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_by_source_document(
        self, source_document_id: str, limit: int = 50, offset: int = 0
    ) -> List[EvidenceItemRecord]:
        """Lists evidence items extracted from a specific source document."""
        return (
            self.db.query(EvidenceItemRecord)
            .filter(EvidenceItemRecord.source_document_id == source_document_id)
            .order_by(EvidenceItemRecord.relevance_score.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_all(
        self,
        min_relevance: Optional[float] = None,
        stance: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvidenceItemRecord]:
        """Lists evidence items with optional filtering."""
        query = self.db.query(EvidenceItemRecord)
        if min_relevance is not None:
            query = query.filter(EvidenceItemRecord.relevance_score >= min_relevance)
        if stance is not None:
            query = query.filter(EvidenceItemRecord.stance == stance)
        return (
            query.order_by(EvidenceItemRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete(self, item_id: str) -> bool:
        """Deletes an EvidenceItem record by ID."""
        record = self.get_by_id(item_id)
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False

