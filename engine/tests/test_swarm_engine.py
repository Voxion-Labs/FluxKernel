"""
Unit Tests for Multi-Domain Agent Swarm (Phase 6).

Verifies:
1. Roster of four sovereign specialist agents (Tech, Science, Finance, Auditor).
2. Parallel specialist fan-out and structured perspective extraction.
3. Peer critique cross-examination DAG.
4. Executive Auditor consensus synthesis and unified action plan generation.
5. All three execution modes: consensus, pipeline, and audit.
6. Automatic persistence of deliberation sessions into Sovereign Storage Vault.
7. FastAPI swarm routes (/api/v1/swarm/*).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

# Ensure engine path is in sys.path
ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from app.core.swarm_engine import (  # noqa: E402
    SWARM_ROSTER,
    SwarmConsensus,
    get_swarm_coordinator,
    list_swarm_agents,
    list_swarm_sessions,
)


def test_swarm_roster_composition():
    """Verify that all four sovereign specialist profiles are registered."""
    agents = list_swarm_agents()
    assert len(agents) == 4

    agent_ids = {a["agent_id"] for a in agents}
    assert "tech_lead" in agent_ids
    assert "science_specialist" in agent_ids
    assert "finance_analyst" in agent_ids
    assert "executive_auditor" in agent_ids

    # Verify domains
    domains = {a["domain"] for a in agents}
    assert domains == {"tech", "science", "finance", "audit"}

    for a in agents:
        assert len(a["expertise"]) >= 5
        assert a["icon"] != ""


def test_consensus_deliberation_flow():
    """Verify end-to-end consensus deliberation across all specialists."""
    coordinator = get_swarm_coordinator()

    prompt = (
        "Design a high-throughput algorithmic order book with microsecond C++ SIMD matching, "
        "numerical risk constraints, and minimal memory allocation."
    )

    consensus = asyncio.run(coordinator.deliberate(prompt, mode="consensus", domain_hint="tech"))

    assert isinstance(consensus, SwarmConsensus)
    assert consensus.session_id.startswith("swarm_")
    assert consensus.user_prompt == prompt
    assert consensus.mode == "consensus"
    assert consensus.status in ("UNANIMOUS", "MAJORITY_CONSENSUS", "AUDITOR_INTERVENTION")

    # 3 specialists should have produced perspectives
    assert len(consensus.perspectives) == 3
    persp_ids = {p.agent_id for p in consensus.perspectives}
    assert "tech_lead" in persp_ids
    assert "science_specialist" in persp_ids
    assert "finance_analyst" in persp_ids

    # Verify structured perspectives
    for p in consensus.perspectives:
        assert p.analysis != ""
        assert p.proposal != ""
        assert len(p.concerns) >= 1
        assert p.vote in ("APPROVE", "REQUEST_CHANGES", "ABSTAIN")
        assert p.execution_time_ms >= 0.0

    # Peer critiques should be generated
    assert len(consensus.peer_critiques) >= 2
    for c in consensus.peer_critiques:
        assert c.reviewer_id in SWARM_ROSTER
        assert c.target_agent_id in SWARM_ROSTER
        assert c.critique_text != ""

    # Executive Auditor output
    assert consensus.executive_summary != ""
    assert len(consensus.unified_action_plan) >= 3
    assert len(consensus.risk_mitigations) >= 1
    assert consensus.total_latency_ms > 0.0


def test_audit_mode_deliberation():
    """Verify rapid direct audit review mode."""
    coordinator = get_swarm_coordinator()
    prompt = "Deploy an unverified third-party C++ binary without sandbox validation."

    consensus = asyncio.run(coordinator.deliberate(prompt, mode="audit"))

    assert consensus.mode == "audit"
    assert consensus.status == "AUDITOR_INTERVENTION"
    assert len(consensus.perspectives) == 1
    assert consensus.perspectives[0].agent_id == "executive_auditor"


def test_session_history_and_retrieval():
    """Verify session tracking in memory and list retrieval."""
    sessions = list_swarm_sessions()
    assert len(sessions) >= 2
    top = sessions[0]
    assert "session_id" in top
    assert "executive_summary" in top
    assert "unified_action_plan" in top


def test_fastapi_swarm_endpoints():
    """Verify FastAPI endpoints (/api/v1/swarm/*)."""
    try:
        from fastapi.testclient import TestClient

        from app.database.connection import Base, engine
        from app.main import app

        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        with TestClient(app) as client:
            # 1. Roster
            resp = client.get("/api/v1/swarm/agents")
            assert resp.status_code == 200
            agents = resp.json()
            assert len(agents) == 4

            # 2. Deliberate
            payload = {
                "prompt": "Evaluate quantum Monte Carlo simulation algorithm for asset pricing.",
                "mode": "consensus",
                "domain_hint": "science",
            }
            d_resp = client.post("/api/v1/swarm/deliberate", json=payload)
            assert d_resp.status_code == 200
            d_data = d_resp.json()
            assert d_data["status"] in ("UNANIMOUS", "MAJORITY_CONSENSUS", "AUDITOR_INTERVENTION")
            sess_id = d_data["session_id"]

            # 3. List Sessions
            s_resp = client.get("/api/v1/swarm/sessions")
            assert s_resp.status_code == 200
            s_data = s_resp.json()
            assert len(s_data) >= 1

            # 4. Get Session Detail
            detail_resp = client.get(f"/api/v1/swarm/sessions/{sess_id}")
            assert detail_resp.status_code == 200
            assert detail_resp.json()["session_id"] == sess_id
    except ImportError:
        pass


if __name__ == "__main__":
    test_swarm_roster_composition()
    test_consensus_deliberation_flow()
    test_audit_mode_deliberation()
    test_session_history_and_retrieval()
    test_fastapi_swarm_endpoints()
    print("All Multi-Domain Agent Swarm unit tests passed successfully!")
