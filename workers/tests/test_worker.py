"""
Automated unit tests for worker tasks and in-memory execution runner.
"""

import pytest
from workers.app.config import TaskStatus
from workers.app.tasks import echo_probe_task, failing_probe_task
from workers.app.runner import InMemoryTaskRunner


def test_echo_probe_task_success():
    """Verifies that demonstration probe task executes successfully and computes hash."""
    payload = {"message": "Veritas worker probe", "sample_id": 42}
    result = echo_probe_task("tsk_001", payload)
    
    assert result.task_id == "tsk_001"
    assert result.status == TaskStatus.SUCCESS
    assert result.error_message is None
    assert result.duration_ms >= 0.0
    assert result.result_data is not None
    assert "payload_sha256" in result.result_data
    assert len(result.result_data["payload_sha256"]) == 64
    assert result.result_data["echo"] == payload


def test_failing_probe_task_traps_error():
    """Verifies that intentional failure task returns FAILURE without crashing."""
    result = failing_probe_task("tsk_err_002")
    
    assert result.task_id == "tsk_err_002"
    assert result.status == TaskStatus.FAILURE
    assert result.error_message is not None
    assert "Simulated operational failure" in result.error_message
    assert result.duration_ms >= 0.0


@pytest.mark.asyncio
async def test_in_memory_task_runner_dispatch_and_completion():
    """Verifies that InMemoryTaskRunner runs tasks asynchronously without Redis."""
    runner = InMemoryTaskRunner()
    task_id = "tsk_async_003"
    payload = {"async_test": True}

    dispatched_id = await runner.dispatch(echo_probe_task, task_id, payload)
    assert dispatched_id == task_id

    result = await runner.wait_for_completion(task_id, timeout_seconds=2.0)
    assert result.status == TaskStatus.SUCCESS
    assert result.result_data["echo"] == payload


@pytest.mark.asyncio
async def test_in_memory_task_runner_polling():
    """Verifies that runner get_result polls properly."""
    runner = InMemoryTaskRunner()
    task_id = "tsk_poll_004"
    await runner.dispatch(echo_probe_task, task_id, {"poll": 1})
    
    await runner.wait_for_completion(task_id)
    cached_result = runner.get_result(task_id)
    assert cached_result is not None
    assert cached_result.status == TaskStatus.SUCCESS

