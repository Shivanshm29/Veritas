"""
RFC 9457 / RFC 7807 Problem Details Schema for Veritas.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InvalidParam(BaseModel):
    name: str
    reason: str


class ProblemDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(default="https://veritas.org/errors/INTERNAL_ERROR")
    title: str = Field(..., description="Short, human-readable summary of the problem type")
    status: int = Field(..., description="HTTP status code")
    detail: Optional[str] = Field(None, description="Human-readable explanation specific to this occurrence")
    instance: Optional[str] = Field(None, description="URI reference that identifies the specific occurrence")
    code: Optional[str] = Field(None, description="Machine-readable application error code")
    invalid_params: Optional[List[InvalidParam]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

