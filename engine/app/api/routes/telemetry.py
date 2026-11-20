"""
telemetry.py — FastAPI routes for real-time telemetry streaming and event inspection.

Endpoints:
  GET  /api/v1/telemetry/stream — Real-time Server-Sent Events (SSE) feed
  GET  /api/v1/telemetry/events — Query recent historical events from ring buffer
  POST /api/v1/telemetry/emit   — Broadcast custom telemetry event
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.telemetry import emit_telemetry, get_telemetry_bus

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


class EmitEventRequest(BaseModel):
    source: str = Field(..., description="Event source: autopilot, swarm, vault, compiler, system")
    level: str = Field(default="INFO", description="Severity level: INFO, WARN, ERROR, DEBUG")
    message: str = Field(..., description="Human-readable event description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary event payload")


@router.get("/events")
def get_recent_events(limit: int = 50, source: str | None = None) -> list[dict[str, Any]]:
    """Returns recent events from the in-memory ring buffer."""
    bus = get_telemetry_bus()
    events = bus.get_history(limit=limit, source=source)
    return [e.to_dict() for e in events]


@router.post("/emit")
def emit_event(req: EmitEventRequest) -> dict[str, Any]:
    """Broadcasts a telemetry event to the global event bus."""
    evt = emit_telemetry(
        source=req.source,
        level=req.level,
        message=req.message,
        metadata=req.metadata,
    )
    return {"status": "emitted", "event": evt.to_dict()}


@router.get("/stream")
async def stream_telemetry():
    """
    Server-Sent Events (SSE) stream pushing real-time events to connected clients.
    Replays recent backlog, then flushes live events continuously.
    """
    bus = get_telemetry_bus()

    async def event_generator():
        try:
            async for evt in bus.subscribe():
                yield evt.to_sse_frame()
                # Yield control to event loop to ensure unbuffered transmission
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
