"""
swarm.py — API routes for Multi-Domain Agent Swarm (Phase 6).

Endpoints:
  GET  /api/v1/swarm/agents         — Roster of sovereign specialists & competencies
  POST /api/v1/swarm/deliberate      — Run multi-agent consensus deliberation
  GET  /api/v1/swarm/sessions       — List recent swarm sessions
  GET  /api/v1/swarm/sessions/{id}  — Inspect specific swarm session transcript
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.swarm_engine import (
    get_swarm_coordinator,
    get_swarm_session,
    list_swarm_agents,
    list_swarm_sessions,
)

router = APIRouter(prefix="/swarm", tags=["swarm"])


class DeliberateRequest(BaseModel):
    prompt: str = Field(..., description="Directive or problem statement for the swarm")
    mode: Literal["consensus", "pipeline", "audit"] = Field(
        default="consensus", description="Swarm execution mode"
    )
    domain_hint: str | None = Field(
        default=None, description="Optional domain hint (tech, science, finance, general)"
    )


@router.get("/agents")
def get_agents() -> list[dict[str, Any]]:
    """Returns the roster of sovereign specialist agents, competencies, and roles."""
    return list_swarm_agents()


@router.post("/deliberate")
async def deliberate(req: DeliberateRequest) -> dict[str, Any]:
    """
    Submits a directive to the Multi-Domain Agent Swarm for concurrent analysis,
    peer critique, and executive consensus synthesis.
    """
    clean_prompt = req.prompt.strip()
    if not clean_prompt:
        raise HTTPException(status_code=400, detail="Directive prompt cannot be empty.")

    coordinator = get_swarm_coordinator()
    consensus = await coordinator.deliberate(
        user_prompt=clean_prompt,
        mode=req.mode,
        domain_hint=req.domain_hint,
    )
    return consensus.to_dict()


@router.get("/sessions")
def get_sessions() -> list[dict[str, Any]]:
    """Lists recent swarm consensus sessions."""
    return list_swarm_sessions()


@router.get("/sessions/{session_id}")
def get_session_detail(session_id: str) -> dict[str, Any]:
    """Retrieves full transcript and vote breakdown for a swarm deliberation."""
    sess = get_swarm_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Swarm session not found.")
    return sess.to_dict()
