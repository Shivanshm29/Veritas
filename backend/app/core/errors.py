"""
Error definitions and exception handlers for PRAMAAN.

Maps application exceptions to RFC 9457 Problem Details responses.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.schemas.problem import ProblemDetail, InvalidParam


class PramaanException(Exception):
    """Base application exception for PRAMAAN."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        title: str = "Internal Server Error",
        detail: str = "An unexpected error occurred.",
        code: str = "INTERNAL_ERROR",
        error_type: str = "https://pramaan.org/errors/INTERNAL_ERROR",
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.code = code
        self.error_type = error_type
        super().__init__(detail)


class ResourceNotFoundError(PramaanException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Resource Not Found",
            detail=f"{resource_type} with id '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            error_type="https://pramaan.org/errors/RESOURCE_NOT_FOUND",
        )


class ServiceUnavailableError(PramaanException):
    def __init__(self, service_name: str, reason: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            title="Service Unavailable",
            detail=f"Downstream service '{service_name}' is currently unavailable: {reason}",
            code="SERVICE_UNAVAILABLE",
            error_type="https://pramaan.org/errors/SERVICE_UNAVAILABLE",
        )


async def pramaan_exception_handler(request: Request, exc: PramaanException) -> JSONResponse:
    """Handles domain-specific PramaanException."""
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


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI/Pydantic validation errors."""
    invalid_params: List[InvalidParam] = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        invalid_params.append(InvalidParam(name=loc, reason=msg))

    problem = ProblemDetail(
        type="https://pramaan.org/errors/VALIDATION_ERROR",
        title="Request Validation Error",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="One or more fields in the request payload failed schema validation.",
        instance=str(request.url.path),
        code="VALIDATION_ERROR",
        invalid_params=invalid_params,
        timestamp=datetime.now(timezone.utc),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem.model_dump(mode="json"),
        headers={"Content-Type": "application/problem+json"},
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard HTTPExceptions."""
    problem = ProblemDetail(
        type=f"https://pramaan.org/errors/HTTP_{exc.status_code}",
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

