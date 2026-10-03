---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260420-M1-CORE-FREEZE
artifact_type: investigation
tags: [m1, core, freeze]
---

# Investigation - Core Substrate Freeze (M1)

## Current State Analysis

### 1. Semantic Baseline (Kernel & Apply)
- `Kernel.py` implements a 6-phase authoritative loop: `INIT` -> `SCHEDULING` -> `COLLECTION` -> `RESOLUTION` -> `CLEANUP` -> `ADVANCEMENT`.
- A 7th phase `PERSISTENCE` is explicitly marked as non-authoritative.
- `ApplyPath.apply_generation` is the singular entry point for authoritative mutation. It uses immutable transitions (`replace`).
- Determinism is achieved via explicit sorting of entity IDs, resource keys, etc., before application.

### 2. Operational Vocabulary (Signals & Status)
- `PressureSignals` (in `core/governance.py`) contains: `tick_compute_ms`, `work_debt_total`, `worker_utilization`, `queue_utilization`, `memory_estimate_mb`, `replay_backlog_kb`, `active_workers`, `dropped_work_delta`.
- `RuntimeStatus` (in `engine/runtime_status.py`) manages mode transitions and history.
- `LifecycleOutcome` (in `core/lifecycle.py`) defines `SUCCESS`, `PARTIAL`, `FAILED`, `SKIPPED`.

### 3. Documentation Drift
- `runtime_completion_contract_ma.md` is marked "FINALIZED / CLOSED" but references "Milestone A". It needs to be updated to reflect its role as the foundation for "Phase 4 - Gameplay Attachment".
- `project_lawbook_m10.md` lists various contracts but might need alignment with the new "Milestone 1-5" revised phase structure.

### 4. Remaining Transitional Leftovers
- `Kernel._get_deterministic_neighbor_view` has a comment about being a prototype. It should be reviewed for "freeze" readiness.
- Need to check if any `TODO` or `pass` blocks remain in `Kernel.py` or `Apply.py` that affect authoritative logic.

## Findings
- The substrate is indeed 100% authoritative now, thanks to recent hardening.
- The "Freeze" is primarily a documentation and "lock" task, plus adding guardrails to prevent future drift.

## Potential Risks
- If we miss a signal that gameplay needs for governance, adding it later will break the "Freeze" contract.
- If the `NeighborView` logic is too slow, we might be tempted to "fix" it during gameplay work, which violates the freeze. We should ensure it's "good enough" for the first slice (Movement).
