"""
Integration tests verifying transactional coordination between storage and database.
Ensures storage files are rolled back (cleaned up) when database commits fail.
"""

import io
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi import status

JPEG_HEADER = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 64


def test_storage_rollback_when_db_commit_fails(client):
    """
    Simulates a database failure during asset creation.
    Verifies that the storage file is deleted and does not leak as an orphan file.
    """
    from backend.app.services.storage import get_storage_service

    storage = get_storage_service()
    deleted_uris = []

    original_delete = storage.delete

    def spy_delete(uri: str) -> bool:
        deleted_uris.append(uri)
        return original_delete(uri)

    with patch.object(storage, "delete", side_effect=spy_delete):
        with patch("backend.app.db.repositories.asset.AssetRepository.create", side_effect=RuntimeError("Simulated DB Disk Crash")):
            file_payload = ("rollback_test.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")
            response = client.post(
                "/api/v1/assets/upload",
                files={"file": file_payload},
            )

            # Ingestion endpoint handles exception and returns 500 Problem Details
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            problem = response.json()
            assert problem["code"] == "INGESTION_PERSISTENCE_ERROR"

            # Assert that storage.delete was invoked on the created file
            assert len(deleted_uris) == 1
            deleted_uri = deleted_uris[0]
            assert deleted_uri.startswith("file://")

            # Assert that the file no longer exists on disk
            path_part = deleted_uri[len("file://"):]
            if len(path_part) > 2 and path_part[0] == "/" and path_part[2] == ":":
                path_part = path_part[1:]
            assert not Path(path_part).exists(), "Orphaned storage file was not rolled back!"


def test_storage_rollback_handles_deletion_failure_gracefully(client):
    """
    Simulates a database failure during asset creation AND a subsequent failure
    during storage deletion (e.g. file lock or permissions error).
    Verifies that the endpoint safely returns HTTP 500 INGESTION_PERSISTENCE_ERROR,
    does not crash with an unhandled exception, and reports that cleanup was attempted.
    """
    from backend.app.services.storage import get_storage_service

    storage = get_storage_service()

    with patch.object(storage, "delete", side_effect=OSError("Permission denied or file locked by OS")):
        with patch("backend.app.db.repositories.asset.AssetRepository.create", side_effect=RuntimeError("Simulated DB Crash")):
            file_payload = ("rollback_fail_test.jpg", io.BytesIO(JPEG_HEADER), "image/jpeg")
            response = client.post(
                "/api/v1/assets/upload",
                files={"file": file_payload},
            )

            # Ingestion endpoint safely traps cleanup error and returns 500 Problem Details
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            problem = response.json()
            assert problem["code"] == "INGESTION_PERSISTENCE_ERROR"
            assert "could not be unlinked" in problem["detail"]
