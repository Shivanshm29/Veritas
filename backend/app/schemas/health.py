"""
Health & Diagnostic Schemas for Veritas.
"""

from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class BasicHealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = Field(..., example="healthy")
    service: str = Field(..., example="Veritas Core Backend")
    version: str = Field(..., example="0.1.0")
    environment: str = Field(..., example="development")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DetailedHealthResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str = Field(..., example="healthy")
    service: str = Field(..., example="Veritas Core Backend")
    version: str = Field(..., example="0.1.0")
    environment: str = Field(..., example="development")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dependencies: Dict[str, Any] = Field(
        ...,
        description="Health states of probed dependencies (database, redis, storage)",
    )
    system: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime telemetry (Python version, platform)",
    )

