<p align="center">
  <img src="assets/logo/fluxkernel-glyph-dark.svg" alt="FluxKernel Logo" width="160" />
</p>

# <p align="center">FluxKernel</p>
<h3 align="center">Voxion Labs Autonomous Engineering Kernel & Operating System</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Architecture-Autonomous%20Agentic%20Loop-39ff8a?style=for-the-badge" alt="Architecture" />
  <img src="https://img.shields.io/badge/Kernel-Python%20%7C%20FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Kernel" />
  <img src="https://img.shields.io/badge/Interface-Next.js%20%7C%20React-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Interface" />
  <img src="https://img.shields.io/badge/Security-Strict%20Sandbox-ffcc00?style=for-the-badge" alt="Security" />
  <img src="https://img.shields.io/badge/License-Proprietary-red.svg?style=for-the-badge" alt="License" />
</p>

---

## 1. Executive Abstract

**FluxKernel** is a proprietary, full-stack autonomous AI engineering environment and cognitive operating system developed exclusively by Voxion Labs. 

Standard large language model (LLM) implementations function as stateless chat wrappers requiring constant human orchestration. FluxKernel abandons this paradigm. It operates as a stateful, agentic operating system capable of executing complex software architecture tasks independently. By bridging a highly deterministic Python execution kernel with a low-latency Next.js command matrix, the system achieves physical agency. 

FluxKernel is capable of direct operating system control, arbitrary script compilation, dynamic software package management, and long-term memory retrieval via Vectorized Retrieval-Augmented Generation (RAG).

---

## 2. Architectural Topology

FluxKernel operates on a strictly bifurcated monorepo architecture to guarantee execution stability, fault isolation, and cognitive scaling. The environment is partitioned into the **Kernel Engine** (Cognitive Backend) and the **Frontend** (Command Matrix).

### 2.1 The Kernel Engine (Cognitive Backend)
Located entirely within the `/kernel-engine` directory, this Python-based environment handles all LLM routing, contextual memory processing, and dangerous physical executions.

#### Core Cognitive Modules (`app/core/`)
*   **`agentic_loop.py`**: The absolute nucleus of FluxKernel. It orchestrates continuous, multi-step autonomous reasoning cycles. It evaluates task completion probabilities, selects appropriate tools, handles error recovery, and determines execution termination without human intervention.
*   **`llm_router.py`**: A deterministic evaluation layer that intercepts system prompts and routes them to optimal local or remote LLM endpoints based on task complexity, token constraints, and latency requirements.
*   **`project_rag.py` & `memory.py`**: The persistent contextual awareness layer. It maintains vectorized embeddings of the operator's entire workspace. This ensures the agentic loop semantically understands the codebase hierarchy before executing targeted mutations.
*   **`persona_engine.py`**: A dynamic system-prompt injection module allowing the kernel to seamlessly shift between operational directives (e.g., Ruthless Refactoring, UI Polishing, Security Auditing) without dropping session state.
*   **`task_queue.py` & `data_analysis.py`**: Asynchronous processing pipelines for handling parallel execution threads and telemetry analysis during prolonged autonomous operations.

#### Execution Arsenal (`app/tools/`)
The cognitive loop relies on a strictly defined arsenal of execution tools, granting the AI physical agency over the host system.
*   **`code_executor.py`**: Compiles and executes arbitrary scripts in an isolated subprocess to validate logic before committing changes to the primary workspace.
*   **`os_controller.py`**: Provides direct interface capabilities with the host operating system for directory traversal, process management, and shell command execution.
*   **`software_manager.py`**: Grants the kernel autonomy over dependency installation, package updates, and environment configuration.
*   **`file_manager.py`**: Enables high-precision read/write operations, AST parsing, and codebase mutations based on RAG context.
*   **`web_fetcher.py`**: Facilitates real-time documentation ingestion, API scraping, and external knowledge integration.
*   **`voice_engine.py` & `image_gen.py`**: Multimodal generation capabilities integrated directly into the operator's command workflow.

#### API Routing & Handlers (`app/api/routes/`)
*   `autopilot.py`: Manages endpoints for initiating and terminating continuous agentic loops.
*   `chat.py`: Handles standard synchronous operator-to-kernel communication.
*   `files.py` & `tasks.py`: Endpoints for workspace synchronization and task state monitoring.
*   `personas.py`: Controls the active cognitive framework of the engine.

---

### 2.2 The Command Matrix (Frontend Interface)
Located within the `/frontend` directory, the Next.js/React interface acts as a high-fidelity, low-latency control deck for the human operator.

#### Workspace Visualization & Synchronization (`src/components/workspace/`)
*   **`FileExplorer.tsx`**: Real-time virtual representation of the host directory, synchronizing live as the kernel manipulates files.
*   **`BatchDiffViewer.tsx` & `DiffViewer.tsx`**: High-precision graphical interfaces for reviewing kernel-generated codebase mutations before authorizing a final merge.
*   **`ImageCanvas.tsx`**: Dedicated rendering surface for multimodal outputs generated by `image_gen.py`.

#### Code Integration & Telemetry (`src/components/chat/` & `hooks/`)
*   **`MonacoEditor.tsx`**: Deep browser-level integration of the Monaco execution environment, providing native syntax highlighting, algorithmic validation, and inline code interaction while the agent operates.
*   **`MessageStream.tsx` & `ModeSelector.tsx`**: The primary communication and state-switching UI for manual overrides.
*   **`useTaskStream.ts` & `AutoPilotToggle.tsx`**: The core telemetry pipeline monitoring continuous autonomous execution, allowing the operator to visualize the agent's thought process in real-time.

#### Decentralized State Management (`src/store/`)
To prevent UI blocking during heavy kernel processing, the frontend relies on strict client-side state handling.
*   **`useFluxStore.ts`**: Global operational state, tracking active processes and socket connections.
*   **`usePersonaStore.ts`**: Synchronizes the frontend UI with the active cognitive framework of the backend.
*   **`useWorkspaceStore.ts`**: Manages the virtual file tree and unsaved diff buffers locally.

#### Modular User Interface (`src/components/ui/`)
Constructed with Tailwind CSS, the platform utilizes strict, modular UI components (`dialog.tsx`, `scroll-area.tsx`, `toast.tsx`, `slider.tsx`) to maintain a polished, premium, and distraction-free aesthetic.

---

## 3. Deployment & Execution Protocol

FluxKernel requires a strict initialization sequence. The Python kernel MUST be fully operational and bound to its required ports before the Next.js interface attempts API or WebSocket handshakes.

### Phase 1: Environment Configuration
Copy environment templates and inject the required API keys, database connection strings, and strict sandbox paths.
```bash
cp kernel-engine/.env.example kernel-engine/.env
```

### Phase 2: Container Initialization
Boot the local PostgreSQL and Redis instances required for long-term memory vectorization and task queuing.
```bash
docker-compose up -d
```

### Phase 3: Kernel Engine Ingress
Initialize the cognitive loop, database models (`models.py`), and API routing layers.
```bash
cd kernel-engine
pip install -r requirements.txt
python app/main.py
```

### Phase 4: Command Matrix Ingress
Boot the Next.js operational interface.
```bash
cd ../frontend
npm install
npm run dev
```

---

## 4. Operational Security (OpSec) & Isolation

Given FluxKernel's ability to execute arbitrary code via `os_controller.py` and `code_executor.py`, operational security is paramount.
*   **Strict Containerization:** The engine must be executed within its designated Docker container to prevent catastrophic host-level degradation.
*   **Route Protection:** All Next.js API endpoints (`src/app/api/`) and Python routes (`app/api/routes/`) utilize strict CORS policies and localized payload validation to prevent cross-site request forgery (CSRF).
*   **Agentic Constraints:** The `security.py` module enforces strict boundary conditions on the `agentic_loop.py`, terminating processes that attempt to mutate unauthorized system directories or burn tokens in recursive loops.

---

## 5. Infrastructure Documentation

For a visual breakdown of the execution topology, database schemas, and tool workflows, refer to the internal documentation assets located in `assets/architecture/`:
*   **System Topology Diagram:** `system-design.drawio`
*   **Database Relational Schema:** `database-schema.md`
*   **Autonomous Tool Flow:** `tool-flow-diagram.png`

---

## 6. Continuous Integration (CI/CD)

FluxKernel utilizes strictly isolated deployment pipelines via GitHub Actions, located in `.github/`:
*   `deploy-kernel.yml`: Validates code execution logic, checks Python AST, and deploys the backend to the designated remote environment defined in `render.yaml`.
*   `deploy-frontend.yml`: Executes static analysis via `eslint.config.mjs`, validates TypeScript definitions (`tsconfig.json`), and deploys the Next.js interface per `vercel.json` directives.

---

## 7. License Directives

This repository, its underlying autonomous logic, its agentic loop, and its architectural blueprints are classified proprietary intellectual property.

FluxKernel operates under the **Voxion Labs Proprietary Research License (VL-PRL)**.
Open-source usage, commercial exploitation, reverse engineering, unauthorized public hosting, or distribution of the kernel engine or interface is strictly prohibited.

The full license text is available in the `LICENSE` file.

---
<p align="center">
  <strong>Voxion Labs</strong> · Autonomous Engineering · Agentic AI · RAG · FastApi · Next.js
</p>