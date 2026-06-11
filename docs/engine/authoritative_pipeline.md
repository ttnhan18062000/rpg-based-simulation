---
status: active
layer: engine
authority: P1
audience: developer
---

# Authoritative Refinement Pipeline

> [!IMPORTANT]
> **The Singular Bottleneck Law**: All state transitions must pass through this pipeline. No system, worker, or external process may mutate the `AuthoritativeState` directly. All changes must be represented as a `StateUpdate` and refined through these 17 phases.

The `AuthoritativeApplyPipeline` ensures that concurrent "intents" from workers are resolved into a deterministic, causally-consistent state update.

## The 17 Phases of Refinement

| Phase | Name | Logic ID | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| 1 | **Trust Boundary** | `RPG-AUTH-001` | Strips raw world-side effects from untrusted worker proposals. |
| 2 | **Actor Validity** | `TOWN-001` | Rejects intents from dead, stunned, or incapacitated actors. |
| 3 | **Contract Lifecycle** | `SOC-182` | Expires stale social and legal contracts before system consumption. |
| 4 | **Production Enforcement** | `TOWN-155` | Validates crafting/blacksmithing requirements and resource costs. |
| 5 | **Action Routing** | `TOWN-149` | Resolves combat, skills, and tactical ability interactions. |
| 6 | **Spatial Swaps** | `COMB-028` | Resolves adjacent position exchange contracts and mutual passing. |
| 7 | **Locomotion Routing** | `COMB-046` | Calculates movement steps, terrain costs, and obstacle avoidance. |
| 8 | **Task Translation** | `TOWN-164` | Converts high-level `ENTITY_ACT` tasks into low-level intents. |
| 9 | **World Interaction** | `TOWN-165` | Enforces rules for harvesting, chest opening, and node usage. |
| 10 | **Combat Hardening** | `COMB-121` | Finalizes near-death state and damage-mitigation logic. |
| 11 | **Infrastructure Sabotage** | `LEG-RPG-006` | Resolves damage to buildings and town structures. |
| 12 | **Town Governance** | `TOWN-147` | Updates regional influence, taxes, and town-level state. |
| 13 | **Ecological Dynamics** | `INFRA-001` | Resolves world-wide generation, respawns, and weather effects. |
| 14 | **Objective Reward** | `PROG-084` | Authoritatively delivers quest rewards and completion markers. |
| 15 | **Economic Enforcement** | `TOWN-166` | Enforces shop prices, trade legality, and inventory capacity. |
| 16 | **Cognitive Refinement** | `STRAT-002` | Updates strategic blockers, leads, and project markers. |
| 17 | **Final Integrity** | `TOWN-167` | Resolves remaining occupancy conflicts and lifecycle status (death). |

---

## Phase 1: Trust Boundary
**Logic ID**: `RPG-AUTH-001`  
**Responsibility**: Workers (LLMs/Systems) operate on snapshots and propose changes. This phase strips any "cheated" state changes (e.g., manually setting HP, adding Gold) and preserves only the core **Intents** (Navigation, Tasks, Interaction).

## Phase 2: Actor Validity
**Logic ID**: `TOWN-001`  
**Responsibility**: Enforces the status of the actor.
- **Law**: Dead entities cannot move or act.
- **Law**: Stunned or Frozen entities are blocked from submission.
- **Law**: Sleeping entities are blocked from submission.
- **Auditability**: All rejections are recorded in `rejections_delta` for auditability.

## Phase 5: Action Routing (Combat)
**Logic ID**: `TOWN-149`, `COMB-001`  
**File**: `src/engine/pipeline_phases/actions.py`  
**Responsibility**: Routes combat intents through `SimulationDomainLogic`.
- **Causal Rule**: Uses "Sliding State". If Actor A kills Target T in this tick, Actor B (later in the queue) will see T as dead and cannot receive a kill reward.

## 🏃 Phase 7: Locomotion Routing
**Logic ID**: `COMB-046`  
**File**: `src/engine/pipeline_phases/movement.py`  
**Responsibility**: Resolves physical movement steps, terrain traversal costs, and dynamic collision avoidance.
- **Spatial Locomotion Indexing**: To prevent O(N) entity collection scans during collision and proximity checks, the locomotion phase queries the spatial grid (`grid.get_entities_in_radius`) to evaluate local obstacles and adjacent entity interactions in O(K) time where K is local density.

## 🗺️ Phase 13: Ecological Dynamics
**Logic ID**: `INFRA-001`, `LEG-RPG-139`  
**File**: `src/engine/world_dynamics.py`  
**Responsibility**: Resolves macro-simulation laws.
- **Trauma Law**: Deaths increase regional trauma.
- **Sovereignty Law**: Influence shifts between Hero and Monster factions based on regional kills.

## 🧠 Phase 16: Cognitive Refinement
**Logic ID**: `STRAT-002`  
**File**: `src/systems/strategic_systems/intelligence.py`  
**Responsibility**: Updates the character's internal mental model.
- **Interruption Resistance**: Switching projects requires a score margin defined by `interruption_resistance * resistance_multiplier`.

---

## 🧪 Certification & Verification
Every phase is mapped to a specific test suite in `tests/engine/pipeline/`.
- **Proof of Determinism**: All phases must use the `StateUpdate.merge()` logic which is strictly additive or prefers "Authority" over "Proposal".
