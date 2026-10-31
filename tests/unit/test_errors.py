"""
Unit tests for domain exceptions and RFC 9457 Problem Details schemas.
"""

from backend.app.core.errors import (
    VeritasException,
    PramaanException,
    ResourceNotFoundError,
    ServiceUnavailableError,
    PayloadTooLargeError,
    InvalidMimeTypeError,
    EmptyFileError,
    InvalidIdentifierError,
    InvalidAssetError,
)
from backend.app.schemas.problem import ProblemDetail


def test_veritas_exception_defaults():
    """Verifies default exception attributes for VeritasException and backward alias."""
    exc = VeritasException()
    assert exc.status_code == 500
    assert exc.code == "INTERNAL_ERROR"
    assert exc.title == "Internal Server Error"
    
    # Backward alias
    alias_exc = PramaanException()
    assert isinstance(alias_exc, VeritasException)


def test_resource_not_found_error():
    """Verifies ResourceNotFoundError creates 404 Problem Details attributes."""
    exc = ResourceNotFoundError("EvidenceAsset", "ast_123")
    assert exc.status_code == 404
    assert exc.code == "RESOURCE_NOT_FOUND"
    assert "ast_123" in exc.detail


def test_service_unavailable_error():
    """Verifies ServiceUnavailableError creates 503 attributes."""
    exc = ServiceUnavailableError("Redis", "Connection refused on port 6379")
    assert exc.status_code == 503
    assert exc.code == "SERVICE_UNAVAILABLE"
    assert "Redis" in exc.detail


def test_problem_detail_serialization():
    """Verifies ProblemDetail serializes to dict matching RFC 9457."""
    prob = ProblemDetail(
        title="Bad Input",
        status=400,
        detail="Missing required parameter.",
        code="INVALID_ARGUMENT",
    )
    dumped = prob.model_dump(mode="json")
    assert dumped["status"] == 400
    assert dumped["title"] == "Bad Input"
    assert "timestamp" in dumped


def test_phase1_domain_errors():
    """Verifies domain errors introduced in Phase 1 create proper RFC 9457 attributes."""
    large_exc = PayloadTooLargeError(500, 1000)
    assert large_exc.status_code == 413
    assert large_exc.code == "PAYLOAD_TOO_LARGE"

    mime_exc = InvalidMimeTypeError("application/pdf", ["image/jpeg"])
    assert mime_exc.status_code == 400
    assert mime_exc.code == "INVALID_MIME_TYPE"

    empty_exc = EmptyFileError()
    assert empty_exc.status_code == 400
    assert empty_exc.code == "EMPTY_FILE"

    id_exc = InvalidIdentifierError("bad_id", "ast_<uuid4>")
    assert id_exc.status_code == 422
    assert id_exc.code == "INVALID_IDENTIFIER"

    asset_exc = InvalidAssetError("Spoofed content header.")
    assert asset_exc.status_code == 400
    assert asset_exc.code == "INVALID_ASSET"

