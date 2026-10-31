"""
Diagnostic & Health Check Endpoints for API v1.
"""

from fastapi import APIRouter, status
from backend.app.schemas.health import DetailedHealthResponse
from backend.app.services.health import get_detailed_health

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Detailed Dependency Health Probe",
    description="Actively checks database, cache, and object storage connectivity.",
)
async def api_health() -> DetailedHealthResponse:
    return get_detailed_health()

