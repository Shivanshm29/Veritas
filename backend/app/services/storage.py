"""
Storage abstraction and local file storage service for Veritas evidence assets.

Enforces bounded chunk streaming, concurrent SHA-256 calculation, atomic writes,
storage rollback on failure, and path traversal defense.
"""

import hashlib
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator, Optional, Union
from fastapi import UploadFile

from backend.app.core.config import settings
from backend.app.core.errors import PayloadTooLargeError, EmptyFileError, InvalidAssetError
from backend.app.core.logging import logger
from backend.app.services.validation import detect_and_validate_mime, sanitize_filename


@dataclass
class StorageUploadResult:
    storage_uri: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    original_filename: str
    file_path: Path


class StorageService(ABC):
    @abstractmethod
    async def save_upload(
        self,
        upload_file: UploadFile,
        asset_id: str,
        max_size_bytes: Optional[int] = None,
        declared_mime: Optional[str] = None,
    ) -> StorageUploadResult:
        """Stream an uploaded file to durable storage."""
        pass

    @abstractmethod
    def delete(self, storage_uri: str) -> bool:
        """Deletes a stored file by its URI."""
        pass


class LocalFileStorageService(StorageService):
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.STORAGE_BASE_DIR) / "assets"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(
        self,
        upload_file: UploadFile,
        asset_id: str,
        max_size_bytes: Optional[int] = None,
        declared_mime: Optional[str] = None,
    ) -> StorageUploadResult:
        limit = max_size_bytes if max_size_bytes is not None else settings.MAX_UPLOAD_SIZE_BYTES
        raw_filename = upload_file.filename or "asset.bin"
        safe_filename = sanitize_filename(raw_filename)

        # Temporary destination for atomic streaming write
        temp_filename = f".tmp_{asset_id}_{uuid.uuid4().hex}"
        temp_path = self.base_dir / temp_filename
        final_filename = f"{asset_id}_{safe_filename}"
        final_path = self.base_dir / final_filename

        # Defense-in-depth: Ensure paths strictly resolve within base_dir
        resolved_base = self.base_dir.resolve()
        resolved_temp = temp_path.resolve()
        resolved_final = final_path.resolve()

        if not (resolved_final.is_relative_to(resolved_base) and resolved_temp.is_relative_to(resolved_base)):
            raise InvalidAssetError(f"Storage path traversal detected for asset '{asset_id}'.")

        hasher = hashlib.sha256()
        total_bytes = 0
        header_bytes = b""
        chunk_size = 64 * 1024  # 64 KB streaming buffer

        try:
            with open(temp_path, "wb") as f_out:
                while True:
                    chunk = await upload_file.read(chunk_size)
                    if not chunk:
                        break

                    total_bytes += len(chunk)
                    if total_bytes > limit:
                        raise PayloadTooLargeError(
                            max_size_bytes=limit,
                            actual_size_bytes=total_bytes,
                        )

                    # Capture header for magic-byte MIME validation
                    if len(header_bytes) < 512:
                        needed = 512 - len(header_bytes)
                        header_bytes += chunk[:needed]

                    hasher.update(chunk)
                    f_out.write(chunk)

            if total_bytes == 0:
                raise EmptyFileError(f"Uploaded file '{raw_filename}' contains 0 bytes.")

            # Validate header bytes against MIME allowlist
            detected_mime = detect_and_validate_mime(
                header_bytes=header_bytes,
                original_filename=safe_filename,
                declared_mime=declared_mime or upload_file.content_type,
            )

            # Atomic rename from temporary file to final storage destination
            if final_path.exists():
                final_path.unlink()
            os.replace(temp_path, final_path)

            sha256_hex = hasher.hexdigest()
            # Canonical URI format: file:///path/to/asset (or file://path)
            abs_path_str = str(final_path.resolve()).replace("\\", "/")
            if not abs_path_str.startswith("/"):
                abs_path_str = "/" + abs_path_str
            storage_uri = f"file://{abs_path_str}"

            logger.info(
                f"Successfully stored asset {asset_id} at {storage_uri} "
                f"({total_bytes} bytes, MIME: {detected_mime})"
            )

            return StorageUploadResult(
                storage_uri=storage_uri,
                sha256_hash=sha256_hex,
                file_size_bytes=total_bytes,
                mime_type=detected_mime,
                original_filename=safe_filename,
                file_path=final_path,
            )

        except BaseException:
            # Ensure temporary file is destroyed on error, abort, or task cancellation
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception as err:
                logger.warning(f"Failed to remove temporary file {temp_path}: {err}")
            raise

    def delete(self, storage_uri: str) -> bool:
        """Deletes the asset file referenced by storage_uri."""
        if not storage_uri.startswith("file://"):
            logger.warning(f"Cannot delete non-file URI: {storage_uri}")
            return False

        path_part = storage_uri[len("file://"):]
        # On Windows, path_part might be /C:/...
        if len(path_part) > 2 and path_part[0] == "/" and path_part[2] == ":":
            path_part = path_part[1:]

        file_path = Path(path_part)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted storage file at {file_path}")
                return True
            except OSError as err:
                logger.error(f"Error deleting storage file at {file_path}: {err}")
                return False
        return False


# Singleton default storage provider
_default_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _default_storage_service
    if _default_storage_service is None:
        _default_storage_service = LocalFileStorageService()
    return _default_storage_service
