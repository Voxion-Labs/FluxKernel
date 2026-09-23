<div align="center">
  <img src="assets/logo/fluxkernel-glyph-dark.svg" alt="FluxKernel Logo" width="160" />
</div>

<br>

# <div align="center">FluxKernel</div>
### <div align="center">Voxion Labs Autonomous Engineering Kernel & Operating System</div>

<div align="center">

![Architecture](https://img.shields.io/badge/Architecture-Autonomous%20Agentic%20Loop-39ff8a?style=for-the-badge)
![Kernel](https://img.shields.io/badge/Kernel-Python%20%7C%20FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Interface](https://img.shields.io/badge/Interface-Next.js%20%7C%20React-000000?style=for-the-badge&logo=next.js&logoColor=white)
![Security](https://img.shields.io/badge/Security-Strict%20Sandbox-ffcc00?style=for-the-badge)
![License](https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge)

</div>

---

## 1. Executive Abstract

**FluxKernel** is a proprietary, full-stack autonomous AI engineering environment and cognitive operating system engineered exclusively by Voxion Labs. 

Standard large language model (LLM) implementations function as stateless, localized chat wrappers requiring constant human orchestration and context injection. FluxKernel abandons this paradigm. It operates as a stateful, agentic operating system capable of executing complex software architecture tasks independently. By bridging a highly deterministic Python execution kernel with a low-latency Next.js command matrix, the system achieves physical agency over its host environment. 

FluxKernel is capable of direct operating system control, arbitrary script compilation, dynamic software package management, and long-term memory retrieval via Vectorized Retrieval-Augmented Generation (RAG).

---

## 2. Infrastructure Topology

FluxKernel operates on a strictly bifurcated monorepo architecture to guarantee execution stability, fault isolation, and cognitive scaling. The environment is partitioned into the **Kernel Engine** (Cognitive Backend) and the **Frontend** (Command Matrix), coordinated via localized Docker containers.

```text
FluxKernel/
├── .github/
│   ├── deploy-frontend.yml         # CI/CD pipelines for Next.js surface
│   └── deploy-kernel.yml           # CI/CD pipelines for Python engine
├── assets/
│   └── architecture/
│       ├── database-schema.md      # Relational and vector schemas
│       ├── system-design.drawio    # Top-level execution topology
│       └── tool-flow-diagram.png   # Tool routing execution flow
├── frontend/                       # Next.js Command Matrix
│   ├── src/app/api/                # Localized proxy routes
│   └── package.json
├── kernel-engine/                  # Python Cognitive Backend
│   ├── app/core/                   # Agentic logic, RAG, and Security
│   ├── app/tools/                  # Physical execution arsenal
│   └── requirements.txt        
└── docker-compose.yml              # Local container orchestration
```

---

## 3. The Kernel Engine (Cognitive Backend)

Located entirely within the `/kernel-engine` directory, this Python-based environment handles all LLM routing, contextual memory processing, and dangerous physical executions. It exposes a strictly typed FastAPI surface for the frontend to consume.

### 3.1 Core Cognitive Modules (`app/core/`)
*   **`agentic_loop.py`**: The absolute nucleus of FluxKernel. It orchestrates continuous, multi-step autonomous reasoning cycles. It evaluates task completion probabilities, selects appropriate tools, handles error recovery, and determines execution termination without human intervention.
*   **`llm_router.py`**: A deterministic evaluation layer that intercepts system prompts and routes them to optimal local or remote LLM endpoints based on task complexity, token constraints, and latency requirements.
*   **`project_rag.py` & `memory.py`**: The persistent contextual awareness layer. It maintains vectorized embeddings of the operator's entire workspace. This ensures the agentic loop semantically understands the codebase hierarchy before executing targeted mutations.
*   **`security.py`**: Hardened execution constraints preventing the loop from initiating recursive token-burn cycles or accessing unauthorized host-level directories.
*   **`persona_engine.py`**: A dynamic system-prompt injection module allowing the kernel to seamlessly shift between operational directives (e.g., Ruthless Refactoring, UI Polishing, Security Auditing).

### 3.2 Execution Arsenal (`app/tools/`)
The cognitive loop relies on a strictly defined arsenal of execution tools, granting the AI physical agency over the host system.
*   **`code_executor.py`**: Compiles and executes arbitrary scripts in an isolated subprocess to validate logic before committing changes to the primary workspace.
*   **`os_controller.py`**: Provides direct interface capabilities with the host operating system for directory traversal, process management, and shell command execution.
*   **`file_manager.py`**: Enables high-precision read/write operations, AST parsing, and codebase mutations based on RAG context.
*   **`software_manager.py`**: Grants the kernel autonomy over dependency installation, package updates, and environment configuration.
*   **`web_fetcher.py`**: Facilitates real-time documentation ingestion, API scraping, and external knowledge integration.
*   **`voice_engine.py` & `image_gen.py`**: Multimodal generation capabilities integrated directly into the operator's command workflow.

### 3.3 Backend Telemetry Snippet
The FastAPI engine initializes via `app/main.py`, binding the core loop to WebSocket streams for real-time telemetry:

```python
# kernel-engine/app/main.py (Architecture Abstraction)
from fastapi import FastAPI, WebSocket
from app.core.agentic_loop import initialize_autonomous_loop

app = FastAPI(title="FluxKernel Cognitive Engine")

@app.websocket("/ws/telemetry")
async def telemetry_stream(websocket: WebSocket):
    await websocket.accept()
    # Continuous stream of autonomous decision trees to the command matrix
    await initialize_autonomous_loop(telemetry_socket=websocket)
```

---

## 4. The Command Matrix (Frontend Interface)

Located within the `/frontend` directory, the Next.js/React interface acts as a high-fidelity, low-latency control deck for the human operator. It is completely stateless regarding AI processing, acting solely as a visualizer and manual override trigger.

### 4.1 Workspace Visualization & Synchronization
*   **`components/workspace/FileExplorer.tsx`**: Real-time virtual representation of the host directory, synchronizing live as the kernel manipulates files.
*   **`components/workspace/BatchDiffViewer.tsx`**: High-precision graphical interfaces for reviewing kernel-generated codebase mutations before authorizing a final merge.

### 4.2 Code Integration & Telemetry
*   **`components/chat/MonacoEditor.tsx`**: Deep browser-level integration of the Monaco execution environment, providing native syntax highlighting, algorithmic validation, and inline code interaction while the agent operates.
*   **`hooks/useTaskStream.ts`**: The core telemetry pipeline monitoring continuous autonomous execution.
*   **`components/AutoPilotToggle.tsx`**: The physical trigger that shifts the kernel from synchronous chat mode into the asynchronous, continuous `agentic_loop.py`.

### 4.3 Decentralized State Management
To prevent UI blocking during heavy kernel processing, the frontend relies on strict client-side state handling via Zustand (`src/store/`):
*   **`useFluxStore.ts`**: Global operational state, tracking active processes and socket connections.
*   **`usePersonaStore.ts`**: Synchronizes the frontend UI with the active cognitive framework of the backend.

---

## 5. Deployment & Execution Protocol

FluxKernel requires a strict initialization sequence. The Python kernel MUST be fully operational, and the localized Docker networks must be established before the Next.js interface attempts initialization.

### Step 1: Environment Configuration
The kernel requires dedicated paths and API keys to establish its vectorized memory and tool routing.

```bash
cd kernel-engine
cp .env.example .env
```

*Example `kernel-engine/.env` Configuration:*
```env
APP_ENV=production
# Vector Database & Memory
POSTGRES_URL=postgresql://flux:flux@localhost:5432/flux_memory
REDIS_URL=redis://localhost:6379/0
# Cognitive Routing
OPENAI_API_KEY=sk_...
ANTHROPIC_API_KEY=sk_...
# Sandbox Parameters
WORKSPACE_ROOT=/absolute/path/to/isolated/workspace
MAX_AUTONOMOUS_ITERATIONS=50
```

### Step 2: Infrastructure Initialization
FluxKernel relies on Docker for process isolation and database hosting. The `docker-compose.yml` at the repository root establishes the Redis queues and PostgreSQL vector storage.

```bash
docker-compose up -d
```

### Step 3: Kernel Engine Ingress
Boot the FastAPI application to establish the cognitive backend and expose the telemetry websockets on Port 8000.

```bash
cd kernel-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 4: Command Matrix Ingress
Boot the Next.js operational interface on Port 3000 to bind with the Kernel Engine.

```bash
cd ../frontend
npm install
npm run dev
```

---

## 6. Continuous Integration (CI/CD)

FluxKernel utilizes strictly isolated deployment pipelines via GitHub Actions, located in `.github/`:
*   `deploy-kernel.yml`: Validates code execution logic, checks Python AST, and deploys the backend to the designated remote environment defined in `render.yaml`.
*   `deploy-frontend.yml`: Executes static analysis via `eslint.config.mjs`, validates TypeScript definitions (`tsconfig.json`), and deploys the Next.js interface per `vercel.json` directives.

---

## 7. Contribution Protocols

Due to the nature of FluxKernel's host-level agency (`os_controller.py`, `code_executor.py`), operational security (OpSec) is paramount. We do not accept unverified tool integrations, non-deterministic loop modifications, or unauthorized state mutations.

All developers must adhere to the strict Sandbox Isolation guidelines. 

**Read the full guidelines before submitting a Pull Request:**  
**[View Operational & Contribution Protocols](CONTRIBUTING.md)**

---

## 8. License Directives

This repository, its underlying autonomous logic, its agentic loop, and its architectural blueprints are classified proprietary intellectual property.

FluxKernel operates under the **Voxion Labs Proprietary Research License (VL-PRL)**. Open-source usage, commercial exploitation, reverse engineering, unauthorized public hosting, or distribution of the kernel engine or interface is strictly prohibited.

**Read the full proprietary license terms:**  
**[View Voxion Labs Proprietary Research License (VL-PRL)](LICENSE)**

---
<div align="center">
  <strong>Voxion Labs</strong> · Autonomous Engineering · Agentic AI · FastAPI · Next.js
</div>
