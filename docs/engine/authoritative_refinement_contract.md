# Authoritative Refinement Contract

This document defines the **Refinement** stage of the `src_v2` authoritative mutation pipeline.

## 1. Overview
Refinement is the process of transforming raw `ActionProposal` results into a consolidated, conflict-free `StateUpdate`. It is the "thought-to-authority" boundary where global invariants are enforced.

## 2. The 6-Phase Refinement Order
To ensure deterministic resolution, systems must be invoked in the following strict order:

1.  **Territorial & Service (Phase 1)**: `TownResolution`, `Shop`, `Blacksmith`.
2.  **World Dynamics (Phase 1.5)**: `WorldDynamics`, `BuildingSabotage`.
3.  **Interaction Intent (Phase 2)**: Intent routing for resource nodes.
4.  **Interaction Enforcement (Phase 3)**: Channeling and depletion logic.
5.  **Strategic Logic (Phase 4)**: Blocker resolution and redirection.
6.  **Movement & Occupancy (Phase 5/6)**: Path resolution and tile contention.

## 3. Responsibilities
- **Conflict Resolution**: Resolving multi-agent contention (e.g., two entities moving to the same tile).
- **Invariant Enforcement**: Ensuring that healing, trading, and harvesting obey world laws.
- **Intent Transformation**: Converting navigation targets into step-wise `EntityUpdate` records.

## 4. Orchestration Boundaries
- **Substrate Ownership**: Phase 7 owns the orchestration of all 6 phases.
- **Semantic Closure**: While Phase 7 owns the *orchestration* of Strategic modules, it does NOT own their *semantic depth*. These are "Mixed-Surface Dependencies" whose internal logic is owned by later phases.

## 5. Verification
- `src_v2/engine/pipeline.py`: Authoritative implementation.
- `tests_v2/engine/test_phase_order.py`: Order enforcement proof.
