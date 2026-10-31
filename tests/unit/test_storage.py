"""
Unit tests for LocalFileStorageService.
"""

import io
import os
import tempfile
from pathlib import Path
import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from backend.app.core.errors import PayloadTooLargeError, EmptyFileError, InvalidAssetError
from backend.app.services.storage import LocalFileStorageService


def make_upload_file(filename: str, content: bytes, content_type: str = "image/jpeg") -> UploadFile:
    file_obj = io.BytesIO(content)
    headers = Headers({"content-type": content_type})
    return UploadFile(file=file_obj, filename=filename, headers=headers)


@pytest.fixture
def temp_storage():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = LocalFileStorageService(base_dir=tmp_dir)
        yield service, Path(tmp_dir) / "assets"


@pytest.mark.asyncio
async def test_save_valid_jpeg(temp_storage):
    service, storage_dir = temp_storage
    jpeg_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100
    upload = make_upload_file("sample.jpg", jpeg_data, "image/jpeg")

    res = await service.save_upload(upload, asset_id="ast_11111111-2222-4333-8444-555555555555")

    assert res.file_size_bytes == len(jpeg_data)
    assert res.mime_type == "image/jpeg"
    assert res.original_filename == "sample.jpg"
    assert res.file_path.exists()
    assert res.storage_uri.startswith("file://")
    assert res.file_path.read_bytes() == jpeg_data


@pytest.mark.asyncio
async def test_save_empty_file_fails(temp_storage):
    service, storage_dir = temp_storage
    upload = make_upload_file("empty.jpg", b"", "image/jpeg")

    with pytest.raises(EmptyFileError):
        await service.save_upload(upload, asset_id="ast_11111111-2222-4333-8444-555555555555")

    # Ensure no leftover files
    assert list(storage_dir.glob("*")) == []


@pytest.mark.asyncio
async def test_save_oversized_file_fails(temp_storage):
    service, storage_dir = temp_storage
    jpeg_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 2000
    upload = make_upload_file("big.jpg", jpeg_data, "image/jpeg")

    # Set strict 500-byte limit
    with pytest.raises(PayloadTooLargeError) as exc_info:
        await service.save_upload(
            upload,
            asset_id="ast_11111111-2222-4333-8444-555555555555",
            max_size_bytes=500,
        )

    assert "exceeds maximum permitted limit of 500" in str(exc_info.value.detail)
    # Ensure no temp file leaked
    assert list(storage_dir.glob(".tmp*")) == []
    assert list(storage_dir.glob("ast_*")) == []


@pytest.mark.asyncio
async def test_path_traversal_sanitized(temp_storage):
    service, storage_dir = temp_storage
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 50
    upload = make_upload_file("../../../secret.png", png_data, "image/png")

    res = await service.save_upload(upload, asset_id="ast_11111111-2222-4333-8444-555555555555")

    assert res.original_filename == "secret.png"
    assert res.file_path.name.endswith("_secret.png")
    assert res.file_path.parent == storage_dir


@pytest.mark.asyncio
async def test_path_traversal_windows_style_sanitized(temp_storage):
    service, storage_dir = temp_storage
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 50
    upload = make_upload_file(r"..\..\windows\system32\secret.png", png_data, "image/png")

    res = await service.save_upload(upload, asset_id="ast_22222222-3333-4444-8555-666666666666")

    assert res.original_filename == "secret.png"
    assert res.file_path.name.endswith("_secret.png")
    assert res.file_path.parent == storage_dir


@pytest.mark.asyncio
async def test_storage_defense_in_depth_confinement(temp_storage, monkeypatch):
    """Verifies that storage layer traps path traversal even if sanitizer is bypassed."""
    service, storage_dir = temp_storage
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 50
    upload = make_upload_file("harmless.png", png_data, "image/png")

    # Simulate hypothetical sanitizer failure attempting directory escape
    monkeypatch.setattr("backend.app.services.storage.sanitize_filename", lambda _: "../../../escaped.png")

    with pytest.raises(InvalidAssetError, match="Storage path traversal detected"):
        await service.save_upload(upload, asset_id="ast_33333333-4444-5555-8666-777777777777")


@pytest.mark.asyncio
async def test_delete_stored_file(temp_storage):
    service, storage_dir = temp_storage
    jpeg_data = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 10
    upload = make_upload_file("delete_me.jpg", jpeg_data, "image/jpeg")

    res = await service.save_upload(upload, asset_id="ast_11111111-2222-4333-8444-555555555555")
    assert res.file_path.exists()

    deleted = service.delete(res.storage_uri)
    assert deleted is True
    assert not res.file_path.exists()


@pytest.mark.asyncio
async def test_save_upload_cleans_up_on_task_cancellation(temp_storage):
    """Verifies that asyncio.CancelledError during chunk streaming unlinks temp files."""
    import asyncio
    service, storage_dir = temp_storage

    class CancellingUploadFile:
        def __init__(self):
            self.filename = "cancel.jpg"
            self.content_type = "image/jpeg"
            self.chunks_read = 0

        async def read(self, chunk_size):
            self.chunks_read += 1
            if self.chunks_read == 1:
                return b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100
            raise asyncio.CancelledError("Client disconnected")

    upload = CancellingUploadFile()
    with pytest.raises(asyncio.CancelledError):
        await service.save_upload(upload, asset_id="ast_11111111-2222-4333-8444-555555555555")

    assert list(storage_dir.glob(".tmp*")) == []
    assert list(storage_dir.glob("ast_*")) == []


@pytest.mark.asyncio
async def test_save_upload_cancellation_preserves_exception_when_temp_cleanup_fails(temp_storage):
    """
    Verifies that if unlinking a temporary file fails (e.g. OS file lock or permission error),
    the original asyncio.CancelledError is still strictly preserved and re-raised.
    """
    import asyncio
    from unittest.mock import patch
    service, storage_dir = temp_storage

    class CancellingUploadFile:
        def __init__(self):
            self.filename = "cancel_lock.jpg"
            self.content_type = "image/jpeg"
            self.chunks_read = 0

        async def read(self, chunk_size):
            self.chunks_read += 1
            if self.chunks_read == 1:
                return b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"\x00" * 100
            raise asyncio.CancelledError("Client disconnected")

    upload = CancellingUploadFile()
    with patch("pathlib.Path.unlink", side_effect=OSError("File lock held by antivirus")):
        with pytest.raises(asyncio.CancelledError):
            await service.save_upload(upload, asset_id="ast_22222222-3333-4444-8555-666666666666")
