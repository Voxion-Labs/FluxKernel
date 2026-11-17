# FluxKernel Sandboxed Workspace

Welcome to the **FluxKernel Sandboxed Workspace**. This directory is the isolated execution environment where the autonomous agent operates.

### Security & State Boundaries
- **Strict Realpath Sandboxing**: All read/write and execution tasks are cryptographically verified and constrained within this folder.
- **Atomic Snapshot & Rollback**: Every state mutation is automatically snapshotted. You can revert any mutation instantly using the Rollback Engine.
- **Protected Partitions**: Internal engine structures (`.flux_snapshots`, `.flux_temp`, `.git`) are isolated and protected against unauthorized mutations.

---
*Voxion Labs Autonomous Engineering Kernel — Isolated Workspace Runtime*
