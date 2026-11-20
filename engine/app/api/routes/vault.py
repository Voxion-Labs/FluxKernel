"""
vault.py — API routes for Sovereign Zero-Footprint Embedded Storage Vault (Phase 5).

Endpoints:
  GET  /api/v1/vault/status       — Storage telemetry, active connection count, WAL size
  POST /api/v1/vault/checkpoint   — Execute WAL checkpoint (TRUNCATE mode)
  POST /api/v1/vault/vacuum       — Compact database storage on disk
  POST /api/v1/vault/tasks/enqueue — Enqueue job into zero-daemon embedded queue
  GET  /api/v1/vault/tasks/{task_id} — Retrieve status of an embedded task
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.storage.vault import get_embedded_task_queue, get_storage_vault

router = APIRouter(prefix="/vault", tags=["vault"])


class EnqueueTaskRequest(BaseModel):
    task_name: str = Field(..., description="Name/type of the job to execute")
    payload: dict[str, Any] = Field(default_factory=dict, description="Task payload parameters")


@router.get("/status")
def get_vault_status() -> dict[str, Any]:
    """Returns deep storage telemetry, WAL state, and 0% idle RAM metrics."""
    vault = get_storage_vault()
    return vault.get_stats()


@router.post("/checkpoint")
def checkpoint_vault() -> dict[str, Any]:
    """Flushes all WAL frames back into the main database and shrinks WAL to 0 bytes."""
    vault = get_storage_vault()
    result = vault.wal_checkpoint(truncate=True)
    return {"status": "checkpointed", **result}


@router.post("/vacuum")
def vacuum_vault() -> dict[str, Any]:
    """Defragments and compacts database pages on disk."""
    vault = get_storage_vault()
    vault.vacuum()
    return {
        "status": "vacuumed",
        "database_size_bytes": vault.get_file_size(),
        "database_size_kb": round(vault.get_file_size() / 1024, 2),
    }


@router.post("/tasks/enqueue")
def enqueue_task(req: EnqueueTaskRequest) -> dict[str, Any]:
    """Enqueues an asynchronous task into the embedded zero-daemon task queue."""
    queue = get_embedded_task_queue()
    task_id = queue.enqueue(req.task_name, req.payload)
    return {"status": "enqueued", "task_id": task_id, "task_name": req.task_name}


@router.get("/tasks/{task_id}")
def get_task_status(task_id: str) -> dict[str, Any]:
    """Retrieves the execution state and result of an embedded task."""
    queue = get_embedded_task_queue()
    return queue.get_task_state(task_id)
