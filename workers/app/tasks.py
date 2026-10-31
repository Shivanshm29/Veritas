"""
Task interfaces and demonstration handlers for Veritas worker scaffold.
"""

import hashlib
import json
import time
from typing import Any, Dict
from workers.app.config import TaskResult, TaskStatus
from backend.app.core.logging import logger


def echo_probe_task(task_id: str, payload: Dict[str, Any]) -> TaskResult:
    """
    Harmless demonstration task: echoes payload with SHA-256 checksum and latency telemetry.
    Does not perform AI inference or media processing.
    """
    start_time = time.perf_counter()
    logger.info(f"[Worker] Executing probe task '{task_id}' with keys: {list(payload.keys())}")

    try:
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload_hash = hashlib.sha256(serialized).hexdigest()

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return TaskResult(
            task_id=task_id,
            task_name="echo_probe_task",
            status=TaskStatus.SUCCESS,
            result_data={
                "echo": payload,
                "payload_sha256": payload_hash,
                "processed_items_count": len(payload),
            },
            duration_ms=round(duration_ms, 2),
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"[Worker] Task '{task_id}' failed: {exc}")
        return TaskResult(
            task_id=task_id,
            task_name="echo_probe_task",
            status=TaskStatus.FAILURE,
            error_message=str(exc),
            duration_ms=round(duration_ms, 2),
        )


def failing_probe_task(task_id: str) -> TaskResult:
    """
    Demonstration task intentionally raising an exception to verify error handling.
    """
    start_time = time.perf_counter()
    logger.info(f"[Worker] Executing failing probe task '{task_id}' (intentional failure test)")

    try:
        raise ValueError("Simulated operational failure in worker pipeline.")
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        return TaskResult(
            task_id=task_id,
            task_name="failing_probe_task",
            status=TaskStatus.FAILURE,
            error_message=str(exc),
            duration_ms=round(duration_ms, 2),
        )

