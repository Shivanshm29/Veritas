"""
Task Runner abstraction enabling decoupled testing without external Redis daemon.
"""

import asyncio
from typing import Any, Callable, Dict, Optional
from workers.app.config import TaskResult, TaskStatus
from backend.app.core.logging import logger


class InMemoryTaskRunner:
    """
    Decoupled task execution runner.
    Executes worker tasks asynchronously in-process, storing results for polling.
    """

    def __init__(self) -> None:
        self._results: Dict[str, TaskResult] = {}
        self._tasks: Dict[str, asyncio.Task[Any]] = {}

    async def dispatch(
        self,
        task_func: Callable[..., TaskResult],
        task_id: str,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        """Dispatches task execution asynchronously without blocking."""
        logger.info(f"[TaskRunner] Dispatching task '{task_id}' ({task_func.__name__})")

        async def _run() -> None:
            # Run synchronous task in threadpool to avoid event loop stalling
            result = await asyncio.to_thread(task_func, task_id, *args, **kwargs)
            self._results[task_id] = result

        task = asyncio.create_task(_run())
        self._tasks[task_id] = task
        return task_id

    async def wait_for_completion(self, task_id: str, timeout_seconds: float = 5.0) -> TaskResult:
        """Waits for task to complete within timeout."""
        if task_id in self._tasks:
            try:
                await asyncio.wait_for(self._tasks[task_id], timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(f"[TaskRunner] Task '{task_id}' timed out after {timeout_seconds}s")
                return TaskResult(
                    task_id=task_id,
                    task_name="unknown",
                    status=TaskStatus.FAILURE,
                    error_message=f"Task timed out after {timeout_seconds}s",
                    duration_ms=timeout_seconds * 1000.0,
                )
        if task_id in self._results:
            return self._results[task_id]
        raise KeyError(f"Task '{task_id}' not found in runner registry.")

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Polls current task result without blocking."""
        return self._results.get(task_id)

