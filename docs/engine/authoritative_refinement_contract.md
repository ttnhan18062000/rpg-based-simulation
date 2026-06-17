---
status: active
layer: engine
authority: P1
audience: developer
---

# Authoritative Refinement Contract

This document defines the **Refinement** stage of the `src` authoritative mutation pipeline.

## 1. Overview
Refinement is the process of transforming raw `ActionProposal` results into a consolidated, conflict-free `StateUpdate`. It is the "thought-to-authority" boundary where global invariants are enforced.

## 2. The Refinement Order
To ensure deterministic resolution, systems must be invoked in the following strict order:

1.  **Territorial & Service**: `TownResolution`, `Shop`, `Blacksmith`.
2.  **World Dynamics**: `WorldDynamics`, `BuildingSabotage`.
3.  **Interaction Intent**: Intent routing for resource nodes.
4.  **Interaction Enforcement**: Channeling and depletion logic.
5.  **Strategic Logic**: Blocker resolution and redirection.
6.  **Movement & Occupancy**: Path resolution and tile contention.

## 3. Responsibilities
- **Conflict Resolution**: Resolving multi-agent contention (e.g., two entities moving to the same tile).
- **Invariant Enforcement**: Ensuring that healing, trading, and harvesting obey world laws.
- **Intent Transformation**: Converting navigation targets into step-wise `EntityUpdate` records.

## 4. Orchestration Boundaries
- **Substrate Ownership**: The Locomotion Routing stage owns the orchestration of all refinement steps above.
- **Semantic Closure**: While the Locomotion Routing stage owns the *orchestration* of Strategic modules, it does NOT own their *semantic depth*. These are "Mixed-Surface Dependencies" whose internal logic is owned by later stages.

## 5. Verification
- `src/engine/pipeline.py`: Authoritative implementation.
- `tests/engine/test_phase_order.py`: Order enforcement proof.
