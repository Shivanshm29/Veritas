"""
Asset management API endpoints for Veritas Phase 1: Data Ingestion & Evidence Asset Management.

Provides secure multipart file upload, metadata retrieval, bounded streaming,
content validation, and storage coordination.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import (
    InvalidIdentifierError,
    ResourceNotFoundError,
    VeritasException,
)
from backend.app.core.logging import logger
from backend.app.db.models.asset import EvidenceAssetRecord
from backend.app.db.repositories.asset import AssetRepository
from backend.app.db.session import get_db
from backend.app.services.storage import StorageService, get_storage_service
from contracts.schemas.models import (
    EvidenceAsset,
    EntityPrefix,
    AssetStatus,
    C2PAStatus,
    validate_prefixed_id,
)

router = APIRouter(prefix="/assets", tags=["Evidence Assets"])


@router.post(
    "/upload",
    response_model=EvidenceAsset,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest an evidence asset",
    description=(
        "Streams and stores an evidence file, computes its SHA-256 digest, enforces size bounds, "
        "validates file signatures against allowed MIME types, and creates an EvidenceAsset record."
    ),
)
async def upload_asset(
    file: UploadFile = File(..., description="Multipart binary asset file"),
    investigation_id: Optional[str] = Form(
        None, description="Optional investigation ID (inv_<uuid4>). Auto-generated if omitted."
    ),
    source_url: Optional[str] = Form(None, description="Optional origin URL of the media"),
    source_platform: Optional[str] = Form(None, description="Optional platform name (e.g., twitter, youtube)"),
    captured_at: Optional[datetime] = Form(None, description="Timestamp when evidence was captured"),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
) -> EvidenceAsset:
    # 1. Validate or generate investigation_id
    if investigation_id:
        try:
            validate_prefixed_id(investigation_id, EntityPrefix.INVESTIGATION)
        except ValueError:
            raise InvalidIdentifierError(
                identifier=investigation_id,
                expected_format="inv_<uuid4>",
            )
    else:
        investigation_id = f"inv_{uuid.uuid4()}"

    # 2. Generate new asset identifier
    asset_id = f"ast_{uuid.uuid4()}"

    # 3. Stream upload into durable storage
    upload_result = await storage.save_upload(
        upload_file=file,
        asset_id=asset_id,
        max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
    )

    # 4. Construct ORM model
    now = datetime.now(timezone.utc)
    record = EvidenceAssetRecord(
        id=asset_id,
        investigation_id=investigation_id,
        original_filename=upload_result.original_filename,
        file_size_bytes=upload_result.file_size_bytes,
        mime_type=upload_result.mime_type,
        sha256_hash=upload_result.sha256_hash,
        storage_uri=upload_result.storage_uri,
        source_url=source_url,
        source_platform=source_platform,
        captured_at=captured_at,
        c2pa_manifest_present=False,
        c2pa_status=C2PAStatus.ABSENT.value,
        status=AssetStatus.STORED.value,
        quarantine_reason=None,
        uploaded_at=now,
    )

    # 5. Persist to database with storage rollback on failure
    repo = AssetRepository(db)
    try:
        repo.create(record)
    except Exception as exc:
        logger.error(f"Database commit failed for asset {asset_id}. Rolling back storage file: {exc}")
        storage.delete(upload_result.storage_uri)
        raise VeritasException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Asset Ingestion Failed",
            detail="Failed to record evidence asset metadata in database. Storage write was rolled back.",
            code="INGESTION_PERSISTENCE_ERROR",
        )

    logger.info(f"Ingested evidence asset {asset_id} under investigation {investigation_id}")
    return record.to_schema()


@router.get(
    "/{asset_id}",
    response_model=EvidenceAsset,
    status_code=status.HTTP_200_OK,
    summary="Retrieve evidence asset metadata",
    description="Fetches an evidence asset by its unique prefixed identifier (ast_<uuid4>).",
)
async def get_asset(
    asset_id: str,
    db: Session = Depends(get_db),
) -> EvidenceAsset:
    # 1. Validate identifier syntax
    try:
        validate_prefixed_id(asset_id, EntityPrefix.EVIDENCE_ASSET)
    except ValueError:
        raise InvalidIdentifierError(
            identifier=asset_id,
            expected_format="ast_<uuid4>",
        )

    # 2. Query repository
    repo = AssetRepository(db)
    record = repo.get_by_id(asset_id)
    if not record:
        raise ResourceNotFoundError("EvidenceAsset", asset_id)

    return record.to_schema()


@router.get(
    "",
    response_model=List[EvidenceAsset],
    status_code=status.HTTP_200_OK,
    summary="List evidence assets",
    description="Lists evidence assets, optionally filtered by investigation ID.",
)
async def list_assets(
    investigation_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> List[EvidenceAsset]:
    repo = AssetRepository(db)
    if investigation_id:
        try:
            validate_prefixed_id(investigation_id, EntityPrefix.INVESTIGATION)
        except ValueError:
            raise InvalidIdentifierError(
                identifier=investigation_id,
                expected_format="inv_<uuid4>",
            )
        records = repo.list_by_investigation(investigation_id, limit=limit, offset=offset)
    else:
        records = db.query(EvidenceAssetRecord).order_by(EvidenceAssetRecord.uploaded_at.desc()).offset(offset).limit(limit).all()

    return [r.to_schema() for r in records]
