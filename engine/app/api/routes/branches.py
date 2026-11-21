from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.git_sandbox import GitSandboxManager

router = APIRouter(prefix="/branches", tags=["branches"])


class CreateBranchRequest(BaseModel):
    task_id: str = Field(..., description="Unique task identifier, e.g. task-9f3a1b")
    base_branch: str | None = Field(
        None, description="Base branch to fork from (default: current/main)"
    )


@router.get("")
def list_branches() -> list[dict[str, Any]]:
    """Lists all active and past isolated task branches."""
    return GitSandboxManager.list_sandboxes()


@router.post("/create")
def create_branch(req: CreateBranchRequest) -> dict[str, Any]:
    """Initializes an isolated task branch and working sandbox."""
    meta = GitSandboxManager.create_sandbox(task_id=req.task_id, base_branch=req.base_branch)
    return {
        "status": "created",
        "task_id": meta.task_id,
        "branch_name": meta.branch_name,
        "base_branch": meta.base_branch,
        "mode": meta.mode,
        "sandbox_path": meta.sandbox_path,
    }


@router.get("/{task_id}/diff")
def get_branch_diff(task_id: str) -> dict[str, Any]:
    """Retrieves the unified diff between the task branch and base workspace."""
    meta = GitSandboxManager.get_sandbox(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Task sandbox '{task_id}' not found")
    return GitSandboxManager.get_diff(task_id)


@router.post("/{task_id}/merge")
def merge_branch(task_id: str) -> dict[str, Any]:
    """Approves and merges changes from the isolated task branch into the workspace."""
    try:
        return GitSandboxManager.merge_sandbox(task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{task_id}/abort")
def abort_branch(task_id: str) -> dict[str, Any]:
    """Rejects and purges the task branch, leaving original files untouched."""
    return GitSandboxManager.abort_sandbox(task_id)
