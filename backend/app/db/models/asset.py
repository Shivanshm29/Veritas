"""
SQLAlchemy ORM models for Evidence Assets in Veritas.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime
from backend.app.db.base import Base
from contracts.schemas.models import EvidenceAsset, AssetStatus, C2PAStatus


class EvidenceAssetRecord(Base):
    """ORM representation of an evidence asset."""
    __tablename__ = "evidence_assets"

    id = Column(String(64), primary_key=True, index=True)
    investigation_id = Column(String(64), nullable=False, index=True)
    original_filename = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    storage_uri = Column(String(1024), nullable=False)
    source_url = Column(String(2048), nullable=True)
    source_platform = Column(String(100), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    c2pa_manifest_present = Column(Boolean, default=False, nullable=False)
    c2pa_status = Column(String(50), default=C2PAStatus.ABSENT.value, nullable=False)
    status = Column(String(50), default=AssetStatus.STORED.value, nullable=False)
    quarantine_reason = Column(String(1000), nullable=True)
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_schema(self) -> EvidenceAsset:
        """Converts the ORM record to the canonical EvidenceAsset Pydantic model."""
        up_at = self.uploaded_at
        if up_at is not None and up_at.tzinfo is None:
            up_at = up_at.replace(tzinfo=timezone.utc)

        cap_at = self.captured_at
        if cap_at is not None and cap_at.tzinfo is None:
            cap_at = cap_at.replace(tzinfo=timezone.utc)

        return EvidenceAsset(
            id=self.id,
            investigation_id=self.investigation_id,
            original_filename=self.original_filename,
            file_size_bytes=self.file_size_bytes,
            mime_type=self.mime_type,
            sha256_hash=self.sha256_hash,
            storage_uri=self.storage_uri,
            source_url=self.source_url,
            source_platform=self.source_platform,
            captured_at=cap_at,
            c2pa_manifest_present=self.c2pa_manifest_present,
            c2pa_status=C2PAStatus(self.c2pa_status) if isinstance(self.c2pa_status, str) else self.c2pa_status,
            status=AssetStatus(self.status) if isinstance(self.status, str) else self.status,
            quarantine_reason=self.quarantine_reason,
            uploaded_at=up_at,
        )
