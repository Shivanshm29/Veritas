"""
SQLAlchemy ORM model for Claim records in Veritas.
"""

from datetime import datetime, timezone
import json
from typing import List, Optional
from sqlalchemy import Column, String, BigInteger, Integer, Float, Text, DateTime, JSON
from backend.app.db.base import Base
from contracts.schemas.models import Claim, ClaimCategory, ClaimModalityOrigin, ClaimStatus


class ClaimRecord(Base):
    """ORM representation of an extracted claim."""
    __tablename__ = "claims"

    id = Column(String(64), primary_key=True, index=True)
    investigation_id = Column(String(64), nullable=False, index=True)
    source_asset_id = Column(String(64), nullable=True, index=True)
    claim_text = Column(Text, nullable=False)
    modality_origin = Column(String(50), nullable=False)
    extraction_confidence = Column(Float, nullable=False)
    source_timecode_start_ms = Column(BigInteger, nullable=True)
    source_timecode_end_ms = Column(BigInteger, nullable=True)
    source_char_start = Column(Integer, nullable=True)
    source_char_end = Column(Integer, nullable=True)
    speaker_tag = Column(String(100), nullable=True)
    claim_entities = Column(JSON, nullable=False, default=list)
    category = Column(String(50), nullable=True)
    status = Column(String(50), default=ClaimStatus.EXTRACTED.value, nullable=False)
    language = Column(String(10), nullable=True)
    extraction_method = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_schema(self) -> Claim:
        """Converts the ORM record to the canonical Claim Pydantic model."""
        c_at = self.created_at
        if c_at is not None and c_at.tzinfo is None:
            c_at = c_at.replace(tzinfo=timezone.utc)

        entities = self.claim_entities
        if isinstance(entities, str):
            try:
                entities = json.loads(entities)
            except Exception:
                entities = []
        elif entities is None:
            entities = []

        cat = None
        if self.category:
            try:
                cat = ClaimCategory(self.category)
            except ValueError:
                cat = None

        origin = ClaimModalityOrigin(self.modality_origin) if self.modality_origin else ClaimModalityOrigin.USER_PROMPT
        st = ClaimStatus(self.status) if self.status else ClaimStatus.EXTRACTED

        return Claim(
            id=self.id,
            investigation_id=self.investigation_id,
            source_asset_id=self.source_asset_id,
            claim_text=self.claim_text,
            modality_origin=origin,
            extraction_confidence=self.extraction_confidence,
            source_timecode_start_ms=self.source_timecode_start_ms,
            source_timecode_end_ms=self.source_timecode_end_ms,
            speaker_tag=self.speaker_tag,
            claim_entities=entities,
            category=cat,
            status=st,
            source_char_start=self.source_char_start,
            source_char_end=self.source_char_end,
            language=self.language,
            extraction_method=self.extraction_method,
            created_at=c_at,
        )
