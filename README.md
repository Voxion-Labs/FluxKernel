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

## 1. Executive Abstract

**FluxKernel** is a proprietary, full-stack autonomous AI engineering environment and cognitive operating system engineered exclusively by Voxion Labs. 

Standard large language model (LLM) implementations function as stateless, localized chat wrappers requiring constant human orchestration and context injection. FluxKernel abandons this paradigm. It operates as a stateful, agentic operating system capable of executing complex software architecture tasks independently.

The system is architected as a **high-concurrency tri-stack sovereign platform** featuring **0% TypeScript / 0% Node.js across the entire repository**:
1. **High-Performance Go Gateway & Web Console (`gateway/`)**: Handles edge networking, SSE streaming multiplexing, webhook ring buffering, concurrent file-tree operations, and embedded Zero-JS Web UI on Port `8080`.
2. **C++20 Native Accelerator (`native/`)**: Delivers bare-metal SIMD vector dot products, high-speed memory difference scoring, and canonical sandbox filesystem traversal barriers via a C ABI shared library (`libflux_core`).
3. **Python Cognitive Kernel (`engine/`)**: Serves as the central cognitive brain on Port `8000`, orchestrating the autonomous reasoning cycle, LLM tool dispatch, AST codebase mutations, and multi-language execution (Python, native Go, and C++20).
4. **Sovereign Embedded Console (`gateway/internal/ui/`)**: A pure Go `html/template` SSR console on Port `8080` with zero client-side JavaScript, enterprise minimalist styling, light/dark/system themes, in-place file editing, and unified batch diff approval gates.

---

## 2. Infrastructure Topology

FluxKernel operates on a strictly partitioned multi-language repository designed for zero-coupling, maximum throughput, and uncompromising operational security.

```text
FluxKernel/
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Enterprise Multi-Stage CI/CD (Go, C++, Python)
│       └── bot-json-writer.yml     # Autonomous Bot Activity Ledger (voxion-bot)
├── assets/
│   └── architecture/
│       ├── database-schema.md      # Relational and vector schemas
│       ├── system-design.drawio    # Top-level execution topology
│       └── tool-flow-diagram.png   # Tool routing execution flow
├── gateway/                        # Go 1.23 High-Performance Gateway & Sovereign Console (:8080)
│   ├── cmd/server/main.go          # Gateway entrypoint & reverse proxy
│   ├── internal/handlers/          # Specialized API handlers (Chat, Autopilot, Tasks, Web, Webhooks, Workspace)
│   ├── internal/ui/                # Embedded Zero-JS Web UI (templates, static CSS, diff engine)
│   ├── Dockerfile                  # Distroless minimal attack-surface image
│   └── go.mod
├── native/                         # C++20 Bare-Metal Native Accelerator
│   ├── include/flux/flux_core.h    # Exported C ABI declarations
│   ├── src/flux_core.cpp           # Vector dot, diff distance, path barriers
│   ├── tests/test_flux_core.cpp    # Native C++ test harness
│   └── CMakeLists.txt              # Modern CMake build configuration
├── engine/                         # Python Cognitive Brain (:8000)
│   ├── app/core/                   # Agentic loop, LLM router, native C ABI bridge
│   ├── app/tools/                  # Physical execution arsenal (Go, C++, Python)
│   ├── app/api/                    # FastAPI routes & telemetry endpoints
│   ├── tests/                      # Unit & integration verification suites
│   ├── requirements.txt            # Python dependencies (Celery, FastAPI, etc.)
│   └── pyproject.toml              # Ruff linter and formatter configuration
├── ops.ps1 / ops.sh                # Operational Workflow CLI (sync, push, lint, test)
├── Dockerfile                      # Multi-stage production container build
└── docker-compose.yml              # Local multi-service container orchestration
```

---

## 3. Architecture Deep-Dive

### 3.1 Go High-Performance Gateway (`gateway/`)
Operating on Port `:8080`, the Go Gateway terminates external traffic, manages non-blocking HTTP Server-Sent Events (SSE), and isolates filesystem operations:
*   **SSE Stream Multiplexing**: Duplex event streams for autonomous loops (`/api/autopilot`) and long-running background tasks (`/api/tasks/`) bypass Python thread bottlenecks.
*   **Thread-Safe Event Ledger**: In-memory ring buffer holding recent webhook events with concurrent mutex synchronization (`/api/webhooks`).
*   **Parallel Directory Traversal**: Fast multi-threaded workspace tree scanner (`/api/workspace/tree`) and traversal-protected file writer (`/api/workspace/write`).

### 3.2 C++20 Native Accelerator (`native/`)
Compiled into `libflux_core.so` (Linux) / `flux_core.dll` (Windows), this module delivers sub-millisecond execution for performance-critical kernels:
*   **Vector Dot Product (`flux_fast_vector_dot`)**: High-speed floating-point vector products for RAG embedding retrieval and cosine similarity.
*   **Memory Difference Distance (`flux_diff_distance`)**: Rapid character- and block-level diff calculation for real-time code mutation tracking.
*   **Canonical Path Barrier (`flux_sandbox_verify_path`)**: Realpath normalization ensuring all agent-generated filesystem operations remain strictly bounded within the authorized workspace.
*   **Transparent ABI Bridge**: Python integrates via `ctypes` in `engine/app/core/native_bridge.py` with zero overhead and automatic fallback to pure Python if the binary is uncompiled.

### 3.3 Python Cognitive Kernel Engine (`engine/`)
Operating on Port `:8000`, Python remains the central cognitive brain:
*   **`agentic_loop.py`**: The autonomous nucleus executing planning, code generation, verification, and automated bug-fixing cycles.
*   **`code_executor.py`**: Multi-language execution sandbox supporting Python, native Go, and modern C++20. All JavaScript/TypeScript runners have been purged.
*   **`llm_router.py`**: Dynamic model routing evaluating prompt complexity, context sizes, and cost/latency constraints.
*   **`file_manager.py` & `os_controller.py`**: Workspace modification tools gated by native path validation.

### 3.4 Sovereign Embedded Web Console (`gateway/internal/ui/`)
Embedded directly inside the Go Gateway binary, the Web Console serves as a zero-JS, high-security operational surface:
*   **Zero-JS Enterprise Compliance**: Operates purely on Go standard library `html/template`, HTML5 semantic forms, and HTTP 303 post-redirect-get state transitions. Zero external JS bundles, zero CDN dependencies.
*   **Minimalist Light/Dark/System Theming**: Clean white/slate FAANG internal tool aesthetic with default Light mode, native Dark mode, and OS-synchronized System mode.
*   **Dynamic Workspace In-Place File Editor**: Inspect, edit, and create workspace files directly with automatic pre-mutation safety snapshots and C++ sandbox validation.
*   **Autonomous Batch Diff Review Gate**: Visualizes agent-generated changes via a high-performance LCS unified diff viewer with 1-click **Approve & Merge** or **Reject & Rollback** controls.

---

## 4. Operational Workflow CLI (`ops.ps1` / `ops.sh`)

FluxKernel provides cross-platform operational scripts to automate formatting, testing, rebasing, and pushing without requiring global software installations:

```bash
# Windows (PowerShell)
.\ops.ps1 sync                  # Fetch origin/main and rebase cleanly
.\ops.ps1 push "feat: message"  # Lint, test, commit, auto-rebase, and push
.\ops.ps1 lint                  # Format Go (gofmt) and Python (ruff)
.\ops.ps1 test                  # Execute Go, C++, and Python test suites
.\ops.ps1 clean                 # Clean build artifacts and __pycache__

# Linux / macOS (Bash)
./ops.sh sync
./ops.sh push "feat: message"
./ops.sh lint
./ops.sh test
./ops.sh clean
```

---

## 5. Deployment Protocol

### Local Multi-Container Stack (Docker Compose)
Boot the complete isolated environment (PostgreSQL, Redis, Go Gateway, Python Engine, Celery Worker):

```bash
docker-compose up --build -d
```

### Manual Host Ingress

1. **Start Go Gateway (`:8080`)**:
   ```bash
   cd gateway
   go run ./cmd/server
   ```

2. **Start Python Kernel Engine (`:8000`)**:
   ```bash
   cd engine
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access Sovereign Console (`:8080`)**:
   Open `http://localhost:8080/dashboard` in any web browser.

---

## 6. Continuous Integration (CI/CD)

The GitHub Actions pipeline ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) validates every push across multiple matrix environments:
*   **Go Matrix**: Validates `gofmt`, `go vet`, compilation, and race-detector test suite on Go 1.22 and Go 1.23.
*   **C++ Matrix**: Configures CMake and compiles with GCC-13 and Clang-17 under `-std=c++20`, running CTest.
*   **Python Matrix**: Lints and formats with Ruff, installs dependencies, and runs `pytest` across all test suites.
*   **Docker Multi-Stage Build**: Compiles the unified container image verifying end-to-end integration.

---

## 7. License Directives

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
  <strong>Voxion Labs</strong> · Autonomous Engineering · Agentic AI · Go · C++20 · Python
</div>
