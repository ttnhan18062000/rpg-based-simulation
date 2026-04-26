# Phase 7 Entry Support Boundary: Substrate Hardening Initiation

## 1. Overview
This document defines the supported substrate boundary at the start of Phase 7. It formalizes the shift from generic "action" terminology to the implementation-backed **Task/Result/Update** model.

## 2. Supported Substrate Architecture

### A. Intent Model (Task/Work Packets)
- **Scope**: Structured intent emitted by worker-side logic.
- **Contract**: Tasks carry `NavigationComponent` and `TaskComponent` requirements. Untyped `properties` are officially retired for authoritative use.
- **Verification**: `tests/core/test_intent_model.py`

### B. Resolution Model (Worker Results)
- **Scope**: Deterministic output of semantic executors (e.g., Strategic, Movement).
- **Contract**: Results must emit explicit `EntityUpdate` or `WorldUpdate` records. Direct mutation of `AuthoritativeState` is forbidden.
- **Verification**: `tests/engine/test_worker_isolation.py`

### C. Refinement Pipeline (Authoritative Refinement)
- **Scope**: Consolidation of results through the 6-phase authoritative tick.
- **Contract**: Phases execute in strict order: Town/Service -> Dynamics -> Interaction -> Strategic -> Movement -> Occupancy.
- **Verification**: `tests/engine/test_phase_order.py`

### D. Authoritative Apply (Outcome Truth)
- **Scope**: Single-point application of the refined `StateUpdate`.
- **Contract**: World truth is defined by the post-apply state, which is frozen and emitted for replay.
- **Verification**: `tests/engine/test_authoritative_apply.py`

## 3. Supported Gameplay Slice
- **Grid Movement**: Deterministic 8-way tile navigation.
- **Resource Interaction**: Channeled harvesting and inventory resolution.
- **Regional Dynamics**: Hazard drains and calamity scaling (New in Ph 7).
- **Evolution**: Threshold-based entity transformation (New in Ph 7).
- **Sabotage**: Building damage and service disruption (New in Ph 7).

## 4. Execution Integrity
- **Determinism**: Identical inputs/seeds produce bit-identical states.
- **Isolation**: State snapshots are deep-copied and immutable read-only surfaces.

---
*Created as part of Phase 7 Milestone 1 — Substrate Hardening Entry Gate.*
