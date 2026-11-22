<div align="center">
  <img src="assets/logo/fluxkernel-glyph-dark.svg" alt="FluxKernel Logo" width="160" />
</div>

<br>

# <div align="center">FluxKernel</div>
### <div align="center">Voxion Labs Intelligence Kernel & Operating System</div>

<div align="center">

![Gateway](https://img.shields.io/badge/Gateway-Go%201.23%20%7C%20High--Concurrency-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![Accelerator](https://img.shields.io/badge/Accelerator-C%2B%2B20%20%7C%20SIMD%20AVX2-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![Kernel](https://img.shields.io/badge/Kernel-Python%20%7C%20Cognitive%20Core-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Interface](https://img.shields.io/badge/Interface-Server--Side%20Rendered%20UI-00ADD8?style=for-the-badge&logo=go&logoColor=white)
![License](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)

</div>

---

## 1. Technical Overview

**FluxKernel** is a sovereign multi-domain intelligence kernel and local runtime engineered for complex engineering synthesis, quantitative modeling, scientific computing, and system automation.

The platform executes across three coordinated tiers connected via high-speed IPC and C ABI shared memory interfaces:

- **Network Gateway & Reverse Proxy (Go 1.23)**: High-concurrency request routing, Server-Sent Events (SSE) telemetry streaming, workspace file management, and an industrial server-side rendered Mission Control console supporting System Default, Light, and Dark themes.
- **Native SIMD Vector Memory (C++20)**: Bare-metal AVX2 SIMD vector dot products (384-dimensional embeddings), L2 cosine metrics, character-level diff distance calculations, and filesystem execution boundaries accessible through a zero-overhead C ABI interface (`ctypes` / FFI).
- **Cognitive Reasoning Engine (Python 3.11 / FastAPI)**: Multi-step architectural synthesis, sandboxed multi-language code execution, episodic rule distillation, autonomous web grounding, and multi-domain agent swarm deliberation.

---

## 2. System Architecture & Topology

```
+=======================================================================================================+
|                                    FLUXKERNEL SYSTEM TOPOLOGY                                         |
+=======================================================================================================+
|                                                                                                       |
|  [ Operator / Browser / Mobile Device ]                                                               |
|          ||                                                                                           |
|          || HTTP / Server-Side Rendered Streams (:8080)                                               |
|          \/                                                                                           |
|  +-------------------------------------------------------------------------------------------------+  |
|  | NETWORK GATEWAY & MISSION CONTROL CONSOLE (:8080)                                               |  |
|  | -- High-Concurrency Request Router & Reverse Proxy                                              |  |
|  | -- Server-Side Rendered UI (System Default, Light, and Dark Themes)                             |  |
|  | -- In-Place Workspace Editor & LCS Unified Batch Diff Gate                                      |  |
|  | -- Real-Time Server-Sent Events (SSE) Telemetry Streamer                                        |  |
|  +-------------------------------------------------------------------------------------------------+  |
|          ||                                                 ||                                        |
|          || Local Reverse Proxy (HTTP/SSE)                  || C ABI Shared Memory / FFI             |
|          \/                                                 \/                                        |
|  +---------------------------------------+      +--------------------------------------------------+  |
|  | COGNITIVE REASONING ENGINE (:8000)    |      | NATIVE ACCELERATOR (libflux_core)                |  |
|  | -- Flux-1.0 Native Foundational Brain |<====>| -- AVX2 SIMD Vector Dot Products (384-dim)       |  |
|  | -- Multi-Domain Swarm Consensus DAG   | C ABI| -- Memory Difference Scoring (Diff Distance)     |  |
|  | -- Multi-Language Sandboxed Executor  | ctypes| -- Lexical Path Normalization & Isolation       |  |
|  | -- Episodic Rule Learning & Feedback  |      | -- Execution Boundary Verification               |  |
|  +---------------------------------------+      +--------------------------------------------------+  |
|          ||                     ||                                  ||                                |
|          || Task Dispatch       || WAL Mode Queries                 || File System Operations         |
|          \/                     \/                                  \/                                |
|  +----------------+     +--------------------------+    +------------------------------------------+  |
|  | ASYNC TASK     |     | ZERO-FOOTPRINT VAULT     |    | ISOLATED GIT SANDBOXES                   |  |
|  | QUEUE          |     | SQLite 3 (WAL Checkpoint |    | Target: ./workspace/                     |  |
|  | (Embedded)     |     | & Vacuum Compaction)     |    | Branches: flux/task-* (Clean Working Tree) | |
|  +----------------+     +--------------------------+    +------------------------------------------+  |
|                                                                                                       |
+=======================================================================================================+
```

---

## 3. Core Capabilities & Subsystems

### 3.1 Flux-1.0 Native AI Driver
The sovereign foundational reasoning engine (`FluxNativeSynthesizer`) operates without brittle keyword bags. It acts as an all-rounder brain that dynamically parses specifications, searches and grounds live research from the web, and generates multi-file plans with concurrent architectures. It also supports seamless routing between local and external engines (`flux-native`, `ollama`, `gemini`, `anthropic`).

### 3.2 Multi-Domain Agent Swarm Consensus
A directed acyclic graph (DAG) of four specialized domain agents collaborates on complex directives:
- **Tech Lead**: Evaluates concurrency, algorithmic complexity, memory bounds, and code correctness.
- **Science & Math Specialist**: Formulates differential equations, Hamiltonian simulations, and proofs.
- **Financial Auditor**: Conducts DCF audits, EBITDA margins, cash flow tracking, and option Greeks.
- **Executive Auditor**: Cross-examines ballots, resolves trade-offs, and synthesizes a unified action plan.

### 3.3 Isolated Git Task Sandboxing
All file mutations execute inside isolated git task branches (`flux/task-*`). The main working tree remains pristine while the agent edits, tests, and verifies code. Proposed mutations are presented through a unified diff review gate for inspection before atomic merge or abort.

### 3.4 Zero-Footprint Storage Vault
An embedded transactional SQLite 3 storage vault configured with Write-Ahead Logging (WAL). It stores conversation history, vector embeddings, and learned rules. To preserve host memory, persistent connections close automatically when idle (0% idle RAM connection footprint), complemented by on-demand WAL checkpointing and VACUUM compaction.

### 3.5 Industrial Mission Control UI
A minimalist, server-side rendered interface engineered for clarity and focus:
- **Theme Selection**: System Default (active by default), Light, and Dark options.
- **Domain Hubs**: Dedicated workspaces for Overview, Tech & Systems, Science & Math, Finance, Web Research, Memory & Rules, Swarm Deliberation, and Storage Vault.
- **Live Telemetry Ribbon**: Real-time status indicators monitoring gateway traffic, vector indexer state, core engine readiness, active sandboxes, and SSE event streaming.

---

## 4. 1-Click Launch Protocol

FluxKernel embeds its local daemon with a lightweight native OS WebView, providing a desktop application experience without heavyweight runtimes:

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
- **Local Network / Mobile Access**: Automatically detects your LAN IP address so any smartphone or tablet on the same Wi-Fi can connect directly via `http://<LAN_IP>:8080/dashboard`.
- **Clean Termination**: Exiting with `[Q]` or `[Ctrl+C]` cleanly terminates all daemons without orphan background processes.

---

## 5. Verification & Operations CLI

FluxKernel includes a master 12-phase verification suite and an operational workflow CLI (`ops.ps1` / `ops.sh`).

### 5.1 End-to-End Production Verification
Run the unified 12-phase master verification suite anytime to test SIMD vector math, web grounding, transcript ingestion, feedback learning, vault transactions, swarm consensus, sandboxing, and UI rendering:

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
  <strong>Voxion Labs</strong> · Intelligence Kernel · Go · C++20 · Python
</div>
