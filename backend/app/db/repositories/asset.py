"""
Asset repository for database interactions in Veritas.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.asset import EvidenceAssetRecord


class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, asset: EvidenceAssetRecord) -> EvidenceAssetRecord:
        """Persists a new evidence asset record."""
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def get_by_id(self, asset_id: str) -> Optional[EvidenceAssetRecord]:
        """Retrieves an evidence asset record by its prefixed id (ast_...)."""
        return self.db.query(EvidenceAssetRecord).filter(EvidenceAssetRecord.id == asset_id).first()

    def get_by_hash(self, sha256_hash: str) -> Optional[EvidenceAssetRecord]:
        """Retrieves an evidence asset record by its SHA-256 hash."""
        return self.db.query(EvidenceAssetRecord).filter(EvidenceAssetRecord.sha256_hash == sha256_hash).first()

    def list_by_investigation(
        self, investigation_id: str, limit: int = 50, offset: int = 0
    ) -> List[EvidenceAssetRecord]:
        """Lists assets belonging to an investigation."""
        return (
            self.db.query(EvidenceAssetRecord)
            .filter(EvidenceAssetRecord.investigation_id == investigation_id)
            .order_by(EvidenceAssetRecord.uploaded_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete(self, asset_id: str) -> bool:
        """Deletes an asset record by id."""
        record = self.get_by_id(asset_id)
        if record:
            self.db.delete(record)
            self.db.commit()
            return True
        return False
