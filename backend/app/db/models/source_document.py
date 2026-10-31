"""
SQLAlchemy ORM model for SourceDocument records in Veritas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from backend.app.db.base import Base
from contracts.schemas.models import SourceDocument


class SourceDocumentRecord(Base):
    """ORM representation of an external source document."""
    __tablename__ = "source_documents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=True)
    publisher = Column(String(255), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    retrieval_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    content_snippet = Column(Text, nullable=False)
    content_sha256 = Column(String(64), nullable=False, index=True)
    source_reliability_score = Column(Float, nullable=True)
    full_text_storage_uri = Column(String(500), nullable=True)
    is_simulated = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_schema(self) -> SourceDocument:
        """Converts the ORM record to the canonical SourceDocument Pydantic model."""
        r_time = self.retrieval_timestamp
        if r_time is not None and r_time.tzinfo is None:
            r_time = r_time.replace(tzinfo=timezone.utc)

        p_date = self.published_date
        if p_date is not None and p_date.tzinfo is None:
            p_date = p_date.replace(tzinfo=timezone.utc)

        return SourceDocument(
            id=self.id,
            title=self.title,
            url=self.url,
            domain=self.domain,
            author=self.author,
            publisher=self.publisher,
            published_date=p_date,
            retrieval_timestamp=r_time,
            content_snippet=self.content_snippet,
            content_sha256=self.content_sha256,
            source_reliability_score=self.source_reliability_score,
            full_text_storage_uri=self.full_text_storage_uri,
            is_simulated=self.is_simulated,
        )

