"""
Veritas Backend Application Entry Point.

FastAPI application factory, CORS configuration, exception handlers, and routing.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.errors import (
    VeritasException,
    PramaanException,
    http_exception_handler,
    veritas_exception_handler,
    pramaan_exception_handler,
    validation_exception_handler,
)
from backend.app.core.logging import logger
from backend.app.schemas.health import BasicHealthResponse
from backend.app.services.health import get_basic_health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle events: startup and shutdown."""
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]"
    )
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


def create_app() -> FastAPI:
    """Application factory configuring middleware, exception handlers, and routes."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Veritas — Provenance, Reliability & Authenticity Monitoring and Analysis Network.\n\n"
            "Person 1 Backend: Data Ingestion, Claim Intelligence, and Retrieval Verification."
        ),
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    cors_origins = (
        settings.CORS_ORIGINS
        if isinstance(settings.CORS_ORIGINS, list)
        else [settings.CORS_ORIGINS]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register Exception Handlers (RFC 9457 Problem Details)
    app.add_exception_handler(VeritasException, veritas_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Root Health Probe
    @app.get(
        "/health",
        response_model=BasicHealthResponse,
        status_code=status.HTTP_200_OK,
        tags=["Health"],
        summary="Root Liveness Probe",
        description="Quick lightweight check for container orchestrators and load balancers.",
    )
    async def root_health() -> BasicHealthResponse:
        return get_basic_health()

    # Mount Versioned API Routes
    app.include_router(api_router)

    return app


app = create_app()

