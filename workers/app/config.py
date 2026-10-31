"""
Worker configuration and task execution models for PRAMAAN.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"


class TaskResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    task_id: str
    task_name: str
    status: TaskStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: float = Field(..., ge=0.0)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

