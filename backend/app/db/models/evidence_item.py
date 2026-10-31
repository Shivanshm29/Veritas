"""
SQLAlchemy ORM model for EvidenceItem records in Veritas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from backend.app.db.base import Base
from contracts.schemas.models import EvidenceItem, EvidenceStance, RetrievalMethod


class EvidenceItemRecord(Base):
    """ORM representation of a specific retrieved passage evaluated against a claim."""
    __tablename__ = "evidence_items"

    id = Column(String(64), primary_key=True, index=True)
    claim_id = Column(String(64), nullable=False, index=True)
    source_document_id = Column(
        String(64),
        ForeignKey("source_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_text = Column(Text, nullable=False)
    stance = Column(String(50), nullable=False, default=EvidenceStance.NEUTRAL.value)
    relevance_score = Column(Float, nullable=False)
    page_number = Column(Integer, nullable=True)
    paragraph_index = Column(Integer, nullable=True)
    retrieval_method = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_schema(self) -> EvidenceItem:
        """Converts the ORM record to the canonical EvidenceItem Pydantic model."""
        c_at = self.created_at
        if c_at is not None and c_at.tzinfo is None:
            c_at = c_at.replace(tzinfo=timezone.utc)

        st = EvidenceStance(self.stance) if self.stance else EvidenceStance.NEUTRAL
        rm = RetrievalMethod(self.retrieval_method) if self.retrieval_method else None

        return EvidenceItem(
            id=self.id,
            claim_id=self.claim_id,
            source_document_id=self.source_document_id,
            evidence_text=self.evidence_text,
            stance=st,
            relevance_score=self.relevance_score,
            page_number=self.page_number,
            paragraph_index=self.paragraph_index,
            retrieval_method=rm,
            created_at=c_at,
        )

