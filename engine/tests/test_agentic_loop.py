"""
test_agentic_loop.py — Verification of the autonomous loop event ledger and timeline tracking.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Ensure engine path is in sys.path
ENGINE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)

from app.core.agentic_loop import (  # noqa: E402
    abort_loop,
    create_loop,
    get_latest_loop,
    get_loop,
)


def test_loop_creation_and_latest_registry():
    prompt = "Create a robust concurrent queue in Go"
    persona = "coder"
    sys_prompt = "You are FluxKernel."

    loop_id, state = create_loop(prompt, persona, sys_prompt)
    assert loop_id is not None
    assert state.loop_id == loop_id
    assert state.initial_prompt == prompt
    assert state.persona_name == persona
    assert state.status == "running"
    assert state.abort_flag is False

    # Check retrieval
    fetched = get_loop(loop_id)
    assert fetched is state

    # Check latest retrieval
    latest = get_latest_loop()
    assert latest is state


def test_loop_event_ledger():
    loop_id, state = create_loop("Test prompt", "coder", "Test sys prompt")

    async def _emit_sequence():
        await state.emit("iteration_start", {"iteration": 1, "max_iterations": 5})
        await state.emit(
            "snapshot_created", {"iteration": 1, "snapshot_id": "snap_1", "file_count": 3}
        )
        await state.emit("file_written", {"iteration": 1, "path": "test.py"})
        await state.emit("test_start", {"iteration": 1, "entrypoint": "test.py"})
        await state.emit("test_result", {"iteration": 1, "success": True, "exit_code": 0})
        await state.emit("loop_done", {"iterations_used": 1, "diff_batch": []})

    asyncio.run(_emit_sequence())

    assert len(state.events) == 6
    assert state.events[0]["event"] == "iteration_start"
    assert state.events[1]["event"] == "snapshot_created"
    assert state.events[1]["snapshot_id"] == "snap_1"
    assert state.events[4]["event"] == "test_result"
    assert state.events[4]["success"] is True
    assert state.events[5]["event"] == "loop_done"


def test_loop_abort():
    loop_id, state = create_loop("Abort test", "auditor", "sys")
    assert state.abort_flag is False

    success = abort_loop(loop_id)
    assert success is True
    assert state.abort_flag is True


if __name__ == "__main__":
    test_loop_creation_and_latest_registry()
    test_loop_event_ledger()
    test_loop_abort()
    print("All Agentic Loop and Timeline tests passed successfully!")
