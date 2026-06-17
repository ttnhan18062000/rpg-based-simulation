---
status: historical
layer: engine
authority: P2
audience: developer
---

# Gap Audit: Phase 7 Action/Update Substrate

## 1. Executive Summary

This audit evaluates the `src` engine against the Milestone 2 requirement for an "Authoritative Action and Typed Update Substrate". While `StateUpdate` and `EntityUpdate` provide a strong foundation for authoritative mutation, the lack of an explicit `ActionProposal` (Intent) model creates structural drift and makes the substrate semantically fuzzy.

## 2. Implementation Status (Ledger Mapping)

| Ledger ID | Requirement | Status | Gap Reference |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-001** | Action intent-to-update convergence | **PARTIAL** | See Gap A, C |
| **LEG-RPG-004** | Typed authoritative update buckets | **STABLE** | Disaggregation debt remains (Gap D) |
| **LEG-RPG-006** | Conflict resolution preserves authoritative | **PARTIAL** | Blocked by missing Intent model |

## 3. Detailed Gap Analysis

### Gap A: Missing Intent Model (`ActionProposal`)
- **Location**: `src/core/` (Missing), `src/actions/` (Missing)
- **Problem**: Workers return `EntityUpdate` (Side Effects) but do not produce an `ActionProposal` (Intent).
- **Required**: Implement a strictly typed `ActionProposal` class containing `ActorID`, `Verb`, `Target`, and `Reason`.

### Gap B: Missing Normalization (`ActionReason`)
- **Location**: `src/core/updates.py`
- **Problem**: `EntityUpdate` lacks a `reason` field. Replay auditing cannot explain *why* a mutation occurred (e.g., "ADVANCING", "COLLISION", "HARVEST_START").
- **Required**: Port the `ActionReason` enum and logic from legacy to `src/core/enums.py` or similar.

### Gap C: Structural Drift (Kernel-side Routing)
- **Location**: `src/engine/kernel.py:L283-L334`
- **Problem**: The `Kernel` is performing "Intent Routing" for Movement and Interaction logic during the `RESOLUTION` phase.
- **Impact**: This violates the V2 principle that worker thought emits intent. The Kernel should only be responsible for *applying* intent, not generating it.
- **Required**: Move this logic to worker-side Action Proposals.

### Gap D: Disaggregation Debt (Flat Fields)
- **Location**: `src/core/updates.py:L55-L70`
- **Problem**: `EntityUpdate` contains flat fields like `new_position`, `moved_this_tick`, and `readiness_delta`.
- **Impact**: These should be disaggregated into domain-specific buckets (e.g., `SpatialUpdate`) to maintain strict boundary safety.
- **Required**: Refactor `EntityUpdate` to use typed domain buckets for all fields.

## 4. Implementation Checklist for Milestone 2

- [ ] **Task 2**: Create `src/core/actions.py` with `ActionProposal`.
- [ ] **Task 3**: Refactor `EntityUpdate` for full disaggregation.
- [ ] **Task 4**: Implement `src/core/reason.py` (Structured Reason).
- [ ] **Task 5**: Refactor `Kernel._phase_resolution` to remove implicit routing.
- [ ] **Task 6**: Add direct contract tests for the new substrate models.
