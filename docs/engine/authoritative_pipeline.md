---
status: active
layer: engine
authority: P1
audience: developer
---

# Authoritative Refinement Pipeline

> [!IMPORTANT]
> **The Singular Bottleneck Law**: All state transitions must pass through this pipeline. No system, worker, or external process may mutate the `AuthoritativeState` directly. All changes must be represented as a `StateUpdate` and refined through these 39 phases.

The `AuthoritativeApplyPipeline` ensures that concurrent "intents" from workers are resolved into a deterministic, causally-consistent state update.

## The 39 Phases of Refinement

Phase names match the `run_phase()` call identifiers in `src/engine/pipeline.py:refine()`. Phases may be skipped if their associated feature flag is disabled.

| # | Phase Name | Primary Responsibility |
| :--- | :--- | :--- |
| 1 | `trust_boundary` | Strips raw world-side effects from untrusted worker proposals (`RPG-AUTH-001`). |
| 2 | `actor_validity` | Rejects intents from dead, stunned, or incapacitated actors (`TOWN-001`). |
| 3 | `memory_update` | Enhanced RPG: updates causal/temporal/spatial memory from prior-tick trigger events (`ENABLE_MEMORY_UPDATE`). |
| 4 | `self_model` | Enhanced RPG: updates cognitive self-model (`ENABLE_SELF_MODEL_COGNITION`). |
| 5 | `information_belief` | Enhanced RPG: assimilates new information into entity belief state (`ENABLE_BELIEF_ASSIMILATION`). |
| 6 | `information_intent_execution` | Enhanced RPG: executes self-model query-routing intents via `ActionIntentAdapter.execute()` (`ENABLE_INFORMATION_INTENT_EXECUTION`). |
| 7 | `cooperation` | Enhanced RPG: resolves social cooperation contracts (`ENABLE_SOCIAL_COOPERATION`). |
| 8 | `contracts` | Expires stale social and legal contracts before system consumption. |
| 9 | `blacksmith` | Validates crafting/blacksmithing requirements and resource costs (`TOWN-155`). |
| 10 | `faction_awareness` | Updates faction tension from the prior tick's resource-related world events. |
| 11 | `diplomatic_transitions` | Resolves the diplomatic state machine and generates common-enemy alliance proposals (`E53Bc`/`E53Bd`). |
| 12 | `military_conflict` | Resolves military conflict outcomes between factions (`E53Ca`). |
| 13 | `action_routing` | Resolves combat, skills, and tactical ability interactions (`TOWN-149`). |
| 14 | `position_swaps` | Resolves adjacent position exchange contracts and mutual passing (`COMB-028`). |
| 15 | `movement_routing` | Calculates movement steps, terrain costs, and obstacle avoidance (`COMB-046`). |
| 16 | `combat_engagement` | Enhanced RPG: resolves full combat engagement sequences (`ENABLE_COMBAT_ENGAGEMENT`). |
| 17 | `interaction_routing` | Routes interaction intents to domain handlers (`TOWN-165`). |
| 18 | `interaction_enforcement` | Enforces harvesting, chest opening, and node usage rules. |
| 19 | `building_sabotage` | Resolves damage to buildings and town structures (`LEG-RPG-006`). |
| 20 | `town_resolution` | Updates regional influence, taxes, and town-level state (`TOWN-147`). |
| 21 | `gold_sink` | Injects fee/tax intents on `INFLATION_SPIRAL` windows (`E33C`). |
| 22 | `world_dynamics` | Resolves world-wide generation, respawns, and weather effects (`INFRA-001`). |
| 23 | `world_emergence` | Enhanced RPG: emergent world events and narrative triggers (`ENABLE_WORLD_EMERGENCE`). |
| 24 | `quest_rewards` | Authoritatively delivers quest rewards and completion markers (`PROG-084`). |
| 25 | `guild_visit` | Enhanced RPG: guild-visit arrival detection and quest-project completion (`ENABLE_GUILD_QUEST_GENERATION`). |
| 26 | `shop` | Enforces shop prices and trade legality (`TOWN-166`). |
| 27 | `paid_information` | Injects paid-information-transaction intents before the resolver runs (`E42C`). |
| 28 | `resource_transactions` | Enforces resource conservation and atomic transaction integrity. |
| 29 | `evolution` | Applies entity evolution and stat boosts. |
| 30 | `progression_conversion` | Enhanced RPG: converts progression points to levels/skills (`ENABLE_PROGRESSION_EVOLUTION`). |
| 31 | `strategic_intelligence` | Updates strategic blockers, leads, and project markers (`STRAT-002`). |
| 32 | `lead_contradiction` | Detects world-state-inconsistent leads (depleted resource, dead person, absent object, inactive event) and marks them EXHAUSTED with provider reliability penalty (`E42D`; `TCK-20260824-LEAD-CONTRADICTION-WIRING`). |
| 33 | `near_death_hardening` | Finalizes near-death state and damage-mitigation logic (`COMB-121`). |
| 34 | `occupancy_resolution` | Resolves spatial occupancy conflicts between entities. |
| 35 | `lifecycle` | Commits death and lifecycle status changes. |
| 36 | `groups` | Updates group membership and party composition. |
| 37 | `active_contracts` | Enforces active social and economic contract obligations. |
| 38 | `expired_offers` | Clears stale trade and social offers past their TTL. |
| 39 | `capacity_enforcement` | Final inventory and carrying-capacity enforcement pass. |

---

## Trust Boundary
**Logic ID**: `RPG-AUTH-001`  
**Responsibility**: Workers (LLMs/Systems) operate on snapshots and propose changes. This stage strips any "cheated" state changes (e.g., manually setting HP, adding Gold) and preserves only the core **Intents** (Navigation, Tasks, Interaction).

## Actor Validity
**Logic ID**: `TOWN-001`  
**Responsibility**: Enforces the status of the actor.
- **Law**: Dead entities cannot move or act.
- **Law**: Stunned or Frozen entities are blocked from submission.
- **Law**: Sleeping entities are blocked from submission.
- **Auditability**: All rejections are recorded in `rejections_delta` for auditability.

## Action Routing (Combat)
**Logic ID**: `TOWN-149`, `COMB-001`  
**File**: `src/engine/pipeline_phases/actions.py`  
**Responsibility**: Routes combat intents through `SimulationDomainLogic`.
- **Causal Rule**: Uses "Sliding State". If Actor A kills Target T in this tick, Actor B (later in the queue) will see T as dead and cannot receive a kill reward.

## 🏃 Locomotion Routing
**Logic ID**: `COMB-046`  
**File**: `src/engine/pipeline_phases/movement.py`  
**Responsibility**: Resolves physical movement steps, terrain traversal costs, and dynamic collision avoidance.
- **Spatial Locomotion Indexing**: To prevent O(N) entity collection scans during collision and proximity checks, this stage queries the spatial grid (`grid.get_entities_in_radius`) to evaluate local obstacles and adjacent entity interactions in O(K) time where K is local density.

## 🗺️ Ecological Dynamics
**Logic ID**: `INFRA-001`, `LEG-RPG-139`  
**File**: `src/engine/world_dynamics.py`  
**Responsibility**: Resolves macro-simulation laws.
- **Trauma Law**: Deaths increase regional trauma.
- **Sovereignty Law**: Influence shifts between Hero and Monster factions based on regional kills.

## 🧠 Cognitive Refinement
**Logic ID**: `STRAT-002`  
**File**: `src/systems/strategic_systems/intelligence.py`  
**Responsibility**: Updates the character's internal mental model.
- **Interruption Resistance**: Switching projects requires a score margin defined by `interruption_resistance * resistance_multiplier`.
- **Adjacent Phase**: The immediately following `lead_contradiction` phase (`E42D`) tests leads produced/refreshed here against current world state and marks the inconsistent ones EXHAUSTED — see `docs/mechanics/04_strategic_cognition.md` §3 for the mechanic itself.

---

## 🧪 Certification & Verification
Every phase is mapped to a specific test suite in `tests/engine/pipeline/`.
- **Proof of Determinism**: All phases must use the `StateUpdate.merge()` logic which is strictly additive or prefers "Authority" over "Proposal".
