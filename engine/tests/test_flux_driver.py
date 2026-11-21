from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add engine directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.flux_driver import (
    AVAILABLE_ENGINES,
    FluxDriver,
    FluxNativeSynthesizer,
    get_active_engine,
    list_available_engines,
    set_active_engine,
)


def test_engine_registry():
    assert "flux-native" in AVAILABLE_ENGINES
    assert "gemini" in AVAILABLE_ENGINES
    assert "anthropic" in AVAILABLE_ENGINES
    assert "ollama" in AVAILABLE_ENGINES

    # Test listing
    engines = list_available_engines()
    assert len(engines) >= 4
    active_entry = next(e for e in engines if e["id"] == get_active_engine())
    assert active_entry["is_active"] is True

    # Test switching
    old_engine = get_active_engine()
    set_active_engine("gemini")
    assert get_active_engine() == "gemini"
    set_active_engine(old_engine)


def test_native_synthesis_multi_domain():
    # 1. Tech domain
    tech_res = FluxNativeSynthesizer.synthesize(
        prompt="Build a concurrent worker pool in Go",
        domain="tech",
    )
    assert tech_res.engine == "flux-native"
    assert tech_res.domain == "tech"
    assert "Flux-1.0 Native" in tech_res.content

    # 2. Finance domain
    fin_res = FluxNativeSynthesizer.synthesize(
        prompt="Audit treasury balance sheet and calculate net margin",
        domain="finance",
    )
    assert fin_res.domain == "finance"

    # 3. Science domain
    sci_res = FluxNativeSynthesizer.synthesize(
        prompt="Simulate exponential decay Hamiltonian",
        domain="science",
    )
    assert sci_res.domain == "science"


def test_native_agentic_plan_synthesis():
    prompt = "Implement a solution engine in Python with unit tests. Return only valid JSON."
    res = FluxNativeSynthesizer.synthesize(prompt=prompt, system_prompt="PLANNER AGENT")
    plan = json.loads(res.content)
    assert "entrypoint" in plan
    assert "language" in plan
    assert "files" in plan
    assert len(plan["files"]) >= 2
    assert any(f["path"] == "main.py" for f in plan["files"])


def test_foundational_all_rounder_plans():
    # 1. Levenshtein Dynamic Programming in Python
    res_lev = FluxNativeSynthesizer.synthesize(
        prompt="Implement a dynamic programming Levenshtein diff matrix in Python. Return only valid JSON.",
        system_prompt="PLANNER",
    )
    plan_lev = json.loads(res_lev.content)
    assert plan_lev["language"] == "python"
    assert any(f["path"] == "levenshtein.py" for f in plan_lev["files"])

    # 2. Concurrent Worker Pool in Go
    res_go = FluxNativeSynthesizer.synthesize(
        prompt="Build a concurrent worker pool in Go with goroutines and channels. Return only valid JSON.",
        system_prompt="PLANNER",
    )
    plan_go = json.loads(res_go.content)
    assert plan_go["language"] == "go"
    assert plan_go["entrypoint"] == "main.go"
    assert any(f["path"] == "pool.go" for f in plan_go["files"])

    # 3. Knowledge Grounding verification
    grounding = FluxNativeSynthesizer.ground_knowledge("Quantum harmonic oscillator simulation")
    assert isinstance(grounding, str)


def test_flux_driver_generate_async():
    async def _run():
        res = await FluxDriver.generate(
            prompt="Compute matrix bounds",
            domain="science",
            engine_override="flux-native",
        )
        assert res.engine == "flux-native"
        assert res.tokens_estimated > 0

    asyncio.run(_run())


def test_driver_api_endpoints():
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            # 1. Status
            res_status = client.get("/api/v1/driver/status")
            assert res_status.status_code == 200
            data_status = res_status.json()
            assert "active_engine" in data_status
            assert "available_engines" in data_status

            # 2. Select engine
            res_sel = client.post("/api/v1/driver/select", json={"engine": "flux-native"})
            assert res_sel.status_code == 200
            assert res_sel.json()["active_engine"] == "flux-native"

            # 3. Generate
            res_gen = client.post(
                "/api/v1/driver/generate",
                json={
                    "prompt": "Evaluate portfolio ROI",
                    "domain": "finance",
                    "persona": "coder",
                },
            )
            assert res_gen.status_code == 200
            data_gen = res_gen.json()
            assert "content" in data_gen
            assert data_gen["tokens_estimated"] > 0
    except ImportError:
        pass


if __name__ == "__main__":
    test_engine_registry()
    test_native_synthesis_multi_domain()
    test_native_agentic_plan_synthesis()
    test_foundational_all_rounder_plans()
    test_flux_driver_generate_async()
    test_driver_api_endpoints()
    print("All Flux-1.0 Native AI Driver unit tests passed successfully!")
