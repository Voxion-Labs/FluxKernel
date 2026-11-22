<div align="center">
  <img src="assets/logo/fluxkernel-glyph-dark.svg" alt="FluxKernel Logo" width="160" />
</div>

<br>

# <div align="center">FluxKernel</div>
### <div align="center">Sovereign Agentic AI & Foundational LLM Combo Engine</div>

<div align="center">

![Agentic Core](https://img.shields.io/badge/Agentic%20Core-Autonomous%20Loop-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![Foundational LLM](https://img.shields.io/badge/Foundational%20LLM-Flux--1.0%20Native-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Swarm Deliberation](https://img.shields.io/badge/Swarm%20Deliberation-4--Specialist%20DAG-9333EA?style=for-the-badge)
![Vector Memory](https://img.shields.io/badge/Vector%20Memory-C%2B%2B20%20%7C%20AVX2%20SIMD-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![UI Console](https://img.shields.io/badge/Interface-Zero--JS%20SSR%20Console-10B981?style=for-the-badge)
![License](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)

</div>

---

## 1. Executive Overview

**FluxKernel** is a sovereign, self-contained intelligence platform engineered by fusing **Foundational Large Language Model (LLM) reasoning** with an **Autonomous Agentic Decision & Execution Loop**.

Traditional LLMs generate text in an isolated vacuum without the ability to verify their own code, inspect runtime errors, or interact with local repositories. Conversely, conventional orchestration frameworks lack deep foundational comprehension and rely on rigid, fragile script pipelines. 

FluxKernel solves this divide by unifying both paradigms into a cohesive, local-first engine:

1. **Foundational Neural Reasoning (`Flux-1.0`)**: An all-rounder foundational brain capable of understanding open-ended engineering directives, generating concurrent multi-file code plans, and dynamically searching the live web for authoritative citations without hardcoded keyword filters.
2. **Autonomous Agentic Execution Loop**: A self-healing **Plan → Write → Test → Fix** cycle that executes tasks inside isolated git sandboxes, analyzes compiler and runtime diagnostics, coordinates multi-specialist swarm deliberations, and commits verified mutations through an in-memory unified diff gate.
3. **Bare-Metal SIMD Acceleration (C++20)**: Hardware-accelerated AVX2 vector dot products (384-dimensional embeddings), cosine similarity search, and character-level diff distance calculations running directly against CPU registers via a zero-overhead C ABI interface.
4. **High-Concurrency Gateway & Mission Control (Go 1.23)**: A lightweight, server-side rendered (SSR) web console featuring industrial typography, System Default, Light, and Dark themes, and progressive real-time telemetry streaming with zero JavaScript overhead.

---

## 2. System Topology & Dual-Engine Synergy

```
+=======================================================================================================+
|                                  FLUXKERNEL SYSTEM ARCHITECTURE                                       |
+=======================================================================================================+
|                                                                                                       |
|  [ Operator / Browser / Mobile LAN Device ]                                                           |
|          ||                                                                                           |
|          || HTTP / Server-Side Rendered HTML5 Streams (:8080)                                         |
|          \/                                                                                           |
|  +-------------------------------------------------------------------------------------------------+  |
|  | NETWORK GATEWAY & MISSION CONTROL CONSOLE (Go 1.23)                                             |  |
|  | -- High-Concurrency Request Router & Reverse Proxy                                              |  |
|  | -- Lexio-Inspired Landing & Operator Session Console (/login)                                   |  |
|  | -- Server-Side Rendered Mission Control Hub (/dashboard, System Default / Light / Dark)        |  |
|  | -- In-Place Workspace Editor & Unified LCS Batch Diff Gate                                      |  |
|  | -- Real-Time Server-Sent Events (SSE) & Chunked Progress Telemetry                              |  |
|  +-------------------------------------------------------------------------------------------------+  |
|          ||                                                 ||                                        |
|          || Reverse Proxy (HTTP/SSE)                        || C ABI Shared Memory / FFI             |
|          \/                                                 \/                                        |
|  +---------------------------------------+      +--------------------------------------------------+  |
|  | FOUNDATIONAL LLM & REASONING BRAIN    |      | BARE-METAL SIMD ACCELERATOR (libflux_core)       |  |
|  | -- Flux-1.0 Native Synthesizer        |<====>| -- AVX2 SIMD Vector Dot Products (384-dim)       |  |
|  | -- Multi-File Architectural Planner   | C ABI| -- L2 Cosine Distance & Semantic Search         |  |
|  | -- Autonomous Live Web Grounding      |ctypes| -- Lexical LCS Difference Distance               |  |
|  | -- Multi-Model Driver Routing         |      | -- Memory Boundary & Path Normalization          |  |
|  +---------------------------------------+      +--------------------------------------------------+  |
|          ||                     ||                                  ||                                |
|          || Plan & Directives   || Transactions                     || Branch Mutations               |
|          \/                     \/                                  \/                                |
|  +-----------------------+  +--------------------------+    +--------------------------------------+  |
|  | AGENTIC EXECUTION     |  | ZERO-FOOTPRINT VAULT     |    | ISOLATED GIT TASK SANDBOXES          |  |
|  | -- Autonomous Loop    |  | -- SQLite 3 (WAL Mode)   |    | -- Branch: flux/task-*               |  |
|  | -- Swarm Consensus DAG|  | -- 0% Idle RAM Handles   |    | -- Zero Production Code Corruption   |  |
|  | -- Self-Healing Fix   |  | -- Checkpoint & Vacuum   |    | -- Sandbox Mutation Verification     |  |
|  | -- Episodic Rules     |  | -- Vector & Rule Storage |    | -- Atomic Merge / Abort Protocol     |  |
|  +-----------------------+  +--------------------------+    +--------------------------------------+  |
|                                                                                                       |
+=======================================================================================================+
```

---

## 3. Core Capabilities & Subsystems

### 3.1 Flux-1.0 Native Foundational Brain
The foundational reasoning engine (`FluxNativeSynthesizer`) operates as an all-rounder generalist. Rather than relying on rigid keyword dictionaries, it dynamically analyzes technical problem statements, decomposes complex tasks into structured multi-step plans, generates multi-file code architectures, and grounds novel specifications with live web research. In addition to native offline synthesis, it provides seamless multi-model routing to external backends (`flux-native`, `ollama`, `gemini`, `anthropic`).

### 3.2 Autonomous Self-Healing Agentic Loop
When an objective is dispatched, FluxKernel initiates an autonomous **Plan → Write → Test → Fix** cycle:
- **Plan**: Synthesizes structured implementation steps based on codebase context and active rules.
- **Write**: Emits target files within an isolated execution boundary.
- **Test**: Executes compiler passes, syntax validators, and test suites in real-time.
- **Fix**: Automatically captures compiler errors, analyzes stack traces, and generates targeted remediation patches without requiring manual intervention.

### 3.3 Multi-Domain Specialist Swarm Consensus
Complex architectural decisions are deliberated by a directed acyclic graph (DAG) of four specialized domain agents:
- **Tech Lead**: Evaluates concurrency patterns, algorithmic complexity, memory safety, and race hazards.
- **Science & Math Specialist**: Formulates differential equations, Hamiltonian simulations, and mathematical invariants.
- **Financial Auditor**: Audits cash flow projections, EBITDA margins, valuation metrics, and risk limits.
- **Executive Auditor**: Cross-examines ballots, resolves trade-offs, and synthesizes a unified consensus action plan.

### 3.4 Isolated Git Task Sandboxing
FluxKernel safeguards production codebases through dynamic git branch sandboxing. Every autonomous operation executes inside a dedicated `flux/task-*` branch created from the current repository HEAD. The main working tree remains pristine while the agent edits, builds, and verifies code. Proposed mutations are presented through an industrial unified diff gate for operator review before atomic merge or clean abort.

### 3.5 Bare-Metal Vector Memory & Zero-Footprint Vault
- **SIMD AVX2 Vector Vault**: The C++20 accelerator indexes workspace files into 384-dimensional vector embeddings, computing vector dot products and cosine similarity across register vectors with bare-metal speed.
- **0% Idle RAM Storage Vault**: Transactional SQLite 3 storage configured with Write-Ahead Logging (WAL). Storage connections close immediately upon query completion, ensuring zero persistent connection footprint during idle periods, complemented by automated WAL checkpoints and VACUUM compaction.
- **Episodic Rule Distillation**: Learns from corrections and negative constraints across past tasks, saving permanent rules that guide future reasoning.

### 3.6 Industrial Mission Control & Landing Console
A minimalist, server-side rendered interface engineered for clarity, focus, and low latency:
- **Lexio Aesthetic System**: Geometric typography powered by `Plus Jakarta Sans`, elevated floating operator cards, rounded status badges, and smooth scrollable landing sections.
- **Theme Selection**: Three modes supported—**System Default** (active by default), **Light**, and **Dark**.
- **Domain Hubs**: Workspaces for Overview, Systems Engineering, Science & Math, Quantitative Finance, Web Research, Episodic Rules, Swarm Consensus, and Storage Vault.
- **Zero-JS Policy**: Pure HTML5 and CSS compliance. No external JavaScript libraries, trackers, or client-side runtime bloat.

---

## 4. 1-Click Launch Protocol

FluxKernel embeds its local daemon with a lightweight native OS WebView, providing a desktop application experience without heavyweight electron dependencies:

### 4.1 Launch Commands

```bash
# Windows (PowerShell or Double-click)
.\run.bat
# or
powershell -ExecutionPolicy Bypass -File .\scripts\launch.ps1
# or
.\ops.ps1 start

# Linux / macOS (Terminal)
chmod +x run.sh ops.sh scripts/launch.sh
./run.sh
# or
./scripts/launch.sh
# or
./ops.sh start
```

- **Zero-Setup Boot**: Verifies Python and Go runtimes automatically.
- **Standalone Gateway**: Compiles a static Go binary (`bin/fluxkernel-gateway.exe` or `bin/fluxkernel-gateway`) with embedded assets.
- **Native OS WebView**: Launches Microsoft Edge in App Mode (`--app=http://127.0.0.1:8080/dashboard`) on Windows (borderless native desktop window, <15MB RAM) or Chrome/Chromium App Mode on Linux/macOS.
- **Dedicated Landing & Login Console**: Access the architecture landing page and operator session console at `http://127.0.0.1:8080/login`.
- **Local Network / Mobile Access**: Automatically detects your LAN IP address so any smartphone or tablet on the same Wi-Fi can connect directly via `http://<LAN_IP>:8080/dashboard` or `http://<LAN_IP>:8080/login`.
- **Clean Termination**: Exiting with `[Q]` or `[Ctrl+C]` cleanly terminates all daemons without orphan background processes.

---

## 5. Verification & Operations CLI

FluxKernel includes a master 12-phase verification suite and an operational workflow CLI (`ops.ps1` / `ops.sh`).

### 5.1 End-to-End Production Verification
Run the unified 12-phase master verification suite anytime to test SIMD vector math, web grounding, transcript ingestion, feedback learning, vault transactions, swarm consensus, git sandboxing, and UI rendering:

```bash
python scripts/verify_production.py
```

### 5.2 Operations CLI (`ops.ps1` / `ops.sh`)
```bash
# Windows (PowerShell)
.\ops.ps1 test                  # Execute Go, C++, Python, and Phase 12 master suite
.\ops.ps1 build                 # Compile static Go gateway binary
.\ops.ps1 lint                  # Format Go (gofmt) and Python (ruff)
.\ops.ps1 sync                  # Fetch origin/main and rebase cleanly
.\ops.ps1 push "feat: message"  # Lint, test, commit, auto-rebase, and push
.\ops.ps1 clean                 # Purge build caches and temporary files

# Linux / macOS (Bash)
./ops.sh test
./ops.sh build
./ops.sh lint
./ops.sh sync
./ops.sh push "feat: message"
./ops.sh clean
```

---

## 6. Continuous Integration & Quality Gates

The GitHub Actions pipeline ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) validates every commit across four parallel verification matrices:
1. **C++20 Native Matrix**: Builds with GCC-13 and Clang-17 under `-std=c++20`, runs `clang-format`, and executes static analysis with `cppcheck` and `CTest`.
2. **Go Gateway Matrix**: Checks `gofmt` compliance, executes `go vet`, compiles the static binary, and runs the unit test suite under `-race` on Go 1.22 and Go 1.23.
3. **Python Backend Matrix**: Lints and formats with Ruff, runs pytest across unit tests, and executes `scripts/verify_production.py`.
4. **Container Build Gate**: Builds the multi-stage Dockerfile to guarantee zero container regressions.

---

## 7. License Directives

This repository, its underlying sovereign logic, its decision matrix, and its architectural blueprints are classified proprietary intellectual property.

FluxKernel operates under the **Voxion Labs Master Proprietary License (VL-MPL)**. Open-source usage, commercial exploitation, reverse engineering, unauthorized public hosting, or distribution is strictly prohibited.

---

<br>
<div align="right">
  <b>Rudranarayan Jena</b><br>
  <i>Founder @ Voxion Labs</i>
</div>

---
<div align="center">
  (c) 2026 Voxion Labs & Rudranarayan Jena<br>
  <strong>Voxion Labs</strong> · Agentic AI & Foundational LLM · Go · C++20 · Python
</div>
