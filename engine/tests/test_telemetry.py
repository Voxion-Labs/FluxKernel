"""
Unit Tests for Real-Time SSE Telemetry & Streaming Bus (Phase 7).

Verifies:
1. TelemetryBus ring buffer and thread-safe event emission.
2. Standard Server-Sent Events (SSE) frame formatting.
3. Event subscription and asynchronous generator delivery.
4. FastAPI telemetry endpoints (/api/v1/telemetry/*).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

# Ensure engine path is in sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from app.core.telemetry import (  # noqa: E402
    TelemetryBus,
    TelemetryEvent,
    emit_telemetry,
    get_telemetry_bus,
)


def test_telemetry_event_model_and_sse_formatting():
    """Verify TelemetryEvent serialization to dict and standard SSE frame."""
    evt = TelemetryEvent(
        event_id="evt_test_123",
        source="compiler",
        level="INFO",
        message="Compilation succeeded: libflux_core.dll",
        metadata={"exit_code": 0, "target": "c++20"},
    )

    data = evt.to_dict()
    assert data["event_id"] == "evt_test_123"
    assert data["source"] == "compiler"
    assert data["level"] == "INFO"

    frame = evt.to_sse_frame()
    assert frame.startswith("id: evt_test_123\n")
    assert "event: compiler\n" in frame
    assert "data: " in frame
    assert frame.endswith("\n\n")


def test_telemetry_bus_ring_buffer_and_filtering():
    """Verify event emission, ring buffer cap, and source filtering."""
    bus = TelemetryBus(max_history=5)

    for i in range(10):
        src = "swarm" if i % 2 == 0 else "vault"
        bus.emit(source=src, level="INFO", message=f"Event {i}", metadata={"idx": i})

    all_history = bus.get_history(limit=10)
    assert len(all_history) == 5  # capped by max_history=5
    assert all_history[-1].message == "Event 9"

    # Filter by source
    swarm_events = bus.get_history(limit=10, source="swarm")
    for e in swarm_events:
        assert e.source == "swarm"


def test_async_telemetry_subscription():
    """Verify real-time event streaming over asynchronous subscriber queue."""

    async def _run():
        bus = TelemetryBus(max_history=20)
        bus.emit("system", "INFO", "Pre-existing historical event")

        received: list[TelemetryEvent] = []

        async def _consumer():
            async for evt in bus.subscribe():
                received.append(evt)
                if len(received) >= 2:
                    break

        consumer_task = asyncio.create_task(_consumer())
        await asyncio.sleep(0.02)

        # Emit live event
        bus.emit("autopilot", "SUCCESS", "Live generated event")

        await asyncio.wait_for(consumer_task, timeout=2.0)
        assert len(received) == 2
        assert received[0].message == "Pre-existing historical event"
        assert received[1].message == "Live generated event"

    asyncio.run(_run())


def test_global_helper_and_fastapi_telemetry_routes():
    """Verify global emit_telemetry helper and FastAPI endpoint responses."""
    evt = emit_telemetry(
        source="system",
        level="SUCCESS",
        message="Global telemetry test event",
        metadata={"unit_test": True},
    )
    assert evt.event_id.startswith("evt_")

    bus = get_telemetry_bus()
    events = bus.get_history(limit=10)
    assert any(e.message == "Global telemetry test event" for e in events)

    try:
        from fastapi.testclient import TestClient

        from app.database.connection import Base, engine
        from app.main import app

        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        with TestClient(app) as client:
            # 1. Query events
            resp = client.get("/api/v1/telemetry/events?limit=10")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 1

            # 2. Emit event
            payload = {
                "source": "vault",
                "level": "INFO",
                "message": "Vault backup snapshot created",
                "metadata": {"frames": 10},
            }
            emit_resp = client.post("/api/v1/telemetry/emit", json=payload)
            assert emit_resp.status_code == 200
            assert emit_resp.json()["status"] == "emitted"
    except ImportError:
        pass


if __name__ == "__main__":
    test_telemetry_event_model_and_sse_formatting()
    test_telemetry_bus_ring_buffer_and_filtering()
    test_async_telemetry_subscription()
    test_global_helper_and_fastapi_telemetry_routes()
    print("All Real-Time Telemetry & Log Streaming unit tests passed successfully!")
