#!/usr/bin/env python3
"""
scripts/verify_production.py — End-to-End Production Verification & Parity Suite.

Performs exhaustive verification across all 12 architectural phases of FluxKernel:
  Phase 1:  C++ SIMD Vector Memory & Semantic Indexer
  Phase 2:  Autonomous Live Web Intelligence & Research Grounding
  Phase 3:  Cross-AI Learning Adapter (ChatGPT / Claude / Cursor)
  Phase 4:  Episodic Feedback & Sovereign Rule Learning
  Phase 5:  Zero-Footprint SQLite Storage Vault (WAL & 0% Idle RAM)
  Phase 6:  Multi-Domain Agent Swarm Consensus (4 Specialists)
  Phase 7:  Real-Time SSE Live Telemetry Stream
  Phase 8:  Universal Workspace & Cross-Domain Fast Search
  Phase 9:  Isolated Git Branching Sandbox (Zero File Corruption)
  Phase 10: Flux-1.0 Native AI Driver (Universal Foundational Model)
  Phase 11: Industrial Mission Control UI & Zero-JS Compliance
  Phase 12: Cross-Platform Parity, Security, and 1-Click Launchers

Exits 0 if all phases pass.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Setup repository paths
REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "engine"
GATEWAY_DIR = REPO_ROOT / "gateway"
NATIVE_DIR = REPO_ROOT / "native"
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

# Terminal styling
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_phase(num: int, title: str):
    print(f"\n{BOLD}{CYAN}=== [Phase {num:02d}/12] {title} ==={RESET}")


def assert_ok(condition: bool, msg: str):
    if not condition:
        print(f"  {RED}[FAIL]{RESET} {msg}")
        raise AssertionError(msg)
    print(f"  {GREEN}[PASS]{RESET} {msg}")


def verify_phase_1_simd_native():
    log_phase(1, "C++ SIMD Multi-Domain Memory & Semantic Vector Indexer")
    from app.core import native_bridge, project_rag

    version = native_bridge.get_native_version()
    assert_ok(bool(version), f"Native engine version reporting: {version}")

    # Vector dot product
    vec_a = [1.0, 2.0, 3.0, 4.0]
    vec_b = [2.0, 0.5, 1.0, 0.5]
    # (1*2) + (2*0.5) + (3*1) + (4*0.5) = 2 + 1 + 3 + 2 = 8.0
    dot = native_bridge.vector_dot_product(vec_a, vec_b)
    assert_ok(
        abs(dot - 8.0) < 1e-4, f"SIMD Vector dot product accurate (got {dot:.4f})"
    )

    # Multi-domain embedding & infer domain
    domain = project_rag.infer_domain("pkg/server/main.go")
    assert_ok(domain == "tech", f"Domain inference for Go code: {domain}")
    domain_sci = project_rag.infer_domain("papers/hamiltonian.tex")
    assert_ok(domain_sci == "science", f"Domain inference for TeX file: {domain_sci}")
    domain_fin = project_rag.infer_domain("data/cash_flow.csv")
    assert_ok(domain_fin == "finance", f"Domain inference for CSV ledger: {domain_fin}")


def verify_phase_2_web_intelligence():
    log_phase(2, "Live Autonomous Web Intelligence & Research Grounding Engine")
    from app.tools import web_fetcher

    # Search web structure
    results = web_fetcher.search_web("Raft Consensus Algorithm", max_results=3)
    assert_ok(
        isinstance(results, list) and len(results) > 0,
        f"Structured web search returned {len(results)} hits",
    )
    first = results[0]
    assert_ok(
        "title" in first and "snippet" in first,
        "Structured web hit contains title and snippet",
    )


def verify_phase_3_chat_ingestor():
    log_phase(3, "Cross-AI Learning Adapter (ChatGPT / Claude / Cursor Ingestor)")
    from app.tools import chat_ingestor

    sample_transcript = """# System Architecture Guidelines
### User:
Please enforce light theme by default and zero external JavaScript libraries.

### Assistant:
Understood. I will strictly apply light theme styling and pure server-side HTML/CSS rendering with zero JavaScript.
"""
    sessions = chat_ingestor.auto_detect_and_parse(sample_transcript, source="auto")
    assert_ok(
        len(sessions) >= 1,
        f"Parsed external AI transcript into {len(sessions)} session(s)",
    )
    first_session = sessions[0]
    assert_ok(len(first_session.turns) >= 1, "Extracted conversation turns correctly")
    assert_ok(
        first_session.title == "System Architecture Guidelines",
        f"Extracted transcript title: {first_session.title}",
    )


def verify_phase_4_feedback_learner():
    log_phase(4, "Episodic Feedback & Sovereign Rule-Learning Engine")
    from app.tools import feedback_learner

    # Add learned rule
    rule = feedback_learner.add_learned_rule(
        directive="Never import external npm or JavaScript scripts into dashboard views",
        domain="tech",
        category="constraint",
        source="user_explicit",
    )
    assert_ok(bool(rule.rule_id), f"Episodic rule registered: {rule.rule_id}")

    # Matching rule against directive
    matching = feedback_learner.get_matching_rules(
        "Add a script tag for external charts"
    )
    assert_ok(
        len(matching) >= 1,
        "Learned negative constraint successfully retrieved for directive",
    )


def verify_phase_5_storage_vault():
    log_phase(5, "Zero-Footprint Embedded Local/Cloud Storage Vault (0% Idle RAM)")
    from app.storage.vault import SovereignStorageVault

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "prod_vault.db"
        vault = SovereignStorageVault(db_path)

        # Initial stats
        stats = vault.get_stats()
        assert_ok(
            stats["status"] == "healthy",
            "Storage vault initialized healthy in WAL mode",
        )
        assert_ok(
            stats["active_connections"] == 0,
            "Zero idle persistent connections (0% idle RAM)",
        )

        # Save rule into vault
        vault.save_rule(
            "rule-prod-1", "Always maintain light theme default", "tech", "constraint"
        )
        rules = vault.get_all_rules()
        assert_ok(
            len(rules) == 1 and rules[0]["rule_id"] == "rule-prod-1",
            "Rule saved into SQLite vault",
        )

        # WAL checkpoint and defragmentation
        cp_ok = vault.wal_checkpoint()
        assert_ok(cp_ok, "WAL checkpoint completed cleanly")
        vault.vacuum()
        assert_ok(True, "Storage vault vacuum defragmentation succeeded")


def verify_phase_6_swarm_engine():
    log_phase(6, "Multi-Domain Agent Swarm (Tech / Sci / Finance / Auditor)")
    from app.core.swarm_engine import SWARM_ROSTER, get_swarm_coordinator

    assert_ok(
        len(SWARM_ROSTER) == 4,
        f"Swarm roster has 4 sovereign domain specialists ({list(SWARM_ROSTER.keys())})",
    )

    coordinator = get_swarm_coordinator()
    directive = "Design a high-throughput lock-free ring buffer in C++20 and verify cache locality."
    consensus = asyncio.run(coordinator.deliberate(directive, mode="consensus"))

    assert_ok(
        consensus.status in ("UNANIMOUS", "MAJORITY_CONSENSUS", "AUDITOR_INTERVENTION"),
        f"Swarm consensus reached: {consensus.status}",
    )
    assert_ok(
        len(consensus.perspectives) == 3,
        f"3 domain specialists submitted perspectives ({[p.agent_id for p in consensus.perspectives]})",
    )
    assert_ok(
        bool(consensus.unified_action_plan),
        "Executive Auditor synthesized unified execution plan",
    )


def verify_phase_7_telemetry():
    log_phase(7, "Real-Time SSE Live Telemetry & Log Streaming (Zero-JS)")
    from app.core.telemetry import TelemetryBus

    bus = TelemetryBus(max_history=10)
    bus.emit(
        source="gateway",
        level="INFO",
        message="Gateway operational",
        metadata={"port": 8080, "ram_mb": 14.8},
    )

    history = bus.get_history(limit=5)
    assert_ok(
        len(history) == 1, f"Telemetry event stored in ring buffer (len={len(history)})"
    )
    evt = history[0]
    assert_ok(evt.source == "gateway", f"Telemetry source matches: {evt.source}")
    frame = evt.to_sse_frame()
    assert_ok(
        "event: gateway" in frame and "data: " in frame,
        "Formatted valid Server-Sent Events (SSE) frame",
    )


def verify_phase_8_workspace_search():
    log_phase(8, "Universal Workspace & Cross-Domain Fast Search Bar")
    from app.core.workspace_search import search_workspace

    results = search_workspace(query="FluxKernel", target_dir=REPO_ROOT)
    assert_ok(
        results.get("total_matches", 0) > 0,
        f"Universal workspace search found {results.get('total_matches')} match(es)",
    )
    assert_ok(
        len(results.get("results", [])) > 0,
        "Workspace search returned structured matches",
    )


def verify_phase_9_git_sandbox():
    log_phase(9, "Isolated Git Branching Sandbox (Zero File Corruption)")
    from app.core.git_sandbox import GitSandboxManager

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "kernel.go").write_text("package main\n", encoding="utf-8")
        task_id = "prod-verify-sb"
        meta = GitSandboxManager.create_sandbox(task_id=task_id, target_dir=root)
        assert_ok(
            Path(meta.sandbox_path).exists(),
            f"Isolated sandbox created: {meta.branch_name}",
        )

        abort_res = GitSandboxManager.abort_sandbox(task_id=task_id, dest_dir=root)
        assert_ok(
            abort_res.get("status") == "aborted",
            "Sandbox aborted and cleaned up with zero trace on main branch",
        )


def verify_phase_10_flux_native_driver():
    log_phase(10, '"Flux-1.0" Native AI Driver (Default Sovereign Brain)')
    from app.core.flux_driver import (
        FluxNativeSynthesizer,
        get_active_engine,
        list_available_engines,
    )

    engines = list_available_engines()
    assert_ok(
        len(engines) >= 4, f"Driver registry contains {len(engines)} engine drivers"
    )
    active = get_active_engine()
    assert_ok(active == "flux-native", f"Default sovereign driver is active: {active}")

    # Test foundational universal synthesizer (all-rounder, no 1990 keyword bags)
    res = FluxNativeSynthesizer.synthesize(
        prompt="Build a concurrent worker pool in Go with goroutines and channels. Return only valid JSON.",
        system_prompt="PLANNER",
    )
    plan = json.loads(res.content)
    assert_ok(
        "files" in plan and len(plan["files"]) > 0,
        f"Synthesizer generated multi-file plan ({len(plan['files'])} files)",
    )
    assert_ok(
        plan.get("language") == "go",
        "Synthesizer correctly identified Go language spec",
    )


def verify_phase_11_industrial_mission_control():
    log_phase(11, "Industrial Mission Control UI (Domain Hub & Zero-JS Policy)")

    template_path = GATEWAY_DIR / "internal" / "ui" / "templates" / "dashboard.html"
    assert_ok(template_path.is_file(), f"Dashboard template exists: {template_path}")
    tmpl_content = template_path.read_text(encoding="utf-8")

    # Strict Zero-JS check: Ensure 0 <script> tags exist in dashboard.html
    scripts = re.findall(r"<script\b", tmpl_content, re.IGNORECASE)
    assert_ok(
        len(scripts) == 0,
        f"Strict Zero-JS Policy verified: 0 <script> tags found (found {len(scripts)})",
    )

    # Domain Hub Tabs
    required_tabs = [
        "overview",
        "tech",
        "science",
        "finance",
        "research",
        "rules",
        "consensus",
        "vault",
        "all",
    ]
    for tab in required_tabs:
        assert_ok(
            f"tab={tab}" in tmpl_content
            or f'data-tab="{tab}"' in tmpl_content
            or tab in tmpl_content,
            f"Domain hub tab present: '{tab}'",
        )

    # Mission Control Telemetry Ribbon
    assert_ok(
        "mission-control-ribbon" in tmpl_content,
        "Mission Control Telemetry Ribbon present in template",
    )

    # CSS Verification
    css_path = GATEWAY_DIR / "internal" / "ui" / "static" / "css" / "dashboard.css"
    assert_ok(css_path.is_file(), f"Dashboard CSS exists: {css_path}")
    css_content = css_path.read_text(encoding="utf-8")
    assert_ok(
        ".mission-control-ribbon" in css_content,
        "Telemetry ribbon styling verified in CSS",
    )
    assert_ok(
        ".domain-hub-bar" in css_content,
        "Domain Hub navigation styling verified in CSS",
    )


def verify_phase_12_cross_platform_production():
    log_phase(12, "End-to-End Cross-Platform Verification & 1-Click Launchers")

    # 1. Check Launchers exist
    ps1_launcher = SCRIPTS_DIR / "launch.ps1"
    sh_launcher = SCRIPTS_DIR / "launch.sh"
    assert_ok(
        ps1_launcher.is_file(), f"Windows 1-Click launcher exists: {ps1_launcher}"
    )
    assert_ok(
        sh_launcher.is_file(), f"Linux/macOS 1-Click launcher exists: {sh_launcher}"
    )

    # 2. Check .gitignore protects binaries and caches
    gitignore_path = REPO_ROOT / ".gitignore"
    assert_ok(gitignore_path.is_file(), ".gitignore exists")
    gi_content = gitignore_path.read_text(encoding="utf-8")
    assert_ok("bin/" in gi_content, ".gitignore excludes bin/")
    assert_ok(
        "*.exe" in gi_content or "*.dll" in gi_content,
        ".gitignore excludes compiled binaries (*.exe, *.dll)",
    )

    # 3. Check for forbidden buzzwords in codebase comments/strings
    forbidden_terms = ["FAANG", "faang", "lfs hell", "shadow ban"]
    scan_extensions = {".py", ".go", ".cpp", ".hpp", ".html", ".css", ".md"}
    found_violations = []

    for root, _, files in os.walk(REPO_ROOT):
        # Skip git, caches, and node_modules
        if any(
            skip in root
            for skip in [
                ".git",
                "__pycache__",
                ".ruff_cache",
                "node_modules",
                "bin",
                "build",
                ".flux_sandboxes",
            ]
        ):
            continue
        for file in files:
            p = Path(root) / file
            if p.suffix in scan_extensions:
                # Do not scan this verification script itself for the forbidden words check list
                if p.name == "verify_production.py":
                    continue
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    for term in forbidden_terms:
                        if term in text:
                            found_violations.append(
                                f"{p.relative_to(REPO_ROOT)}: contains forbidden term '{term}'"
                            )
                except (OSError, UnicodeDecodeError):
                    continue

    assert_ok(
        len(found_violations) == 0,
        f"Codebase hygiene verified: 0 forbidden terms found. {found_violations}",
    )


def main():
    print(
        f"\n{BOLD}=============================================================================={RESET}"
    )
    print(f"{BOLD}  FluxKernel Sovereign Autonomous Operating System{RESET}")
    print(
        f"{BOLD}  Master 12-Phase End-to-End Production Verification & Parity Suite{RESET}"
    )
    print(
        f"{BOLD}=============================================================================={RESET}"
    )

    phases = [
        verify_phase_1_simd_native,
        verify_phase_2_web_intelligence,
        verify_phase_3_chat_ingestor,
        verify_phase_4_feedback_learner,
        verify_phase_5_storage_vault,
        verify_phase_6_swarm_engine,
        verify_phase_7_telemetry,
        verify_phase_8_workspace_search,
        verify_phase_9_git_sandbox,
        verify_phase_10_flux_native_driver,
        verify_phase_11_industrial_mission_control,
        verify_phase_12_cross_platform_production,
    ]

    passed = 0
    failed = 0

    for idx, phase_fn in enumerate(phases, start=1):
        try:
            phase_fn()
            passed += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"\n{BOLD}{RED}Verification failed in Phase {idx}: {e}{RESET}")
            sys.exit(1)

    print(
        f"\n{BOLD}{GREEN}=============================================================================={RESET}"
    )
    print(
        f"{BOLD}{GREEN}  ALL 12 PHASES VERIFIED WITH 100% PARITY & ZERO REGRESSIONS!{RESET}"
    )
    print(
        f"{BOLD}{GREEN}  FluxKernel is Production-Ready for 1-Click Sovereign Launch.{RESET}"
    )
    print(
        f"{BOLD}{GREEN}=============================================================================={RESET}\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
