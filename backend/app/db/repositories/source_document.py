"""
SourceDocument repository for database interactions in Veritas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.source_document import SourceDocumentRecord


class SourceDocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, doc: SourceDocumentRecord, commit: bool = True) -> SourceDocumentRecord:
        """Persists a new SourceDocument record."""
        self.db.add(doc)
        if commit:
            self.db.commit()
            self.db.refresh(doc)
        return doc

    def create_batch(
        self, docs: List[SourceDocumentRecord], commit: bool = True
    ) -> List[SourceDocumentRecord]:
        """Persists a batch of SourceDocument records in a transaction."""
        if not docs:
            return []
        self.db.add_all(docs)
        if commit:
            self.db.commit()
            for d in docs:
                self.db.refresh(d)
        else:
            self.db.flush()
        return docs

    def get_by_id(self, doc_id: str) -> Optional[SourceDocumentRecord]:
        """Retrieves a SourceDocument record by prefixed ID (doc_...)."""
        return self.db.query(SourceDocumentRecord).filter(SourceDocumentRecord.id == doc_id).first()

    def get_by_hash(self, content_sha256: str) -> Optional[SourceDocumentRecord]:
        """Retrieves a SourceDocument record by content SHA-256 hash."""
        return (
            self.db.query(SourceDocumentRecord)
            .filter(SourceDocumentRecord.content_sha256 == content_sha256)
            .first()
        )

    def list_by_domain(
        self, domain: str, limit: int = 50, offset: int = 0
    ) -> List[SourceDocumentRecord]:
        """Lists source documents belonging to a domain."""
        return (
            self.db.query(SourceDocumentRecord)
            .filter(SourceDocumentRecord.domain == domain)
            .order_by(SourceDocumentRecord.retrieval_timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list_all(self, limit: int = 50, offset: int = 0) -> List[SourceDocumentRecord]:
        """Lists source documents ordered by retrieval timestamp."""
        return (
            self.db.query(SourceDocumentRecord)
            .order_by(SourceDocumentRecord.retrieval_timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete(self, doc_id: str) -> bool:
        """Deletes a SourceDocument record by ID."""
        record = self.get_by_id(doc_id)
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False

