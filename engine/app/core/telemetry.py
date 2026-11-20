"""
telemetry.py — Real-time event telemetry and streaming bus for FluxKernel.

Features:
- Thread-safe in-memory ring buffer of recent system events.
- Asynchronous pub/sub broadcaster for Server-Sent Events (SSE).
- Structured telemetry events across agentic loops, swarms, storage, and compilers.
- Pure Python standard library implementation with zero external dependencies.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import threading
import time
from typing import Any, AsyncGenerator


@dataclass
class TelemetryEvent:
    event_id: str
    source: str  # autopilot | swarm | vault | compiler | system | sandbox
    level: str  # INFO | WARN | ERROR | DEBUG | SUCCESS
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_sse_frame(self) -> str:
        """Serializes event into standard Server-Sent Event (SSE) frame format."""
        data = json.dumps(self.to_dict())
        return f"id: {self.event_id}\nevent: {self.source}\ndata: {data}\n\n"


class TelemetryBus:
    """
    Central in-process event bus with thread-safe ring buffer and asynchronous pub/sub.
    """

    def __init__(self, max_history: int = 250) -> None:
        self.max_history = max_history
        self._history: deque[TelemetryEvent] = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._subscribers: set[asyncio.Queue[TelemetryEvent]] = set()
        self._seq = 0

    def emit(
        self,
        source: str,
        level: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> TelemetryEvent:
        """
        Emits a structured event synchronously or from background threads.
        Stores in history ring buffer and distributes to all active async subscribers.
        """
        with self._lock:
            self._seq += 1
            event_id = f"evt_{int(time.time() * 1000)}_{self._seq}"
            evt = TelemetryEvent(
                event_id=event_id,
                source=source,
                level=level.upper(),
                message=message,
                metadata=metadata or {},
            )
            self._history.append(evt)

            # Distribute to active asyncio queues safely
            for q in list(self._subscribers):
                try:
                    q.put_nowait(evt)
                except Exception:
                    pass

            return evt

    def get_history(self, limit: int = 50, source: str | None = None) -> list[TelemetryEvent]:
        """Returns recent events from the ring buffer with optional source filtering."""
        with self._lock:
            events = list(self._history)

        if source and source.lower() != "all":
            events = [e for e in events if e.source.lower() == source.lower()]

        return events[-limit:]

    async def subscribe(self) -> AsyncGenerator[TelemetryEvent, None]:
        """
        Yields an async stream of events for an individual SSE connection.
        First replays recent historical events, then pushes live events.
        """
        q: asyncio.Queue[TelemetryEvent] = asyncio.Queue(maxsize=100)

        # Replay the last 15 historical events immediately upon connection
        with self._lock:
            recent = list(self._history)[-15:]
            self._subscribers.add(q)

        for evt in recent:
            await q.put(evt)

        try:
            while True:
                evt = await q.get()
                yield evt
        finally:
            with self._lock:
                self._subscribers.discard(q)


# Global Telemetry Bus Singleton
_GLOBAL_BUS: TelemetryBus | None = None


def get_telemetry_bus() -> TelemetryBus:
    global _GLOBAL_BUS
    if _GLOBAL_BUS is None:
        _GLOBAL_BUS = TelemetryBus()
        # Seed initial startup event
        _GLOBAL_BUS.emit(
            source="system",
            level="INFO",
            message="FluxKernel Telemetry & Log Bus initialized.",
            metadata={"status": "online"},
        )
    return _GLOBAL_BUS


def emit_telemetry(
    source: str,
    level: str,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> TelemetryEvent:
    """Convenience helper to emit events to the global telemetry bus."""
    return get_telemetry_bus().emit(
        source=source,
        level=level,
        message=message,
        metadata=metadata,
    )
