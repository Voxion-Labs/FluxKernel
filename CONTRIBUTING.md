# FluxKernel Operational & Contribution Protocols

FluxKernel is an active, autonomous engineering system capable of executing arbitrary code via its OS Controller and Code Executor modules[cite: 3]. Therefore, operational security (OpSec) and architectural determinism are our highest priorities. 

We do not accept untested tool integrations, non-deterministic loop modifications, or unauthorized state mutations. 

If you have been authorized to submit a Pull Request, you must adhere strictly to the following directives.

## 1. Architectural Standards
* **Kernel Safety (Python):** Any modifications to `app/tools/code_executor.py` or `app/tools/os_controller.py`[cite: 3] must undergo strict sandbox validation. You must prove that your changes cannot escape the designated execution container.
* **Agentic Loop Integrity:** Modifications to `app/core/agentic_loop.py`[cite: 3] must mathematically guarantee termination. Infinite loops or recursive token-burn vulnerabilities will result in instant rejection.
* **Frontend Isolation:** The Next.js client (`frontend/src/`[cite: 3]) must remain a thin interface. It must not execute business logic or store raw LLM API keys. All cognitive processing remains strictly within the `kernel-engine`[cite: 3].

## 2. Pull Request (PR) Governance
1. **[TELEMETRY] Execution Data:** Provide benchmarks proving your changes do not increase token consumption or latency in the `llm_router.py`[cite: 3].
2. **[LOGIC] State Transition:** Document exactly how your code interacts with the existing `useFluxStore.ts` or `memory.py` layers[cite: 3].
3. **[ISOLATION] Threat Model:** Prove that new tools added to `app/tools/`[cite: 3] cannot be manipulated via Prompt Injection from untrusted user input.

*Note: PRs failing to provide empirical telemetry or violating sandbox isolation will be closed immediately.*

## 3. Vulnerability Disclosure
**DO NOT** open public issues for Prompt Injection bypasses, OS Controller sandbox escapes, or memory leaks. Public disclosure of critical threats to the autonomous engine compromises the integrity of Voxion Labs.
* All security reports must be routed internally to the Lead Architect.

## 4. Code of Conduct
We evaluate deterministic logic, sandbox security, and latency. Keep discussions clinical, objective, and exclusively focused on kernel-level architecture.