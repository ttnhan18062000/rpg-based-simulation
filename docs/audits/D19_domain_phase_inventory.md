---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, domain-phases, pipeline, feature-inventory, wiring, domain-layer]
---

# D19 — Domain-Phase Inventory

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | 0 — Feature Inventory |
| **State** | `done` |
| **Impact** | 5 / 5 |
| **Interest** | 4 / 5 |
| **Priority** | 9 |
| **Method** | code-read |
| **Audit date** | 2026-06-27 |

**What this dimension answers:** Which domain-layer pipeline phases are live in the
authoritative pipeline, in what order they execute, whether each is always active or
behind a FeatureMode gate, and what a passing test would verify for each.

This document is the domain-phase counterpart to D02 (Foundation Feature Inventory).
D02 catalogued technical enabling capabilities (infrastructure, algorithms, data structures).
D19 catalogues the domain-level phases wired into `AuthoritativeApplyPipeline.refine()`
and `WorldDynamicsSystem.resolve_dynamics()` — the gameplay behavior layer that runs on
top of the D02 substrate.

**Source of this document:** D09 System Wiring Finding 3 (Risk 13/15) identified that
20+ live domain phases were invisible to current audit coverage. This document closes that gap.

**Related dimensions:**
- D09 (System Wiring) — Finding 3 is the direct source; wiring evidence cross-references D09
- D02 (Foundation Feature Inventory) — companion document for enabling capabilities
- D10 (Test Coverage) — use this inventory to identify which domain phases lack test coverage
- D14 (Coupling Depth) — domain phase ordering and cross-phase coupling
- D12 (Pattern Consistency) — domain phase authoring patterns

---

## Classification Method

Three wiring status labels per phase:

| Status | Meaning |
|---|---|
| `active` | Always in the call path; runs on every `refine()` invocation (subject to `PhaseDependencyGraph.should_run_phase()` cadence skip only) |
| `feature-gated` | Controlled by a `FeatureMode` flag; default is `ON` but can be set to `SHADOW` or `OFF` via `rollout_profile` or `feature_flags` state attribute |
| `cadence-gated` | Runs only when `should_run(state.tick, None, cadence.X)` is satisfied; always-active but fires every N ticks, not every tick |
| `direct-call` | Invoked outside the `run_phase()` mechanism; no FeatureMode check; result fed as input to downstream phases |

All `feature-gated` phases support SHADOW mode: the phase runs but its mutations are
discarded, keeping metric counters and diagnostic telemetry. This is the safe rollout path.

---

## Part A — Pipeline Phases (`pipeline.py:refine()`)

Phases are listed in execution order as they appear in `AuthoritativeApplyPipeline.refine()`.
Phase IDs use the format `PP-NN` (Pipeline Phase). The `run_phase` key is the string passed
to `run_phase()` and tracked in `metric_counters`.

### §1 — Trust & Validity

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-01 | `trust_boundary` | `TrustBoundaryPhase` | `src/engine/pipeline_phases/trust.py` | `active` | Strips untrusted world effects from the incoming `StateUpdate` before any domain logic runs. First gate in every refine cycle. | A `StateUpdate` carrying a fabricated world mutation from an untrusted caller has that mutation absent from the returned update. |
| PP-02 | `actor_validity` | `ActorValidityPhase` | `src/engine/pipeline_phases/actor_validity.py` | `active` | Resolves actor validity — confirms that entities requesting actions exist and meet lifecycle preconditions. | An update referencing a non-existent entity ID has that entity's updates discarded before downstream phases run. |

### §2 — Self Model Cognition (Enhanced RPG Phase 2)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-03 | `self_model` | `SelfModelUpdatePhase` | `src/cognition/self_model_phase.py` | `feature-gated` (flag: `ENABLE_SELF_MODEL_COGNITION`) | Updates each entity's self-model: internal state awareness used by downstream cognition phases. | With flag OFF the entity self-model state is unchanged between ticks; with flag ON the self-model reflects current vitals and resources. |

### §3 — Belief Assimilation (Enhanced RPG Phase 5)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-04 | `information_belief` | `InformationBeliefPhase` | `src/domains/information/phase.py` | `feature-gated + content-gated` (flag: `ENABLE_BELIEF_ASSIMILATION`; also requires non-empty `pending_information_responses` — Branch A — or `self_model.knowledge.unknowns` — Branch B, still dead) | Integrates pending information responses into entity belief state using source profile trust weights. | With flag ON **and** `pending_information_responses` populated, an entity assimilates a response and updates its belief store; with flag OFF or no pending responses, belief state is unchanged. Originally this criterion implicitly assumed the flag alone gated the effect — investigation (2026-07-03, `TCK-20260702-SIMQ-UPLIFT2-INFORMATION`/`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`) found the flag was necessary but not sufficient: `pending_information_responses` had zero writers anywhere in `src/`, and a separate `Kernel._phase_advancement()` tick-alignment bug meant even a populated response would never surface through the real live loop. Both gaps are now closed for Branch A in `urban_political` (compile-time `pending_information_responses` seed + kernel fix); Branch B (`self_model.knowledge.unknowns`, via `SelfModelUpdatePhase`) remains unwired. |

### §4 — Social Cooperation (Enhanced RPG Phase 7)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-05 | `cooperation` | `CooperationPhase` | `src/domains/cooperation/phase.py` | `feature-gated` (flag: `ENABLE_SOCIAL_COOPERATION`) | Executes cooperative social interactions: alliance checks, joint task formation, help offers. | With flag ON two compatible entities in range produce a cooperation outcome; with flag OFF no cooperation updates are emitted. |

### §5 — Contracts & Production (Phase 2)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-06 | `contracts` | `ContractLifecyclePhase` | `src/engine/pipeline_phases/contracts.py` | `active` | Resolves contract expiration: marks expired contracts as lapsed and removes them from active tracking. | A contract past its expiry tick is absent from state after the phase runs. |
| PP-07 | `blacksmith` | `BlacksmithSystem` | `src/engine/blacksmith.py` | `active` | Enforces blacksmith production: converts queued crafting intents into item outputs respecting material availability. | A crafting intent with sufficient materials produces the expected item in the entity's inventory. |

### §6 — Faction Decision (Enhanced RPG Phase 8b)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-08 | *(direct call)* | `FactionDecisionPhase` | `src/engine/faction_decision.py` | `direct-call` | Computes faction-level strategic directives for the current tick. Called outside `run_phase()`; result passed as `faction_directives` input to `adventure_decision`. Runs every tick without cadence or feature gate. | Given a faction with an active objective, `FactionDecisionPhase.execute()` returns at least one directive matching the objective kind. |

### §7 — Faction Awareness (Enhanced RPG Phase 8c)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-09 | `faction_awareness` | `FactionAwarenessService` | `src/engine/faction_decision.py` | `active` | Computes tension updates from last-tick world events (resource seizures, combat outcomes) and merges them into faction state. One-tick lag is inherent: state is frozen during refine. | A resource-seizure event from the prior tick produces a non-zero tension delta on the owning faction. |

### §8 — Diplomatic State Machine (Enhanced RPG Phase 8d)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-10 | `diplomatic_transitions` | `compute_transitions` + `compute_common_enemy_pairs` | `src/domains/faction/diplomatic_state_machine.py` | `active` | Advances the diplomatic state machine: computes relationship transitions (neutral → hostile → war) and generates alliance proposals for factions sharing a common enemy. | Two factions with shared hostile enemy receive an `AllianceProposal`; a faction pair at war whose relationship improves transitions to the correct diplomatic state. |

### §9 — Military Conflict (Enhanced RPG Phase 8e)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-11 | `military_conflict` | `MilitaryConflictPhase` | `src/engine/military_conflict.py` | `active` | Resolves faction-level military conflicts: determines battle outcomes between factions in contested regions. | Two factions at war in a contested region produce a combat outcome update; factions at peace produce none. |

### §10 — Adventure Routing (Enhanced RPG Phase 3)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-12 | `adventure_decision` | `AdventureDecisionPhase` | `src/domains/adventure/phase.py` | `feature-gated` (flag: `ENABLE_ADVENTURE_ROUTING`) | Routes entity adventure decisions: assigns adventure targets based on faction directives, opportunity availability, and entity goals. | With flag ON an entity with an active adventure goal and available opportunity produces a navigation intent toward the adventure target. |

### §11 — Action & Movement Routing (Phase 3)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-13 | `action_routing` | `ActionRoutingPhase` | `src/engine/pipeline_phases/actions.py` | `active` | Routes entity action intents to the correct handler: combat, gather, interact, rest, etc. | An entity with a `GATHER` intent targeting a node produces a resource harvest update; a `REST` intent produces a stamina regen update. |
| PP-14 | `position_swaps` | `MovementPhase` | `src/engine/pipeline_phases/movement.py` | `active` | Resolves simultaneous position swap conflicts: two entities attempting to occupy each other's current cell are arbitrated deterministically. | Two entities with crossing movement intents resolve to non-conflicting positions in tick order. |
| PP-15 | `movement_routing` | `MovementPhase` | `src/engine/pipeline_phases/movement.py` | `active` | Routes entity movement intents: validates legality via `LegalityServiceV2`, applies movement plan cache, emits navigation updates. | An entity with a valid movement intent moves to the target cell; an entity with an obstructed path remains in place. |

### §12 — Combat Engagement (Enhanced RPG Phase 4)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-16 | `combat_engagement` | `CombatEngagementPhase` | `src/domains/combat_engagement/phase.py` | `feature-gated` (flag: `ENABLE_COMBAT_ENGAGEMENT`) | Resolves entity-level combat: applies damage formula, durability decay, and tactical modifiers; emits combat outcome updates. | With flag ON two hostile entities in range produce combat updates with hp_delta applied; with flag OFF no combat updates are emitted. |

**Real fix, `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS`:** `PP-16`'s own
real `run_phase("combat_engagement", ...)` registration (`src/engine/pipeline.py`) previously
called `CombatEngagementPhase.apply(state)` **without** merging the result into the incoming,
already-accumulated `StateUpdate` (`u`) — every other phase in this same real chain that needs
to preserve prior phases' own output correctly calls `u.merge(...)` on its own real output; this
phase's own lambda never referenced `u` at all. Since `run_phase()`'s own real chaining logic
replaces the accumulated `update` wholesale with whatever the phase function returns, this meant
that whenever `combat_engagement` actually ran (flag `ON`, not skipped by dependency-graph
policy), **every** real `StateUpdate` produced by every earlier phase in that same tick —
including the real `action_routing`/`ATTACK`-dispatch phase and `movement_routing` — was
silently discarded, confirmed via live corpus A/B testing to deterministically suppress all
push-shaper combat events (`combat_engagement_started/ended`, `combat_resolved`, `combat_damage`,
`entity_killed`) to zero. Fixed with a one-line `u.merge(...)` addition, matching the file's own
already-established precedent (the `information_belief` phase's identical pattern). Real,
disclosed containment context: `ENABLE_COMBAT_ENGAGEMENT` defaults `OFF` and was never turned
`ON` in any of the 17 shipped SimQ calibration profiles at the time this bug was found — the
real, practical blast radius was zero on any currently-shipped configuration, but the bug was
real and would have silently affected any future scenario/test/profile that legitimately enabled
this flag.

### §13 — Interaction & World Effects (Phase 4)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-17 | `interaction_routing` | `InteractionPhase` | `src/engine/pipeline_phases/interactions.py` | `active` | Routes entity interaction intents (trade, talk, open chest) to the correct enforcement handler. | An entity with a `TRADE` interaction intent targeting a merchant produces a trade enforcement record consumed by PP-18. |
| PP-18 | `interaction_enforcement` | `InteractionSystem` | `src/engine/interaction.py` | `active` | Enforces interaction outcomes: validates preconditions, resolves trade transfers, updates relationship scores. | A valid trade interaction produces balanced item and gold transfers; an invalid interaction (inventory full) is rejected with no transfer. |
| PP-19 | `building_sabotage` | `BuildingSabotageSystem` | `src/engine/sabotage.py` | `active` | Resolves building sabotage actions: applies durability damage to targeted buildings and emits sabotage outcome events. | An entity with a sabotage intent targeting a building produces a durability-decrement update on that building. |

### §14 — Governance & Ecology (Phase 5)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-20 | `town_resolution` | `TownResolutionSystem` | `src/engine/town_resolution.py` | `active` | Resolves town-level governance: service demand, building production, population welfare. Cadence-gated internally via `SystemCadence`. Also reads `state.recent_world_events` (one-tick-lagged) for `PRODUCTION_ROLE_VACATED` events and increments a per-region `economic_vacancy_detected_region_<id>` metric counter (TCK-20260903-ECONOMIC-VACANCY-SIGNAL) -- purely additive, does not gate crafting. | A town with an active smithy and queued orders produces crafting output at the correct cadence tick. |
| PP-21 | `gold_sink` | `GoldSinkSystem` | `src/engine/gold_sink.py` | `active` | Injects fee/tax intents on `INFLATION_SPIRAL` pressure windows (E33C). Runs after `town_resolution` so service context is resolved. | When `INFLATION_SPIRAL` pressure is active a gold-fee intent is emitted; during normal pressure the phase emits nothing. |
| PP-22 | `world_dynamics` | `WorldDynamicsSystem` | `src/engine/world_dynamics.py` | `active` | Applies regional environmental effects, death-triggered trauma, ownership transitions, and cadence-gated macro world events (see Part B for sub-phase detail). | A live entity in a high-hazard region receives hazard drain each tick; a region with trauma > 50 increments hazard_level at the correct rate. |

### §15 — World Emergence (Enhanced RPG Phase 8)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-23 | `world_emergence` | `WorldEmergencePhase` | `src/domains/world_emergence/phase.py` | `feature-gated` (flag: `ENABLE_WORLD_EMERGENCE`) | Processes emergent world-level events from accumulated entity actions: reputation shifts, region mood, narrative triggers. | With flag ON a threshold of combat deaths in a region produces a `WorldEvent` entry of the appropriate category. |

### §16 — Economy & Evolution (Phase 6)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-24 | `quest_rewards` | `QuestRewardPhase` | `src/engine/pipeline_phases/quests.py` | `active` | Resolves quest completion rewards: XP grants, item drops, relationship bonuses for completed quest objectives. | An entity completing the final quest objective receives an XP grant and the configured item reward. |
| PP-25 | `shop` | `ShopSystem` | `src/engine/shop.py` | `active` | Enforces shop purchase and sell transactions: validates inventory capacity and gold, applies atomic transfers. | A shop purchase with sufficient gold removes the item from the shop and adds it to the buyer's inventory with balanced gold transfer. |
| PP-26 | `paid_information` | `PaidInformationTransactionSystem` | `src/engine/pipeline_phases/paid_information.py` | `active` | Enforces paid information transactions (E42C): validates payment, delivers information packets, records transaction provenance. | An entity purchasing a lead tip with sufficient gold receives the lead payload and incurs the gold debit. |
| PP-27 | `resource_transactions` | `ResourceTransactionPhase` | `src/engine/pipeline_phases/resources.py` | `active` | Resolves resource transfers: applies the atomic conservation law — every item transferred from one entity appears on another. | A harvest transfer adds resources to the entity and decrements the resource node by the same quantity; net conservation is zero. |
| PP-28 | `evolution` | `EvolutionSystem` | `src/engine/evolution.py` | `active` | Evaluates XP accumulation and applies level-up transitions, attribute point grants, and skill unlocks. | An entity accumulating enough XP crosses the level threshold and receives the correct attribute and skill awards per Mechanics Bible Ch.01. |

### §17 — Progression & Conversion (Enhanced RPG Phase 6)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-29 | `progression_conversion` | `ProgressionConversionPhase` | `src/domains/progression/phase.py` | `feature-gated` (flag: `ENABLE_PROGRESSION_EVOLUTION`) | Converts accumulated progression signals (skill usage, trait expression) into permanent character evolution updates. | With flag ON an entity with a fully expressed trait receives a permanent progression update; with flag OFF no conversion updates are emitted. |

### §18 — Cognitive & Final Integrity (Phase 7)

| Phase ID | `run_phase` key | Class / Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|---|
| PP-30 | `strategic_intelligence` | `StrategicIntelligenceSystem` | `src/systems/strategic.py` | `active` | Fused strategic pass: updates lead certainty, goal re-scoring, task assignment, and knowledge management for all entities. Cadence-gated internally. | An entity with a decayed lead certainty receives a re-evaluation; a new high-value lead replaces a lower-priority current goal when scoring crosses threshold. |
| PP-31 | `near_death_hardening` | `NearDeathHardeningPhase` | `src/engine/pipeline_phases/hardening.py` | `active` | Applies near-death survival hardening: entities below the death threshold receive a final survival check and minimum hp floor. | An entity whose hp_delta would set hp to 0 on a non-lethal event is instead set to 1 hp. |
| PP-32 | `occupancy_resolution` | `OccupancyPhase` | `src/engine/pipeline_phases/occupancy.py` | `active` | Resolves multi-entity occupancy conflicts: enforces capacity limits and arbitrates contested cell occupation. | Two entities attempting to move to a single-capacity cell result in exactly one entity occupying it; the other is displaced. |
| PP-33 | `lifecycle` | `LifecycleSystem` | `src/systems/lifecycle.py` | `active` | Resolves entity lifecycle transitions: death finalization, corpse creation, respawn scheduling, loot drop. On the aggregate `recent_deaths` pass, also invokes `EconomicVacancyService.check_and_emit` (`src/economy/vacancy.py`), which emits a `PRODUCTION_ROLE_VACATED` `WorldEvent` when a death leaves a region with zero living SHOPKEEPER/WORKER holders (TCK-20260903-ECONOMIC-VACANCY-SIGNAL). | An entity with `alive_set=False` in the update is finalized as dead with a corpse emitted and loot dropped per configuration. |
| PP-34 | `groups` | `GroupPhase` | `src/engine/pipeline_phases/groups.py` | `active` | Resolves group membership transitions: entities joining, leaving, or being expelled from groups based on social state. | An entity meeting group join criteria is added to the group roster; an entity violating group rules is expelled. |
| PP-35 | `active_contracts` | `ContractService` | `src/systems/social_systems/contracts.py` | `active` | Processes active social contracts: enforces ongoing obligations, tracks milestones, emits progress events. | An entity with an active delivery contract and the required item in inventory completes the milestone and receives the reward on schedule. |
| PP-36 | `expired_offers` | `ContractService` | `src/systems/social_systems/contracts.py` | `active` | Reaps expired contract offers that were never accepted: cleans up dangling offer records from state. | A contract offer past its acceptance deadline is removed from state with no residual obligation on either party. |
| PP-37 | `capacity_enforcement` | `CapacityEnforcementPhase` | `src/engine/pipeline_phases/capacity_enforcement.py` | `active` | Final capacity enforcement pass: ensures no entity or region exceeds defined capacity limits after all other phases run. | After a tick in which multiple entities attempt to enter a full region, total occupancy in that region does not exceed its capacity. |

### §1 Pipeline Phase Summary

| Status | Count | Phase IDs |
|---|---|---|
| `active` | 30 | PP-01–02, PP-06–07, PP-09–11, PP-13–15, PP-17–22, PP-24–28, PP-30–37 |
| `feature-gated` | 7 | PP-03, PP-04, PP-05, PP-12, PP-16, PP-23, PP-29 |
| `direct-call` | 1 | PP-08 (`faction_decision`) |
| **Total** | **38** | (37 via `run_phase` + 1 direct call) |

**Feature flags (default ON for all; configurable per `rollout_profile` or `feature_flags` state attribute):**

| Flag | Phase | Phase ID |
|---|---|---|
| `ENABLE_SELF_MODEL_COGNITION` | `self_model` | PP-03 |
| `ENABLE_BELIEF_ASSIMILATION` | `information_belief` | PP-04 |
| `ENABLE_SOCIAL_COOPERATION` | `cooperation` | PP-05 |
| `ENABLE_ADVENTURE_ROUTING` | `adventure_decision` | PP-12 |
| `ENABLE_COMBAT_ENGAGEMENT` | `combat_engagement` | PP-16 |
| `ENABLE_WORLD_EMERGENCE` | `world_emergence` | PP-23 |
| `ENABLE_PROGRESSION_EVOLUTION` | `progression_conversion` | PP-29 |

---

## Part B — World Dynamics Sub-Phases (`world_dynamics.py:resolve_dynamics()`)

`WorldDynamicsSystem.resolve_dynamics()` is itself wired as pipeline phase PP-22. It
contains an internal hierarchy of sub-phases. Sub-phase IDs use the format `WD-NN`.

### §B1 — Every-Tick Sub-Phases (no cadence gate)

| Sub-Phase ID | Service / Handler | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|
| WD-01 | `EnvironmentService` (hazard drain loop) | `src/world/environment.py` | `active` | Applies hazard damage to every living, active entity in a hazardous region each tick. | A living entity in a region with `hazard_level > 0` receives a negative hp_delta each tick equal to `calculate_hazard_drain(region, entity)`. |
| WD-02 | Death-triggered trauma (inline) | `src/engine/world_dynamics.py` L44–60 | `active` | Accumulates +1.0 trauma_delta on the region for every entity killed this tick. | Three entity deaths in the same region produce a `trauma_delta` of 3.0 in that region's `WorldUpdate`. |
| WD-03 | Ownership & calamity progression (inline) | `src/engine/world_dynamics.py` L62–94 | `active` | Transitions region ownership when influence crosses ±100; scales hazard_level when trauma > 50. | A region at influence +100 with a non-protector owner has `owner_faction_id` set to `HERO_GUILD`; trauma 51 increments `hazard_level` by 0.01. |
| WD-04 | `TransformationService` | `src/world/transformation.py` | `active` | Checks each region for a potential type transformation (e.g. PLAINS → CORRUPTED) and emits `kind_set` if a threshold is crossed. | A region meeting the transformation precondition for its current kind emits a `kind_set` targeting the next region type. |
| WD-05 | Node cooldown / recharge (inline) | `src/engine/world_dynamics.py` L169–181 | `active` | Decrements cooldown on depleted resource nodes; restores `max_charges` when cooldown reaches 0. | A node at `cooldown_remaining=1` has `cooldown_set=0` and `charges_delta=max_charges` in its update; at `cooldown_remaining=3` only decrements by 1. |
| WD-06 | Chest cooldown (inline) | `src/engine/world_dynamics.py` L184–188 | `active` | Decrements cooldown on looted chests each tick. | A chest at `cooldown_remaining=2` has `cooldown_set=1` in its update after one tick. |
| WD-07 | Corpse decay (inline) | `src/engine/world_dynamics.py` L191–195 | `active` | Adds corpses past their `decay_tick` to the removal list. | A corpse with `decay_tick <= state.tick` appears in `corpses_remove`; one with `decay_tick > state.tick` does not. |

### §B2 — Cadence-Gated Sub-Phases (`should_run(state.tick, None, cadence.world_dynamics)`)

These sub-phases run only on ticks where the world_dynamics cadence fires. They are
`tick-live` (reachable) but not every-tick; classified as `cadence-gated`.

| Sub-Phase ID | Service | File Path | Wiring Status | Description | Suggested Acceptance Criterion |
|---|---|---|---|---|---|
| WD-08 | `CalamityService.process_world_dynamics()` | `src/world/calamity.py` | `cadence-gated` | Evaluates calamity conditions: checks calamity maturity, triggers calamity spawn events, resets timers. | On a cadence tick with a mature calamity, the service emits at least one calamity entity and updates `last_calamity_tick_set`. |
| WD-09 | `SpawnService.process_spawns()` | `src/world/spawn.py` | `cadence-gated` | Replenishes monster populations in under-populated regions according to spawn configuration. | On a cadence tick, a region below minimum monster count receives new entity entries in `entities_add`. |
| WD-10 | `ResourceEcologyService.process_ecology()` | `src/world/ecology.py` | `cadence-gated` | Replenishes depleted resource nodes according to ecology configuration and region biome. | On a cadence tick, a fully depleted node in an eligible region appears in `nodes_add` or receives a `charges_delta`. |
| WD-11 | `ThreatService.process_threat_evolution()` | `src/world/threat.py` | `cadence-gated` | Evolves regional threat level based on entity composition, combat history, and calamity activity. | A region with high combat activity and no hero presence increments its threat level at the cadence tick. |
| WD-12 | `BossService.check_for_boss_spawn()` | `src/world/boss.py` | `cadence-gated` + `cadence.boss_spawn` | Checks boss spawn conditions (threat threshold + boss spawn cadence); emits boss entity if conditions met. | On a boss_spawn cadence tick with a region at threat threshold, a boss entity appears in `entities_add`. |
| WD-13 | `RaidService.check_for_raid()` | `src/world/raid.py` | `cadence-gated` | Evaluates raid conditions for all regions; emits raid-party entities if preconditions are met. | On a cadence tick where raid preconditions are met in a region, raid entities appear in `entities_add`. |
| WD-14 | `CampService.process_camps()` | `src/world/camp.py` | `cadence-gated` | Processes persistent encampment lifecycle: constructs, decays, and evicts camps by age and faction activity. | On a cadence tick, an expired camp is absent from `camp_updates`; an active camp emits a maintenance update. |
| WD-15 | `DemographicCycleService.process_demographics()` | `src/domains/demographics/cohort.py` | `cadence-gated` | Processes population cohort birth/death cycle (E52A): applies demographic pressure, births new cohort members, retires aged ones. | On a cadence tick, a region with birth pressure emits new population cohort entities; overpopulation emits mortality updates. |

### §B2 World Dynamics Sub-Phase Summary

| Status | Count | Sub-Phase IDs |
|---|---|---|
| `active` (every-tick) | 7 | WD-01 through WD-07 |
| `cadence-gated` | 8 | WD-08 through WD-15 |
| **Total** | **15** | |

---

## Combined Inventory Summary

| Source | Total Phases | Active | Feature-Gated | Cadence-Gated | Direct-Call |
|---|---|---|---|---|---|
| `pipeline.py:refine()` | 38 | 30 | 7 | 0 | 1 |
| `world_dynamics.py:resolve_dynamics()` | 15 | 7 | 0 | 8 | 0 |
| **Grand Total** | **53** | **37** | **7** | **8** | **1** |

**Domain breakdown:**

| Domain | Phases | Phase IDs |
|---|---|---|
| Engine pipeline (structural) | 23 | PP-01–02, PP-06–07, PP-09–11, PP-13–15, PP-17–22, PP-24–28, PP-30–37 |
| `src/domains/adventure/` | 1 | PP-12 |
| `src/domains/combat_engagement/` | 1 | PP-16 |
| `src/domains/cooperation/` | 1 | PP-05 |
| `src/domains/faction/` | 2 | PP-08 (direct), PP-10 |
| `src/domains/information/` | 1 | PP-04 |
| `src/domains/progression/` | 1 | PP-29 |
| `src/domains/world_emergence/` | 1 | PP-23 |
| `src/cognition/` | 1 | PP-03 |
| `src/systems/` | 3 | PP-30, PP-33, PP-35–36 |
| `src/world/` (world dynamics) | 12 | WD-01–14 excl. WD-15 |
| `src/domains/demographics/` | 1 | WD-15 |

---

## Notes

### LeadContradictionSystem
`src/engine/pipeline_phases/lead_contradiction.py` exists on disk and is referenced in
D09 Finding 3 (2026-06-22) as "E42D — wired into authoritative pipeline." It does not
appear in the current `pipeline.py:refine()` call sequence as a top-level `run_phase()`
invocation. It is likely called from within `StrategicIntelligenceSystem.fused_strategic_pass()`
(PP-30) or is pending integration. Not inventoried as a confirmed pipeline phase until
its direct call site is verified.

### Episode-Boundary Systems (not tick-live)
The following systems run in `CampaignOrchestrator._advance_state()` at episode boundaries,
not within the per-tick `refine()` pipeline. They are out of scope for this inventory:
- `SocialMemoryExporter` / `SocialMemoryImporter` (E43B)
- `ChronicleCompiler` (E51)
- `ProgressionPlanExporter` / `ProgressionPlanImporter` (E61B — scoped, not yet implemented)
- `CultureDriftExporter` / `CultureDriftImporter` (E62B — scoped, not yet implemented)

---

## Related Dimensions

- **D09 (System Wiring)** — Finding 3 (Risk 13/15) is the direct source of this document;
  D09 confirmed all PP-phase classes are `tick-live` in the authoritative pipeline
- **D02 (Foundation Feature Inventory)** — companion inventory for the enabling-capability
  substrate beneath the domain phase layer
- **D10 (Test Coverage)** — use this inventory to identify which domain phases have
  insufficient test coverage; feature-gated phases (PP-03–05, PP-12, PP-16, PP-23, PP-29)
  need flag-off scenario tests per Finding 4 (TCK-20260627-P2E-FEATURE-FLAG-TEST)
- **D14 (Coupling Depth)** — phase ordering in Part A defines causal coupling; any
  phase that reads outputs produced by a later phase is a coupling violation
- **D12 (Pattern Consistency)** — `run_phase()` is the canonical authoring pattern;
  PP-08 (`faction_decision`) is the only current exception (direct call by design)
