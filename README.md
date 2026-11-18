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

## 5. Repository Structure

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
|-- ops.ps1 / ops.sh                # Operational Workflow CLI (sync, push, lint, test, start)
|-- run.bat / run.sh                # Zero-setup 1-click universal launchers
|-- Dockerfile                      # Multi-stage production container build (Go + C++ + Python)
`-- docker-compose.yml              # Local multi-service orchestration (Postgres, Redis, Engine, Gateway)
```

---

## 6. Zero-Setup Launch Protocol

FluxKernel requires zero complex toolchains or global package managers (`npm`, `yarn`, `pnpm` are entirely removed).

### 6.1 Instant Launchers
```bash
# Windows (Double-click or run in PowerShell)
.\run.bat
# or
.\ops.ps1 start

# Linux / macOS (Terminal)
chmod +x run.sh ops.sh
./run.sh
# or
./ops.sh start
```
*   Auto-detects Python and Go runtimes.
*   Compiles native C++ shared library if compiler is present; falls back transparently if uncompiled.
*   Boots the Python Brain on `:8000` and Go Gateway on `:8080`.
*   Automatically launches the **Sovereign Console** in your default web browser (`http://localhost:8080/dashboard`).
*   Cleans up all child processes gracefully upon `Ctrl+C`.

### 6.2 Operational CLI (`ops.ps1` / `ops.sh`)
```bash
# Windows (PowerShell)
.\ops.ps1 sync                  # Fetch origin/main and rebase cleanly
.\ops.ps1 push "feat: message"  # Lint, test, commit, auto-rebase, and push
.\ops.ps1 lint                  # Format Go (gofmt) and Python (ruff)
.\ops.ps1 test                  # Execute Go, C++, and Python test suites
.\ops.ps1 clean                 # Purge build caches and temporary files

# Linux / macOS (Bash)
./ops.sh sync
./ops.sh push "feat: message"
./ops.sh lint
./ops.sh test
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
