# Runtime State Contract (M3) — Shape and Retention

## 1. Purpose
This document defines the structural laws for Milestone 3. It establishes the separation between hot-path models and non-authoritative concerns, and enforces bounded memory behavior for all long-lived containers.

## 2. Model Categories
The engine structurally separates models by their role to prevent bloat and high serialization costs.

### A. Hot-Path Runtime Models
- **Role**: Authoritative simulation logic.
- **Rules**:
    - Optimized for deterministic execution speed.
    - Use `dataclasses` with `slots=True`.
    - Avoid Pydantic or complex validation inside the core loop.
    - No diagnostic or non-authoritative payload.

### B. Export Models (DTOs)
- **Role**: Persistence, API, and cross-application transport.
- **Rules**:
    - Built *from* Runtime models via factory functions.
    - May use Pydantic for schema validation.
    - Not allowed to be used as authoritative state in the Kernel.

### C. Diagnostic Models
- **Role**: Observability, traces, and high-fidelity logging.
- **Rules**:
    - Strictly non-authoritative.
    - Buffered in separate containers with exact retention policies.

## 3. Long-Lived Retention Rules
No structure that persists across ticks may grow indefinitely.

### Overflow Policies
- `REJECT`: Fixed population. Fails to add new items when full. Default for Authoritative Registries.
- `EVICT_OLDEST`: Ring-buffer behavior. Removes the oldest entry. Default for logs and history windows.
- `COMPACT`: Summarizes the data (e.g., aggregating old metrics).

## 4. Boundedness Terminology
- **Capacity**: The hard upper limit (count, bytes, or age).
- **Owner**: The system or orchestrator responsible for the collection's lifecycle.
- **Provable Determinism**: Eviction and compaction must be bit-identical for the same seed/inputs.

## 5. Non-Goals
- Replay streaming.
- Resource governor (throttling).
- Performance tuning / micro-optimization.
- Observability system implementation (beyond the model split).
