"""
Error definitions and exception handlers for Veritas.

Maps application exceptions to RFC 9457 Problem Details responses.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.schemas.problem import ProblemDetail, InvalidParam


class VeritasException(Exception):
    """Base application exception for Veritas."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        title: str = "Internal Server Error",
        detail: str = "An unexpected error occurred.",
        code: str = "INTERNAL_ERROR",
        error_type: str = "https://veritas.org/errors/INTERNAL_ERROR",
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.code = code
        self.error_type = error_type
        super().__init__(detail)


# Backward-compatibility alias
PramaanException = VeritasException


class ResourceNotFoundError(VeritasException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Resource Not Found",
            detail=f"{resource_type} with id '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            error_type="https://veritas.org/errors/RESOURCE_NOT_FOUND",
        )


class ServiceUnavailableError(VeritasException):
    def __init__(self, service_name: str, reason: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service Unavailable",
            detail=f"Downstream service '{service_name}' is currently unavailable: {reason}",
            code="SERVICE_UNAVAILABLE",
            error_type="https://veritas.org/errors/SERVICE_UNAVAILABLE",
        )


class PayloadTooLargeError(VeritasException):
    def __init__(self, max_size_bytes: int, actual_size_bytes: int = None):
        detail = f"File size exceeds maximum permitted limit of {max_size_bytes} bytes."
        if actual_size_bytes is not None:
            detail += f" Uploaded file size is {actual_size_bytes} bytes."
        super().__init__(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            title="Payload Too Large",
            detail=detail,
            code="PAYLOAD_TOO_LARGE",
            error_type="https://veritas.org/errors/PAYLOAD_TOO_LARGE",
        )


class InvalidMimeTypeError(VeritasException):
    def __init__(self, mime_type: str, allowed_types: List[str] = None):
        detail = f"Unsupported MIME type '{mime_type}'."
        if allowed_types:
            detail += f" Supported formats: {', '.join(allowed_types)}."
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Invalid MIME Type",
            detail=detail,
            code="INVALID_MIME_TYPE",
            error_type="https://veritas.org/errors/INVALID_MIME_TYPE",
        )


class EmptyFileError(VeritasException):
    def __init__(self, detail: str = "Uploaded file is empty (0 bytes)."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Empty File",
            detail=detail,
            code="EMPTY_FILE",
            error_type="https://veritas.org/errors/EMPTY_FILE",
        )


class InvalidIdentifierError(VeritasException):
    def __init__(self, identifier: str, expected_format: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            title="Invalid Identifier",
            detail=f"Identifier '{identifier}' is invalid. Expected format: '{expected_format}'.",
            code="INVALID_IDENTIFIER",
            error_type="https://veritas.org/errors/INVALID_IDENTIFIER",
        )


class InvalidAssetError(VeritasException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Invalid Asset",
            detail=detail,
            code="INVALID_ASSET",
            error_type="https://veritas.org/errors/INVALID_ASSET",
        )


async def veritas_exception_handler(request: Request, exc: VeritasException) -> JSONResponse:
    """Handles domain-specific VeritasException."""
    problem = ProblemDetail(
        type=exc.error_type,
        title=exc.title,
        status=exc.status_code,
        detail=exc.detail,
        instance=str(request.url.path),
        code=exc.code,
        timestamp=datetime.now(timezone.utc),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(mode="json"),
        headers={"Content-Type": "application/problem+json"},
    )


# Backward-compatibility alias
pramaan_exception_handler = veritas_exception_handler


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI/Pydantic validation errors."""
    invalid_params: List[InvalidParam] = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        invalid_params.append(InvalidParam(name=loc, reason=msg))

    problem = ProblemDetail(
        type="https://veritas.org/errors/VALIDATION_ERROR",
        title="Request Validation Error",
        status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="One or more fields in the request payload failed schema validation.",
        instance=str(request.url.path),
        code="VALIDATION_ERROR",
        invalid_params=invalid_params,
        timestamp=datetime.now(timezone.utc),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=problem.model_dump(mode="json"),
        headers={"Content-Type": "application/problem+json"},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard HTTPExceptions."""
    problem = ProblemDetail(
        type=f"https://veritas.org/errors/HTTP_{exc.status_code}",
        title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
        status=exc.status_code,
        detail=str(exc.detail),
        instance=str(request.url.path),
        code=f"HTTP_{exc.status_code}",
        timestamp=datetime.now(timezone.utc),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(mode="json"),
        headers={"Content-Type": "application/problem+json"},
    )
