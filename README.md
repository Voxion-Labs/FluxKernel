<div align="center">
  <img src="assets/logo/fluxkernel-glyph-dark.svg" alt="FluxKernel Logo" width="160" />
</div>

<br>

# <div align="center">FluxKernel</div>
### <div align="center">Voxion Labs Autonomous Engineering Kernel & Operating System</div>

<div align="center">

![Architecture](https://img.shields.io/badge/Architecture-Autonomous%20Tri--Stack-39ff8a?style=for-the-badge)
![Gateway](https://img.shields.io/badge/Gateway-Go%201.23%20%7C%20High--Concurrency-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![Accelerator](https://img.shields.io/badge/Accelerator-C%2B%2B20%20%7C%20Native%20Bare--Metal-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![Kernel](https://img.shields.io/badge/Kernel-Python%20%7C%20FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Interface](https://img.shields.io/badge/Interface-Go%20Embedded%20SSR%20%7C%20Zero--JS-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-0%25%20Purged-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)

</div>

---

## 1. Executive Summary & Problem Space

### 1.1 The Failure of Legacy AI Coding Agents
Contemporary LLM-assisted programming relies overwhelmingly on stateless chat interfaces or fragile Node.js wrapper scripts. These architectures suffer from four systemic engineering defects:

```
+-------------------------------------------------------------------------------------------------------+
|                                    LEGACY AGENT ARCHITECTURAL DECAY                                   |
+-------------------------------------------------------------------------------------------------------+
|  1. Stateless Chat Loops       ||  Zero execution feedback. Code is hallucinated without compiler    |
|                                ||  verification or self-correcting test loops.                        |
|  2. Node.js / V8 Overhead      ||  Massive memory footprints (500MB+ for simple wrappers), supply-    |
|                                ||  chain security vulnerabilities across 1,000+ npm transitive deps.  |
|  3. Unrestricted Host Access   ||  No kernel-level sandbox. Unfiltered models can execute destructive |
|                                ||  commands ("rm -rf /", "del C:\*") or escape designated workspaces. |
|  4. Irreversible Code Drift    ||  Multi-file mutations are destructive with zero atomic checkpoints  |
|                                ||  or rollback mechanisms when the model degrades or writes bugs.     |
+-------------------------------------------------------------------------------------------------------+
```

### 1.2 The FluxKernel Sovereign Solution
**FluxKernel** replaces legacy wrappers with a deterministic, high-concurrency tri-stack operating system. By combining compiled Go networking, bare-metal C++20 sandbox controls, and an autonomous Python reasoning core, FluxKernel eliminates all Node.js/TypeScript dependencies (0% TS across the entire repository) and provides a fully self-healing, sandboxed software synthesis engine.

---

## 2. Tri-Stack Architecture & Topology

FluxKernel partitions responsibilities across three strictly bounded systems connected via high-speed IPC and C ABI shared memory interfaces:

```
+=======================================================================================================+
|                                  FLUXKERNEL SYSTEM TOPOLOGY & INGRESS                                 |
+=======================================================================================================+
|                                                                                                       |
|  [ Operator / Browser ]                                                                               |
|          ||                                                                                           |
|          || HTTP / Form POST / SSR Streaming                                                         |
|          \/                                                                                           |
|  +-------------------------------------------------------------------------------------------------+  |
|  | GO GATEWAY & SOVEREIGN WEB CONSOLE (:8080)                                                      |  |
|  | -- Go 1.23 High-Concurrency Reverse Proxy & Mutex Request Router                                |  |
|  | -- Embedded Pure HTML/CSS Sovereign Surface (Zero-JS Policy, html/template SSR)                 |  |
|  | -- In-Place Dynamic File Editor & LCS Unified Batch Diff Gate                                   |  |
|  | -- Real-Time Mutex Webhook Ledger & Edge Telemetry Multiplexer                                 |  |
|  +-------------------------------------------------------------------------------------------------+  |
|          ||                                                 ||                                        |
|          || Local Reverse Proxy (HTTP/SSE)                  || Direct FFI / Subprocess Call           |
|          \/                                                 \/                                        |
|  +---------------------------------------+      +--------------------------------------------------+  |
|  | PYTHON COGNITIVE BRAIN (:8000)        |      | C++20 NATIVE ACCELERATOR (libflux_core)          |  |
|  | -- Autonomous Agentic Loop Engine     |<====>| -- SIMD AVX2 Fast Vector Dot Products            |  |
|  | -- LLM Complexity & Context Router    | C ABI| -- Memory Difference Scoring (Diff Distance)     |  |
|  | -- Multi-Language Sandboxed Executor  | ctypes| -- Lexical Path Normalizer (Sandbox Jail)       |  |
|  | -- Atomic Checkpoint Rollback Manager |      | -- Host Destructive Command Pattern Interceptor  |  |
|  +---------------------------------------+      +--------------------------------------------------+  |
|          ||                     ||                                  ||                                |
|          || Job Dispatch        || SQL Queries                      || Disk I/O Realpath Guard        |
|          \/                     \/                                  \/                                |
|  +----------------+     +----------------+             +--------------------------+                   |
|  | REDIS BROKER   |     | POSTGRESQL DB  |             | AUTHORIZED WORKSPACE     |                   |
|  | Port :6379     |     | Port :5432     |             | ./workspace/             |                   |
|  | (Celery Queue) |     | (State / RAG)  |             | [.flux_snapshots Jail]   |                   |
|  +----------------+     +----------------+             +--------------------------+                   |
|                                                                                                       |
+=======================================================================================================+
```

---

## 3. Autonomous Execution & Self-Healing Decision Loop

The heart of FluxKernel is the autonomous `Plan -> Snapshot -> Write -> Test -> Fix` lifecycle managed by `engine/app/core/agentic_loop.py`. Instead of stopping at code generation, the kernel executes code in isolated subprocesses and continuously repairs defects up to `MAX_ITERATIONS` without human intervention.

```
+=======================================================================================================+
|                                AUTONOMOUS AGENTIC LOOP EXECUTION FLOW                                 |
+=======================================================================================================+
|                                                                                                       |
|  [ Engineering Directive ]                                                                            |
|          ||                                                                                           |
|          \/                                                                                           |
|  +------------------+                                                                                 |
|  |   1. PLANNER     | ===> Formulates execution entrypoint, target language, and file manifests       |
|  +------------------+                                                                                 |
|          ||                                                                                           |
|          \/                                                                                           |
|  +------------------+                                                                                 |
|  |  2. ATOMIC SNAP  | ===> Commits SHA-256 pre-mutation snapshot checkpoint (.flux_snapshots/)        |
|  +------------------+                                                                                 |
|          ||                                                                                           |
|          \/                                                                                           |
|  +------------------+                                                                                 |
|  |  3. C++ SANDBOX  | ===> Validates paths via lexically_relative; blocks .git, .env, and escapes     |
|  +------------------+                                                                                 |
|          ||                                                                                           |
|          \/                                                                                           |
|  +------------------+                                                                                 |
|  |  4. WRITE FILES  | ===> Persists modified files directly to disk within authorized workspace       |
|  +------------------+                                                                                 |
|          ||                                                                                           |
|          \/                                                                                           |
|  +------------------+                                                                                 |
|  |  5. RUN SUBPROC  | ===> Executes entrypoint in isolated runtime (Go test, Python, C++20)           |
|  +------------------+                                                                                 |
|          ||                                                                                           |
|          +==================================+                                                         |
|          ||                                 ||                                                        |
|   [ Test Succeeded (0) ]             [ Test Failed (Exit != 0) ]                                     |
|          ||                                 ||                                                        |
|          \/                                 \/                                                        |
|  +------------------------+      +-------------------------+                                          |
|  |  6. BATCH DIFF GATE    |      |  6. FIX GENERATOR       |                                          |
|  |  -- Generates unified  |      |  -- Injects stderr logs |                                          |
|  |     LCS diff table     |      |  -- Iteration counter++ |                                          |
|  |  -- Halts for operator |      |  -- Prompts model to    |                                          |
|  |     Approve or Reject  |      |     repair its syntax   |                                          |
|  +------------------------+      +-------------------------+                                          |
|          ||                                 ||                                                        |
|          || Approved                        +==> [ Loops back to Step 2 ]                             |
|          \/                                                                                           |
|  +------------------------+                                                                           |
|  |  MUTATION COMMITTED    |                                                                           |
|  +------------------------+                                                                           |
|                                                                                                       |
+=======================================================================================================+
```

---

## 4. Hardened C++20 Sandbox Jail & Threat Model

Unfiltered LLMs possess the capability to emit destructive shell code or attempt directory escape attacks. FluxKernel enforces safety not through prompt-engineering, but through a physical C++20 native binary barrier (`native/src/flux_core.cpp`):

```
+=======================================================================================================+
|                                    C++20 NATIVE SECURITY BARRIER                                      |
+=======================================================================================================+
|                                                                                                       |
|  [ Inbound Operation: Path or Command ]                                                               |
|          ||                                                                                           |
|          +--------------------------------------------+                                               |
|          ||                                           ||                                              |
|          \/                                           \/                                              |
|  [ PATH MUTATION ATTEMPT ]                    [ SHELL EXECUTION ATTEMPT ]                             |
|          ||                                           ||                                              |
|          || std::filesystem::path                     || Regex & Token Scan                           |
|          \/                                           \/                                              |
|  +---------------------------------+          +---------------------------------+                     |
|  | 1. Lexical Path Normalization   |          | 1. Destructive Command Blacklist|                     |
|  |    Eliminates ../, relative dot |          |    Blocks: rm -rf, del /f /s,   |                     |
|  |    tricks, and symlink evasion  |          |    fork-bombs, mkfs, diskpart   |                     |
|  +---------------------------------+          +---------------------------------+                     |
|          ||                                           ||                                              |
|          \/                                           \/                                              |
|  +---------------------------------+          +---------------------------------+                     |
|  | 2. Partition Jail Check         |          | 2. Shell Injection Filter       |                     |
|  |    Blocks writes to:            |          |    Intersects chained commands  |                     |
|  |    -- .git/                     |          |    and unauthorized sub-shells  |                     |
|  |    -- .flux_snapshots/          |          +---------------------------------+                     |
|  |    -- .env                      |                          ||                                      |
|  +---------------------------------+                          ||                                      |
|          ||                                                   ||                                      |
|          +====================+===============================+                                       |
|                               ||                                                                      |
|                               \/                                                                      |
|                  +--------------------------+                                                         |
|                  |     VERIFICATION GATE    |                                                         |
|                  +--------------------------+                                                         |
|                     //                      \\                                                        |
|             [ PASSED ]                      [ VIOLATION DETECTED ]                                    |
|                 ||                                    ||                                              |
|                 \/                                    \/                                              |
|      Proceed to Disk Mutation               SecurityException Raised                                  |
|                                             Pre-Mutation Rollback Armed                               |
|                                             Operation Aborted                                         |
|                                                                                                       |
+=======================================================================================================+
```

---

## 5. Master 12-Phase Sovereign Roadmap (100% Completed)

FluxKernel has completed all 12 planned architectural milestones in sovereign sequence:

| Phase | Architecture Milestone | Description & Capabilities | Status |
| :---: | :--- | :--- | :---: |
| **01** | **C++ SIMD Vector Memory** | AVX2 SIMD dot product (384-dim), L2 cosine metrics, zero-copy C ABI bridge | ✅ Completed |
| **02** | **Autonomous Web Grounding** | Live external web intelligence, HTTP scraping, fact extraction & cache | ✅ Completed |
| **03** | **Cross-AI Learning Adapter** | Ingests ChatGPT, Claude, and Cursor transcripts into episodic vector memory | ✅ Completed |
| **04** | **Episodic Feedback Engine** | Sovereign rule learning from user corrections, negative constraint interceptors | ✅ Completed |
| **05** | **Zero-Footprint Storage Vault** | Transactional SQLite WAL storage, automatic checkpointing, 0% idle RAM | ✅ Completed |
| **06** | **Multi-Domain Agent Swarm** | 4-specialist DAG (Tech Lead, Math/Sci, Finance Analyst, Executive Auditor) | ✅ Completed |
| **07** | **Real-Time SSE Telemetry** | High-throughput streaming bus, live system vitals, 100% Zero-JS streaming | ✅ Completed |
| **08** | **Universal Workspace Search** | Cross-domain multi-file symbol, token, and line-level fast search index | ✅ Completed |
| **09** | **Isolated Git Sandbox** | Git branch isolation (`flux/task-*`), dirty write barriers, zero file corruption | ✅ Completed |
| **10** | **Flux-1.0 Native AI Driver** | Sovereign foundational brain, dynamic spec generation, multi-engine routing | ✅ Completed |
| **11** | **Industrial Mission Control UI** | Domain Hubs (Tech, Sci, Finance, Daily), Telemetry Ribbon, Zero-JS SSR | ✅ Completed |
| **12** | **1-Click Production Launch** | Cross-platform launchers, Native OS WebView (Approach A), End-to-End Suite | ✅ Completed |

---

## 6. Repository Structure

```text
FluxKernel/
|-- gateway/                        # Go 1.23 High-Performance Gateway & Sovereign Console (:8080)
|   |-- cmd/server/main.go          # Gateway ingress, reverse proxy, telemetry router
|   |-- internal/config/            # Environment variable bindings & defaults
|   |-- internal/handlers/          # Specialized API endpoints (Chat, Autopilot, Tasks, Webhooks)
|   |-- internal/proxy/             # Upstream reverse proxy and CORS middleware
|   |-- internal/ui/                # Embedded Zero-JS Sovereign Web Engine
|   |   |-- static/css/             # Enterprise Minimalist Stylesheet (Light, Dark, System)
|   |   |-- static/img/             # Embedded vector assets (brand.svg, logo.svg)
|   |   |-- templates/              # Pure Go html/template files (layout.html, dashboard.html)
|   |   |-- diff.go                 # Optimal LCS unified diff generator
|   |   |-- diff_test.go            # Diff verification unit test suite
|   |   `-- ui.go                   # SSR request orchestrator & form post handlers
|   |-- Dockerfile                  # Distroless production container image
|   `-- go.mod
|
|-- native/                         # C++20 Bare-Metal Accelerator & Sandbox Jail
|   |-- include/flux/flux_core.h    # Exported C ABI headers
|   |-- src/flux_core.cpp           # Vector dot, diff distance, path barriers
|   |-- tests/test_flux_core.cpp    # CTest suite
|   `-- CMakeLists.txt              # Multi-OS build specification (Linux, Win, Mac)
|
|-- engine/                         # Python Cognitive Kernel Brain (:8000)
|   |-- app/core/                   # Agentic loop, LLM router, rollback engine, native bridge
|   |-- app/tools/                  # Sandboxed execution arsenal (Python, Go, C++20)
|   |-- app/api/                    # FastAPI routes & telemetry streams
|   |-- tests/                      # Unit & integration verification suites
|   |-- requirements.txt            # Python dependencies (FastAPI, SQLAlchemy, Celery)
|   `-- pyproject.toml              # Ruff linter and formatter configuration
|
|-- scripts/                        # Production Automation & Master Verification
|   |-- launch.ps1                  # Windows 1-Click Launcher (Approach A: Native Edge WebView)
|   |-- launch.sh                   # Linux / macOS 1-Click Launcher (App Mode / Default Browser)
|   `-- verify_production.py        # Master 12-Phase End-to-End Parity Verification Suite
|
|-- ops.ps1 / ops.sh                # Operational Workflow CLI (sync, push, lint, test, build, start)
|-- run.bat / run.sh                # 1-Click universal launcher entrypoints
|-- Dockerfile                      # Multi-stage production container build (Go + C++ + Python)
`-- docker-compose.yml              # Local multi-service orchestration (Postgres, Redis, Engine, Gateway)
```

---

## 7. 1-Click Sovereign Launch Protocol (Approach A)

FluxKernel adopts **Approach A: Embedded Local Daemon + Native OS WebView**, eliminating heavy Electron.js runtimes (saving over 400MB of RAM) and external Node.js dependencies (`npm`, `yarn`, `pnpm` are 0% present).

### 7.1 Instant 1-Click Launchers
```bash
# Windows (Double-click or run in PowerShell)
.\run.bat
# or
.\scripts\launch.ps1
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
*   **Zero-Dependency Boot**: Automatically checks for Python and Go runtimes.
*   **Static Go Gateway Binary**: Automatically compiles a standalone, stripped static binary (`bin/fluxkernel-gateway.exe` or `bin/fluxkernel-gateway`) with embedded templates and styles (`<15MB` binary footprint).
*   **Dual Daemons**: Boots the Python Cognitive Brain on `:8000` and Go Gateway on `:8080`.
*   **Native OS WebView**: Launches Microsoft Edge in App Mode (`--app=http://127.0.0.1:8080/dashboard`) on Windows (borderless window, zero address bar, native desktop feel) or Chrome/Chromium App Mode on Linux/macOS.
*   **Mobile / LAN Connectivity**: Exposes local network endpoints (`http://<LAN_IP>:8080/dashboard`) so mobile devices (iOS, Android) on the same Wi-Fi can directly interact with Mission Control.
*   **Graceful Exit**: Pressing `Q` or `Ctrl+C` cleanly shuts down all background processes with zero orphan PIDs.

### 7.2 Master 12-Phase Verification Suite
To verify end-to-end tri-stack integrity across all 12 architectural phases:
```bash
# Unified Master Verification
python scripts/verify_production.py

# or via Ops CLI
.\ops.ps1 test          # Windows
./ops.sh test           # Linux / macOS
```

### 7.3 Operational CLI (`ops.ps1` / `ops.sh`)
```bash
# Windows (PowerShell)
.\ops.ps1 sync                  # Fetch origin/main and rebase cleanly
.\ops.ps1 push "feat: message"  # Lint, test, commit, auto-rebase, and push
.\ops.ps1 lint                  # Format Go (gofmt) and Python (ruff)
.\ops.ps1 test                  # Execute Go, C++, Python, and Phase 12 master suite
.\ops.ps1 build                 # Compile static Go gateway binary
.\ops.ps1 start                 # 1-Click launch of daemons and Native OS WebView
.\ops.ps1 clean                 # Purge build caches and temporary files

# Linux / macOS (Bash)
./ops.sh sync
./ops.sh push "feat: message"
./ops.sh lint
./ops.sh test
./ops.sh build
./ops.sh start
./ops.sh clean
```

### 6.3 Multi-Container Deployment (Docker Compose)
```bash
docker-compose up --build -d
```

---

## 7. Continuous Integration & Quality Gates

The GitHub Actions pipeline ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) validates every commit across four parallel verification matrices:
1.  **C++20 Native Matrix**: Builds with GCC-13 and Clang-17 under `-std=c++20`, runs `clang-format`, executes static analysis with `cppcheck`, and runs `CTest`.
2.  **Go Gateway Matrix**: Checks `gofmt` compliance, executes `go vet`, compiles the static binary, and runs the unit test suite under `-race` on Go 1.22 and Go 1.23.
3.  **Python Backend Matrix**: Lints and formats with Ruff, imports FastAPI routes, and executes pytest across the sandbox, rollback, and agentic loop test suites.
4.  **Container Build Gate**: Builds the multi-stage Dockerfile to guarantee zero container regressions.

---

## 8. License Directives

This repository, its underlying autonomous logic, its agentic loop, and its architectural blueprints are classified proprietary intellectual property.

FluxKernel operates under the **Voxion Labs Proprietary Research License (VL-PRL)**. Open-source usage, commercial exploitation, reverse engineering, unauthorized public hosting, or distribution is strictly prohibited.

---

<br>
<div align="right">
  <b>Rudranarayan Jena</b><br>
  <i>Founder @ Voxion Labs</i>
</div>

---
<div align="center">
  (c) 2026 Voxion Labs & Rudranarayan Jena<br>
  <strong>Voxion Labs</strong> · Agentic AI · Go · C++20 · Python
</div>
