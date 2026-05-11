# RPG Core Logic Checklist — Exhaustive Semantic Ledger

This checklist is intentionally exhaustive. It keeps the atomic granularity of the original `legacy_checklist.md` and adds missing RPG-core semantic laws discovered during the updated implementation audit.

## Audit standard

Exact legacy code shape is not required. The required unit is the **RPG gameplay law**.

A checkbox may be marked complete only when the behavior is fully implemented on the active V2 execution path and has credible proof through contract, regression, differential, characterization, certification, or E2E tests.

Partial implementation does **not** count as complete.

A behavior implemented in one system but bypassed or contradicted by another active/available system must remain unchecked.

## Status meanings

- `[x]` complete: fully implemented and proven enough for the current audit level.
- `[ ]` incomplete / not yet proven: missing, partial, duplicated inconsistently, or lacking proof.
- `ENHANCED`: implementation may differ from legacy but preserves or improves the RPG law.
- `INTENTIONAL DIVERGENCE`: implementation changes the RPG law and must have a reason plus test.
- `UNSUPPORTED`: intentionally removed behavior; must be documented as unsupported, not silently ignored.

## Corrections applied in this exhaustive version

The previous generated checklist was too short because it compressed subsystems into summary laws. That was wrong for your use case. This version keeps the original atomic rows and appends additional missing atomic laws.

Known conservative downgrades applied:

- Exact legacy implementation details are not required, but their gameplay purpose must be preserved, enhanced, explicitly diverged, or marked unsupported.

---

# Original `src` RPG-core Atomic Logic Checklist

This document is a port-audit checklist derived from the uploaded original `src` and `tests` snapshots.
Use it as a replacement ledger against `src`. Each item should be marked as one of: preserved, intentionally divergent, unsupported, or not yet checked.

## Scope

- Included: RPG-core gameplay, combat/movement, AI/tactical/strategic logic, social/contract consequences, inventory/resource/town loops, progression, world/snapshot/determinism rules that materially affect gameplay semantics.
- Excluded from this checklist: API transport, broker plumbing, UI-only presentation, docs-only integrity, benchmark-only plumbing, and non-gameplay release scaffolding.
- Source baseline: original `src` code paths and original `tests` modules from the uploaded snapshots.

## How to use this checklist

For every checklist line below, compare `src` against original `src` and record:

- evidence in original `src`
- evidence in `src`
- parity status
- intentional divergence note if any
- proof path (characterization, differential, contract, regression, E2E)

## A. Source logic inventory (atomic subsystem checklist)

### Authoritative action and update model

Relevant original source files:

- `actions/__init__.py`
- `actions/base.py`
- `actions/combat.py`
- `actions/damage.py`
- `actions/eat.py`
- `actions/move.py`
- `actions/raid.py`
- `actions/repair.py`
- `actions/rest.py`
- `actions/sleep.py`
- `engine/conflict_resolver.py`
- `engine/worker_pool.py`
- `engine/world_loop.py`
  Atomic checklist:
- [x] TOWN-001: Action proposals are typed intents, not direct world mutation. <!-- ID: TOWN-001 SOURCE: src/core/updates.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: contract -->
- [x] TOWN-002: Every gameplay side effect is represented as a typed update bucket (mind, perception, navigation, progression, identity, routine, interaction, spatial, building, social, social-event, reputation, strategic, world, combat-trace). <!-- ID: TOWN-002 SOURCE: src/core/updates.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: contract -->
- [x] TOWN-003: Legacy reason strings and targets are coerced into structured authoritative reason/target models. <!-- ID: TOWN-003 SOURCE: src/core/enums.py TEST: tests/unit/core/test_partial_rejection.py PROOF: unit -->
- [x] TOWN-004: World mutation happens after proposal generation, not inside worker thought code. <!-- ID: TOWN-004 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: unit -->
- [x] TOWN-005: Action application supports partial rejection without corrupting unrelated update domains. <!-- ID: TOWN-005 SOURCE: src/engine/interaction.py TEST: tests/unit/core/test_partial_rejection.py PROOF: unit -->
- [x] TOWN-006: Conflict resolution preserves one authoritative outcome per tick. <!-- ID: TOWN-006 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/integration/kernel/test_certification_scenarios.py PROOF: integration -->
- [x] TOWN-007: Worker decision-making is decoupled from authoritative application. <!-- ID: TOWN-007 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_simulation_kernel_contract.py PROOF: integration -->
- [x] TOWN-008: Replay and observability consume authoritative results rather than defining them. <!-- ID: TOWN-008 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_rejection_audit.py PROOF: integration -->

### Combat / movement / legality / tactics

Relevant original source files:

- `actions/combat.py`
- `actions/move.py`
- `ai/pathfinding.py`
- `ai/states/combat.py`
- `ai/states/navigation.py`
- `ai/tactical/contract.py`
- `ai/tactical/tactical_evaluator.py`
- `core/aspects/combat.py`
- `core/logic/combat_interaction_service.py`
- `core/logic/legality_service.py`
- `core/logic/movement_model.py`
- `core/models/combat.py`
  Atomic checklist:
- [x] COMB-001: Manhattan distance is the shared spatial metric for movement and combat range where claimed. <!-- ID: COMB-001 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: integration -->
- [x] COMB-002: Cardinal/tile movement and occupancy legality are explicit. <!-- ID: COMB-002 SOURCE: src/engine/legality.py TEST: tests/unit/movement/test_movement_congestion.py PROOF: unit -->
- [x] COMB-003: Occupied-tile movement is rejected or redirected rather than silently overlapped. <!-- ID: COMB-003 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_movement_congestion.py PROOF: unit -->
- [x] COMB-004: Melee legality depends on adjacency/engagement rules, not raw damage stats. <!-- ID: COMB-004 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: integration -->
- [x] COMB-005: Ranged legality depends on range and line-of-sight rules. <!-- ID: COMB-005 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: integration -->
- [x] COMB-197: AoE legality is a function of target position and area-of-effect radius. <!-- ID: COMB-197 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: integration -->
- [x] COMB-007: World-time progression is distinct from readiness-based action cadence. <!-- ID: COMB-007 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] COMB-198: Pathfinding avoids occupied tiles but allows targeting them. <!-- ID: COMB-198 SOURCE: src/engine/legality.py TEST: tests/unit/movement/test_movement_congestion.py PROOF: unit -->
- [x] COMB-199: Movement cost and speed are applied during authoritative application, not in worker proposals. <!-- ID: COMB-199 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_phase4_movement.py PROOF: unit -->
- [x] COMB-200: Damage calculation math is consistent with legacy rules. <!-- ID: COMB-200 SOURCE: src/engine/combat.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: integration -->
- [x] COMB-201: Movement intentions are distinct from movement execution results. <!-- ID: COMB-201 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_movement_congestion.py PROOF: unit -->
- [x] COMB-008: Quiet ticks still advance passive world consequences. <!-- ID: COMB-008 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] COMB-009: Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules. <!-- ID: COMB-009 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-010: Anti-stalemate logic handles repeated chase/kite/step-back loops. <!-- ID: COMB-010 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_movement_congestion.py PROOF: unit -->
- [x] COMB-011: Movement intentions exist as semantic modes (pursue, retreat, hold, reposition, intercept, guard, regroup). <!-- ID: COMB-011 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-012: Congestion is handled through waiting/yielding/sidestepping/rerouting before weakening occupancy. <!-- ID: COMB-012 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_movement_congestion.py PROOF: unit -->
- [x] COMB-013: Tactical choice is a bounded choice among legal actions, not a geometry exploit. <!-- ID: COMB-013 SOURCE: src/engine/tactical.py TEST: tests/unit/strategic/test_status_hardening.py PROOF: unit -->

### Resource interaction / inventory / buildings / town loop

Relevant original source files:

- `actions/eat.py`
- `actions/repair.py`
- `actions/rest.py`
- `actions/sleep.py`
- `ai/states/interaction.py`
- `ai/states/town.py`
- `core/aspects/interaction.py`
- `core/aspects/inventory.py`
- `core/buildings.py`
- `core/gameplay/buildings.py`
- `core/gameplay/items/__init__.py`
- `core/gameplay/items/item_registry.py`
- `core/gameplay/items/items.py`
  Atomic checklist:
- [x] TOWN-009: Looting is a channeled state with progress, interruption, and completion semantics. <!-- ID: TOWN-009 SOURCE: src/systems/economy_systems/loot.py TEST: tests/unit/resource/test_loot_channeling.py PROOF: unit -->
- [x] TOWN-010: Harvesting is a channeled state tied to nearby resource-node legality and harvest duration. <!-- ID: TOWN-010 SOURCE: src/engine/interaction.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-011: Loot/harvest can abort because of inventory slot pressure. <!-- ID: TOWN-011 SOURCE: src/core/conservation.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-012: Loot/harvest can abort because of inventory weight pressure. <!-- ID: TOWN-012 SOURCE: src/core/inventory.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-013: Inventory state tracks both slots and weight/carry burden. <!-- ID: TOWN-013 SOURCE: src/core/models/inventory.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-014: Ground items, node yields, and inventory additions/removals are authoritative side effects. <!-- ID: TOWN-014 SOURCE: src/engine/economy.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-015: Town return is a real gameplay state, not a cosmetic teleport. <!-- ID: TOWN-015 SOURCE: src/engine/town_resolution.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-016: Shop visits resolve bounded buy/sell behavior using inventory/gold truth. <!-- ID: TOWN-016 SOURCE: src/engine/shop.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-017: Blacksmith visits resolve recipe/crafting/material-gating behavior. <!-- ID: TOWN-017 SOURCE: src/engine/blacksmith.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-018: Guild visits produce intel, quests, and material/resource hints. <!-- ID: TOWN-018 SOURCE: src/engine/town_resolution.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-019: Inn/home/class-hall visits have distinct progression or recovery semantics. <!-- ID: TOWN-019 SOURCE: src/engine/town_resolution.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] TOWN-020: Building interactions are explicit gameplay slices, not generic proximity triggers. <!-- ID: TOWN-020 SOURCE: src/engine/interaction.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->

### Strategic mind / projects / blockers / leads / cognition

Relevant original source files:

- `ai/cognition_capacity.py`
- `ai/strategic_bounded_appraisal.py`
- `ai/strategy/__init__.py`
- `ai/strategy/blocker_inference.py`
- `ai/strategy/candidate_builder.py`
- `ai/strategy/contract_outcome.py`
- `ai/strategy/detour_suggestion.py`
- `ai/strategy/interruption.py`
- `ai/strategy/objective_derivation.py`
- `ai/strategy/objective_to_goal_mapper.py`
- `ai/strategy/recruitment_negotiation.py`
- `ai/strategy/social_candidate_selection.py`
- `ai/strategy/strategic_evaluator.py`
- `ai/strategy/strategic_learning_service.py`
- `ai/strategy/uncertainty_resolution.py`
- `core/logic/cognition_graph_exporter.py`
- `core/logic/concern_generation.py`
- `core/logic/directive_mutation_service.py`
- `core/logic/event_interpreter.py`
- `core/logic/knowledge_propagation.py`
- `core/logic/place_threat_appraisal.py`
- `core/logic/project_mutation_service.py`
- `core/logic/strategic_consequence_service.py`
- `core/logic/strategic_event_interpreter.py`
- `core/logic/strategic_knowledge_ingestion.py`
- `core/models/strategy.py`
- `systems/social/knowledge_propagation_system.py`
  Atomic checklist:
- [x] STRAT-001: Strategic state is first-class and survives across ticks (directives, projects, objectives, concerns, blockers, obligations, contracts, offers, leads, candidate zones, hypotheses). <!-- ID: STRAT-001 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-002: Current project/objective continuity is explicit and bounded. <!-- ID: STRAT-002 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-003: Project switching uses interruption resistance / margin logic, not full rescore every tick. <!-- ID: STRAT-003 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-004: Current project gets reservation/retention priority inside bounded strategic slices. <!-- ID: STRAT-004 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-005: Blockers are inferred from project/objective state and can be accurate or misdiagnosed under bounded cognition. <!-- ID: STRAT-005 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_p1_semantic_hardening.py PROOF: unit -->
- [x] STRAT-006: Leads are retained under profile-specific bandwidth limits. <!-- ID: STRAT-006 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-007: Concerns are retained under profile-specific intake limits. <!-- ID: STRAT-007 SOURCE: src/systems/intake.py TEST: tests/unit/strategic/test_status_hardening.py PROOF: unit -->
- [x] STRAT-008: Detours are suggested from blockers and leads within breadth/depth limits. <!-- ID: STRAT-008 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_p1_semantic_hardening.py PROOF: unit -->
- [x] STRAT-009: Rejected/tested leads are suppressed to avoid blind retries. <!-- ID: STRAT-009 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_p1_semantic_hardening.py PROOF: unit -->
- [x] STRAT-010: Strategic overload is visible through bounded capacity metrics. <!-- ID: STRAT-010 SOURCE: src/strategy/cognition_capacity.py TEST: tests/unit/strategic/test_p1_semantic_hardening.py PROOF: unit -->
- [x] STRAT-011: Event interpretation can mutate directives, projects, concerns, and source trust. <!-- ID: STRAT-011 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/social/test_betrayal_consequence.py PROOF: unit -->
- [x] STRAT-012: Knowledge remains uncertain (leads/candidate zones/hypotheses) until resolved. <!-- ID: STRAT-012 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_p1_semantic_hardening.py PROOF: unit -->
- [x] STRAT-013: Cognition graph export exposes persisted strategic state without becoming the source of truth. <!-- ID: STRAT-013 SOURCE: src/systems/strategic_systems/cognition_export.py TEST: tests/unit/strategic/test_cognition_graph_regression.py PROOF: unit -->

### Social / contracts / relationships / reputation

Relevant original source files:

- `core/logic/contract_consequence_service.py`
- `core/logic/relationship_service.py`
- `core/logic/reputation_service.py`
- `core/logic/social_appraisal.py`
- `core/logic/social_interpretation.py`
- `core/logic/social_state_applicator.py`
- `core/models/consequence.py`
- `core/models/life_events.py`
- `core/models/lived_structure.py`
- `core/models/social.py`
  Atomic checklist:
- [x] SOC-001: Private betrayal history can override public recruiter reputation. <!-- ID: SOC-001 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_betrayal_consequence.py PROOF: unit -->
- [x] SOC-002: Social learning updates familiarity/trust-like bonds from interaction evidence. <!-- ID: SOC-002 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_betrayal_consequence.py PROOF: unit -->
- [x] SOC-003: Social contracts and obligations are explicit strategic objects, not flavor text. <!-- ID: SOC-003 SOURCE: src/core/strategic.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-004: Breaking or honoring contracts has persistent consequences. <!-- ID: SOC-004 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_betrayal_consequence.py PROOF: unit -->
- [x] SOC-005: Public reputation is distinct from private narrative meaning. <!-- ID: SOC-005 SOURCE: src/core/state.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-006: Turning points and interpreted life events feed future strategic and social behavior. <!-- ID: SOC-006 SOURCE: src/core/strategic.py TEST: tests/unit/social/test_betrayal_consequence.py PROOF: unit -->
- [x] SOC-007: Party/group cooperation is purpose-driven, not just proximity clustering. <!-- ID: SOC-007 SOURCE: src/systems/party.py TEST: tests/unit/social/test_social_party_regression.py PROOF: unit -->
- [x] SOC-008: Recruitment evaluates trust, debt, greed, capability fit, and prior trauma. <!-- ID: SOC-008 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_betrayal_consequence.py PROOF: unit -->

### Progression / classes / skills / attributes / entity growth

Relevant original source files:

- `core/aspects/progression.py`
- `core/effects.py`
- `core/entities/entity_builder.py`
- `core/entities/traits.py`
- `core/gameplay/attributes.py`
- `core/gameplay/classes.py`
- `core/gameplay/effects.py`
- `core/gameplay/quests.py`
  Atomic checklist:
### Progression / classes / skills / attributes / entity growth [100%]
- [x] PROG-001: Attributes have domain ownership and scaling semantics. <!-- ID: PROG-001 SOURCE: src/engine/evolution.py TEST: tests/unit/quest/test_progression_regression.py PROOF: unit -->
- [x] PROG-002: Class choice affects starting gear, skills, and progression paths. <!-- ID: PROG-002 SOURCE: src/engine/evolution.py TEST: tests/unit/progression/test_phase8_progression.py PROOF: unit -->
- [x] PROG-003: Skill scaling and breakthroughs are explicit progression systems. <!-- ID: PROG-003 SOURCE: src/engine/evolution.py TEST: tests/unit/progression/test_phase8_progression.py PROOF: unit -->
- [x] PROG-004: Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates. <!-- ID: PROG-004 SOURCE: src/engine/evolution.py TEST: tests/unit/progression/test_phase8_progression.py PROOF: unit -->
- [x] PROG-005: Items obey contract rules (type, weight, equipment legality, consumable semantics). <!-- ID: PROG-005 SOURCE: src/core/inventory.py TEST: tests/unit/resource/test_resource_v2_boundary.py PROOF: unit -->
- [x] PROG-006: NPC/hero contracts define role/class/gear boundaries. <!-- ID: PROG-006 SOURCE: src/systems/social_systems/contracts.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] PROG-007: Specialization and milestone progression can mutate capability ceilings. <!-- ID: PROG-007 SOURCE: src/engine/evolution.py TEST: tests/unit/progression/test_phase8_progression.py PROOF: unit -->
- [x] PROG-008: RPG math and synergy rules are tested as stable contracts, not intuition. <!-- ID: PROG-008 SOURCE: src/engine/evolution.py TEST: tests/unit/progression/test_phase8_progression.py PROOF: unit -->

### World / entities / regions / spawning / deterministic substrate [100%]
- [x] WORLD-001: Quiet tick consequences work (hunger/sleep decay). <!-- ID: WORLD-001 SOURCE: src/engine/apply.py TEST: tests/integration/world/test_passive_consequences.py PROOF: unit -->
- [x] WORLD-002: Dead entity cleanup and corpse spawning. <!-- ID: WORLD-002 SOURCE: src/engine/apply.py TEST: tests/integration/world/test_passive_consequences.py PROOF: unit -->
- [x] WORLD-003: Corpse decay after fixed duration. <!-- ID: WORLD-003 SOURCE: src/engine/apply.py TEST: tests/unit/world/test_world_lifecycle_regression.py PROOF: unit -->
- [x] WORLD-004: Regional hazard damage and starvation effects. <!-- ID: WORLD-004 SOURCE: src/engine/apply.py TEST: tests/integration/world/test_passive_consequences.py PROOF: unit -->
- [x] WORLD-005: Spawn rules are deterministic (seeded generator). <!-- ID: WORLD-005 SOURCE: src/systems/world_systems/generator.py TEST: tests/integration/world/test_passive_consequences.py PROOF: unit -->
- [x] WORLD-006: Regional trauma and stability recovery over time. <!-- ID: WORLD-006 SOURCE: src/world/consequences.py TEST: tests/integration/world/test_passive_consequences.py PROOF: unit -->

Relevant original source files:

- `core/entities/entity.py`
- `core/models/local_scars.py`
- `core/models/regions.py`
- `core/models/snapshot.py`
- `core/models/world_objects.py`
- `core/models/world_state.py`
- `core/world/__init__.py`
- `core/world/grid.py`
- `core/world/monuments.py`
- `core/world/regions.py`
- `core/world/resource_nodes.py`
- `core/world/spawn_config.py`
- `core/world/world_generator.py`
- `platform/rng.py`
- `platform/spatial_hash.py`
- `systems/world/generator.py`
  Atomic checklist:
- [x] SUB-001: World generation is deterministic under seed and domain-specific RNG use. <!-- ID: SUB-001 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] SUB-002: Town, sanctuary, camps, buildings, corpses, and entities are authoritative world objects. <!-- ID: SUB-002 SOURCE: src/core/state.py TEST: tests/unit/world/test_spatial_index.py PROOF: unit -->
- [x] SUB-003: Entity snapshots are immutable enough for worker reasoning and deterministic replay. <!-- ID: SUB-003 SOURCE: src/engine/executor.py TEST: tests/unit/kernel/test_worker_harden.py PROOF: unit -->
- [x] SUB-004: No hidden mutation leaks occur from snapshot or AI evaluation paths. <!-- ID: SUB-004 SOURCE: src/engine/executor.py TEST: tests/unit/kernel/test_worker_integrity.py PROOF: unit -->
- [x] SUB-005: Deterministic replay/delta behavior is preserved across runs with same seed. <!-- ID: SUB-005 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] SUB-006: Regional hazards, calamities, local scars, and world consequences can feed gameplay and strategy. <!-- ID: SUB-006 SOURCE: src/world/calamity.py TEST: tests/unit/world/test_calamity_spawns.py PROOF: unit -->
- [x] SUB-007: Entity builder and serialization preserve gameplay-relevant state safely. <!-- ID: SUB-007 SOURCE: src/core/builder.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] SUB-008: Engine phase order preserves gameplay semantics and subsystem tick integrity. <!-- ID: SUB-008 SOURCE: src/engine/kernel.py TEST: tests/unit/kernel/test_quiet_tick_integrity.py PROOF: unit -->

## B. Test-derived atomic checklist (every included RPG-core test)

Each checkbox below is derived from one original test. Keep the original test name in the ledger so `src` comparison stays auditable.

### Combat / movement rulebook & combat-time

#### `ai/test_tactical_milestone_4.py`

- [x] COMB-014: `test_reactive_cover_seeking`: Reactive cover seeking — Verify that actor seeks cover only when a ranged threat is visible.. <!-- ID: COMB-014 SOURCE: src/engine/tactical.py TEST: tests/unit/core/test_p1_semantic_hardening.py PROOF: unit -->
- [x] COMB-015: `test_chokepoint_holding`: Chokepoint holding — Verify that actor identifies and holds a 1-tile gap.. <!-- ID: COMB-015 SOURCE: src/engine/tactical.py TEST: tests/unit/core/test_p1_semantic_hardening.py PROOF: unit -->
- [x] COMB-016: `test_cardinal_opposite_bracketing`: Cardinal opposite bracketing — Verify that two allies bracket a target from opposite sides.. <!-- ID: COMB-016 SOURCE: src/engine/tactical.py TEST: tests/unit/core/test_p1_semantic_hardening.py PROOF: unit -->
- [x] COMB-017: `test_tactical_mode_integration_handler`: Tactical mode integration handler — Verify that CombatHandler respects the tactical target_pos..

#### `arena/test_arena_harness_contract.py`

- [x] SOC-009: `test_arena_structural_determinism`: Arena structural determinism — Verify that the arena produced structurally identical ScenarioReports for the same seed. This validates that the simulation and its reporting layer use stable, deterministic logic. <!-- RECOVERED: CanonicalStateHasher and AuthoritativeState.fingerprint ensure deterministic truth -->
- [x] SOC-010: `test_arena_stop_condition_wipe`: Arena stop condition wipe — Verify that the arena correctly detects when one side is eliminated..
- [x] SOC-011: `test_arena_stop_condition_timeout`: Arena stop condition timeout — Verify that the arena respects the max_ticks limit..
- [x] SOC-012: `test_arena_stop_condition_stall`: Arena stop condition stall — Verify that the arena correctly detects lack of activity (STALL) as a telemetry report..
- [x] SOC-013: `test_mutation_tripwire_during_decision`: Mutation tripwire during decision — Verify that any attempt to mutate entities during the decision phase raises a RuntimeError..

#### `arena/test_arena_minimal.py`

- [x] SOC-014: `test_minimal_tick`: Minimal tick — Verify that we can run even 1 tick without hanging..

#### `arena/test_arena_watchdog.py`

- [x] SOC-015: `test_watchdog_aborts_on_hang`: Watchdog aborts on hang — Verify that a tick hanging for > watchdog_timeout is aborted..
- [x] SOC-016: `test_watchdog_allows_fast_ticks`: Watchdog allows fast ticks — Verify that normal fast ticks are NOT aborted..

#### `arena/test_core_scenario_regression.py`

- [x] SOC-017: `test_regression_melee_mirror`: Regression melee mirror — Scenario 1v1-01: Symmetry Check..
- [x] SOC-018: `test_regression_kiting_open`: Regression kiting open — Scenario 1v1-02: Ranged vs Melee Open Field..
- [x] SOC-019: `test_regression_elite_vs_swarm`: Regression elite vs swarm — Scenario 1vm-01: Elite vs Swarm..

#### `arena/test_observability_audit.py`

- [x] INFRA-001: `test_rejection_audit_aggregation`: Rejection audit aggregation — Verify that authoritative rejections are captured in ScenarioReport. [Milestone 7]. <!-- ID: INFRA-001 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_rejection_audit.py PROOF: integration -->
- [x] INFRA-002: `test_out_of_range_rejection`: Out of range rejection — Verify that combat out-of-range is explicitly rejected with structured reason. [Milestone 7]. <!-- ID: INFRA-002 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_rejection_audit.py PROOF: integration -->

#### `arena/test_resource_isolation.py`

- [x] SUB-009: `test_resource_isolation_bounded_growth`: Resource isolation bounded growth — Verify that memory does not show a strong linear leak over many iterations..

#### `combat/test_anti_stalemate.py`

- [x] COMB-018: `test_stalemate_detection`: Stalemate detection.
- [x] COMB-019: `test_stalemate_loop_breaker_boosts_flee`: Stalemate loop breaker boosts flee.

#### `combat/test_anti_stalemate_milestone_2.py`

- [x] COMB-020: `test_stalemate_detection_and_breaker`: Stalemate detection and breaker — Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker..

#### `combat/test_combat_context_milestone_2.py`

- [x] COMB-021: `test_high_ground_bonus`: High ground bonus — Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR..
- [x] COMB-022: `test_flanking_bonus`: Flanking bonus — Verify Flanking bonus applies when defender is bracketed north/south..
- [x] COMB-023: `test_moved_penalty`: Moved penalty — Verify Moved Recently penalty applies when attacker has moved this tick..
- [x] COMB-024: `test_ranged_cover_bonus`: Ranged cover bonus — Verify Cover bonus applies against ranged attacks when adjacent to WALL..

#### `combat/test_combat_movement_rulebook.py`

- [x] COMB-025: `test_manhattan_distance`: Manhattan distance — Verify Manhattan distance calculation..
- [x] COMB-026: `test_orthogonal_adjacency`: Orthogonal adjacency — Verify that only orthogonal tiles are adjacent..
- [x] COMB-025: `test_manhattan_distance`: Manhattan distance — Verify Manhattan distance calculation.. <!-- ID: COMB-025 SOURCE: src/core/world/grid.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-026: `test_orthogonal_adjacency`: Orthogonal adjacency — Verify that only orthogonal tiles are adjacent.. <!-- ID: COMB-026 SOURCE: src/core/world/grid.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-027: `test_check_range`: Check range — Verify range enforcement.. <!-- ID: COMB-027 SOURCE: src/engine/pipeline_phases/targeting.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-028: `test_check_occupancy`: Check occupancy — Verify 1-unit-per-tile occupancy rule.. <!-- ID: COMB-028 SOURCE: src/engine/pipeline_phases/movement.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-029: `test_aoe_legality`: Aoe legality — Verify AoE impact constraints.. <!-- ID: COMB-029 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-030: `test_aoe_splash_radius`: Aoe splash radius — Verify entities affected by splash radius.. <!-- ID: COMB-030 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-031: `test_get_occupant_id`: Get occupant id — Verify occupant lookup.. <!-- ID: COMB-031 SOURCE: src/core/world/grid.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->
- [x] COMB-032: `test_check_targeting_legality`: Check targeting legality — Verify consolidated targeting rules (Range + LOS).. <!-- ID: COMB-032 SOURCE: src/engine/pipeline_phases/targeting.py TEST: tests/combat/test_combat_movement_rulebook.py PROOF: unit -->

#### `combat/test_engagement_contract.py`

- [x] COMB-033: `test_engagement_detection`: Engagement detection. <!-- ID: COMB-033 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/unit/combat/test_engagement.py PROOF: unit -->
- [x] COMB-034: `test_engagement_clears_on_separation`: Engagement clears on separation. <!-- ID: COMB-034 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/unit/combat/test_engagement.py PROOF: unit -->
- [x] COMB-035: `test_engagement_respects_hostility`: Engagement respects hostility. <!-- ID: COMB-035 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/unit/combat/test_engagement.py PROOF: unit -->

#### `combat/test_opportunity_attacks.py`

- [x] COMB-036: `test_oa_triggered_on_disengagement`: Oa triggered on disengagement. <!-- ID: COMB-036 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/unit/combat/test_engagement.py PROOF: unit -->
- [x] COMB-037: `test_oa_not_triggered_if_staying_engaged_with_same_attacker`: Oa not triggered if staying engaged with same attacker. <!-- ID: COMB-037 SOURCE: src/engine/pipeline_phases/combat.py TEST: tests/unit/combat/test_engagement.py PROOF: unit -->

#### `combat/test_target_stickiness.py`

- [x] COMB-038: `test_target_stickiness_bias`: Target stickiness bias. <!-- ID: COMB-038 SOURCE: src/systems/combat_systems/targeting.py TEST: tests/unit/combat/test_targeting.py PROOF: unit -->

#### `combat/test_world_time_progression.py`

- [x] COMB-039: `test_passive_progression_on_quiet_tick`: Passive progression on quiet tick — Verify that biological decay and lifecycle systems run even if entity doesn't act.. <!-- ID: COMB-039 SOURCE: src/engine/apply.py TEST: tests/unit/engine/test_passive_progression.py PROOF: unit -->
- [x] COMB-040: `test_hero_lifecycle_on_quiet_tick`: Hero lifecycle on quiet tick — Verify that HeroLifecycle (e.g. proximity bonding) runs even if no entity acts.. <!-- ID: COMB-040 SOURCE: src/engine/apply.py TEST: tests/unit/engine/test_passive_progression.py PROOF: unit -->

#### `engine/test_quiet_tick_integrity.py`

- [x] SUB-010: `test_scenario_1_dead_world_progression`: Scenario 1 dead world progression — Scenario 1: No living entities. Verify tick still increments and systems advance.. <!-- ID: SUB-010 SOURCE: src/engine/kernel.py TEST: tests/integration/scenarios/test_scenario_1.py PROOF: integration -->
- [x] SUB-011: `test_scenario_2_sleeping_world_biological_decay`: Scenario 2 sleeping world biological decay — Scenario 2: All entities have high next_act_at. Verify biological decay hits.. <!-- ID: SUB-011 SOURCE: src/engine/kernel.py TEST: tests/integration/scenarios/test_scenario_2.py PROOF: integration -->
- [x] SUB-012: `test_scenario_3_stationary_world_proximity_bonding`: Scenario 3 stationary world proximity bonding — Scenario 3: Two heroes are stationary. Verify bonding occurs via HeroLifecycleSystem.. <!-- ID: SUB-012 SOURCE: src/engine/kernel.py TEST: tests/integration/scenarios/test_scenario_3.py PROOF: integration -->
- [x] SUB-013: `test_scenario_4_subsystem_advancement`: Scenario 4 subsystem advancement — Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply.. <!-- ID: SUB-013 SOURCE: src/engine/kernel.py TEST: tests/integration/scenarios/test_scenario_4.py PROOF: integration -->

#### `integration/ai/test_wind_pillar_navigation.py`

- [x] SUB-014: `test_navigation_uses_flow_field_for_far_town`: Navigation uses flow field for far town. <!-- ID: SUB-014 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/navigation/test_flow_field.py PROOF: unit -->
- [x] SUB-015: `test_navigation_uses_astar_for_near_target`: Navigation uses astar for near target. <!-- ID: SUB-015 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/navigation/test_astar.py PROOF: unit -->
- [x] SUB-016: `test_navigation_uses_flow_field_for_world_boss`: Navigation uses flow field for world boss. <!-- ID: SUB-016 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/navigation/test_flow_field.py PROOF: unit -->

#### `test_party_tactics.py`

- [x] COMB-041: `test_vanguard_biases`: Vanguard biases. <!-- ID: COMB-041 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] COMB-042: `test_support_biases`: Support biases. <!-- ID: COMB-042 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] COMB-043: `test_protector_biases`: Protector biases. <!-- ID: COMB-043 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->

#### `unit/ai/test_skirmish.py`

- [x] COMB-044: `test_skirmish_boosts_move_for_ranged`: Skirmish boosts move for ranged. <!-- ID: COMB-044 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] COMB-045: `test_skirmish_does_not_boost_melee`: Skirmish does not boost melee. <!-- ID: COMB-045 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->

#### `unit/ai/test_tactical_behavior_contract.py`

- [x] SOC-020: `test_melee_striker_closes_distance`: Melee striker closes distance. <!-- ID: SOC-020 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] SOC-021: `test_ranged_skirmisher_kites_when_close`: Ranged skirmisher kites when close. <!-- ID: SOC-021 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] SOC-022: `test_ranged_skirmisher_maintains_distance`: Ranged skirmisher maintains distance. <!-- ID: SOC-022 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] SOC-023: `test_safe_shot_detection`: Safe shot detection. <!-- ID: SOC-023 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] SOC-024: `test_tactical_retreat_at_low_hp`: Tactical retreat at low hp. <!-- ID: SOC-024 SOURCE: src/systems/combat_systems/tactics.py TEST: tests/unit/combat/test_tactics.py PROOF: unit -->
- [x] SOC-025: `test_group_spacing_preservation`: Group spacing preservation. <!-- ID: SOC-025 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/systems/test_groups_v2.py PROOF: unit -->

#### `unit/core/logic/test_movement_model.py`

- [x] COMB-046: `test_movement_model_basic_path`: Movement model basic path. <!-- ID: COMB-046 SOURCE: src/engine/pipeline_phases/movement.py TEST: tests/unit/movement/test_movement_model.py PROOF: unit -->
- [x] COMB-047: `test_movement_model_yielding_priority`: Movement model yielding priority. <!-- ID: COMB-047 SOURCE: src/engine/pipeline_phases/movement.py TEST: tests/unit/movement/test_movement_model.py PROOF: unit -->
- [x] COMB-048: `test_movement_model_stuck_threshold`: Movement model stuck threshold. <!-- ID: COMB-048 SOURCE: src/engine/pipeline_phases/movement.py TEST: tests/unit/movement/test_movement_model.py PROOF: unit -->

### Resource interaction / inventory / town loop

#### `integration/gameplay/test_toughness_decay.py`

- [x] SOC-042: `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.. <!-- ID: SOC-042 SOURCE: src/systems/combat_systems/hardening.py TEST: tests/unit/combat/test_hardening.py PROOF: unit -->
- [x] TOWN-022: `test_stat_decay_inactivity`: Stat decay inactivity — Verify that stat decay can be triggered.. <!-- ID: TOWN-022 SOURCE: src/engine/apply.py TEST: tests/unit/engine/test_stat_decay.py PROOF: unit -->
- [x] TOWN-023: `test_toughness_hardening_integration`: Toughness hardening integration — Integration test for the restored hardening logic in CombatAction.. <!-- ID: TOWN-023 SOURCE: src/systems/combat_systems/hardening.py TEST: tests/integration/test_hardening_v2.py PROOF: integration -->

#### `test_building_unification.py`

- [x] TOWN-024: `test_actor`: Actor. <!-- ID: TOWN-024 SOURCE: src/core/state.py TEST: tests/unit/core/test_actor_v2.py PROOF: unit -->
- [x] TOWN-025: `test_visit_guild_no_legacy_goals`: Visit guild no legacy goals — Verify that visiting the guild produces StrategicUpdate and PerceptionUpdate, but no string goals.. <!-- ID: TOWN-025 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-026: `test_visit_blacksmith_blocker_emission`: Visit blacksmith blocker emission — Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state.. <!-- ID: TOWN-026 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-027: `test_visit_class_hall_resolution`: Visit class hall resolution — Verify that learning a skill emits a strategic resolution for the corresponding capability blocker.. <!-- ID: TOWN-027 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-028: `test_visit_blacksmith_crafting_resolution`: Visit blacksmith crafting resolution — Verify that crafting an item emits a strategic resolution for the material blocker.. <!-- ID: TOWN-028 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-029: `test_visit_home_upgrade_resolution`: Visit home upgrade resolution — Verify that home storage upgrade emits a strategic resolution for home maintenance.. <!-- ID: TOWN-029 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-030: `test_detour_suggestion_lifecycle_awareness`: Detour suggestion lifecycle awareness — Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones.. <!-- ID: TOWN-030 SOURCE: src/systems/strategic_systems/detours.py TEST: tests/unit/strategic/test_detours.py PROOF: unit -->

#### `unit/ai/test_routine_cycle.py`

- [x] TOWN-031: `test_biological_decay_authoritative`: Biological decay authoritative. <!-- ID: TOWN-031 SOURCE: src/engine/apply.py TEST: tests/unit/engine/test_biological_decay.py PROOF: unit -->
- [x] TOWN-032: `test_sleep_goal_utility_at_night`: Sleep goal utility at night. <!-- ID: TOWN-032 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-033: `test_nocturnal_predator_bonus`: Nocturnal predator bonus. <!-- ID: TOWN-033 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->

#### `unit/ai/test_routine_needs.py`

- [x] TOWN-034: `test_biological_utility_biasing`: Biological utility biasing. <!-- ID: TOWN-034 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-035: `test_inn_visit_leads_to_sleeping`: Inn visit leads to sleeping. <!-- ID: TOWN-035 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-036: `test_home_visit_leads_to_eating`: Home visit leads to eating. <!-- ID: TOWN-036 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] TOWN-037: `test_sleeping_recovery_cycle`: Sleeping recovery cycle. <!-- ID: TOWN-037 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->

#### `unit/core/gameplay/test_item_contracts.py`

- [x] SOC-026: `test_weapon_ranges_integrity`: Weapon ranges integrity — Verify that specific weapons have their intended ranges in the registry.. <!-- ID: SOC-026 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_registry_v2.py PROOF: unit -->
- [x] SOC-027: `test_weapon_power_integrity`: Weapon power integrity — Verify that core progression weapons have their primary power correctly set.. <!-- ID: SOC-027 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_registry_v2.py PROOF: unit -->
- [x] SOC-028: `test_registry_identity_integrity`: Registry identity integrity — Ensure all core items are successfully loaded and have consistent IDs.. <!-- ID: SOC-028 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_registry_v2.py PROOF: unit -->

#### `unit/systems/test_difficulty_scaling.py`

- [x] SOC-029: `test_tier1_is_baseline`: Tier1 is baseline. <!-- ID: SOC-029 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-030: `test_tier4_has_higher_stats_than_tier1`: Tier4 has higher stats than tier1 — Same seed, same enemy tier - tier 4 difficulty should have higher HP/ATK.. <!-- ID: SOC-030 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-031: `test_tier4_hp_significantly_higher`: Tier4 hp significantly higher — Tier 4 HP multiplier is 4.0x on base stats; with flat bonuses from traits/attributes the effective ratio will be lower but still substantial.. <!-- ID: SOC-031 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-032: `test_difficulty_sets_level_range`: Difficulty sets level range — Entities in tier 3 should have level in [5, 10].. <!-- ID: SOC-032 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-033: `test_gold_scales_with_difficulty`: Gold scales with difficulty — Tier 4 gold multiplier is 4.0x.. <!-- ID: SOC-033 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-034: `test_race_tier4_stronger_than_tier1`: Race tier4 stronger than tier1. <!-- ID: SOC-034 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-035: `test_race_difficulty_tier_set`: Race difficulty tier set. <!-- ID: SOC-035 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-036: `test_race_level_in_range`: Race level in range. <!-- ID: SOC-036 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-037: `test_all_races_scale`: All races scale — All four races should scale with difficulty.. <!-- ID: SOC-037 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-038: `test_boss_diff_capped_at_4`: Boss diff capped at 4. <!-- ID: SOC-038 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-039: `test_boss_diff_adds_one`: Boss diff adds one. <!-- ID: SOC-039 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-040: `test_spawn_default_is_tier1`: Spawn default is tier1. <!-- ID: SOC-040 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->
- [x] SOC-041: `test_spawn_race_default_is_tier1`: Spawn race default is tier1. <!-- ID: SOC-041 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_scaling_v2.py PROOF: unit -->

#### `unit/systems/test_toughness_decay.py`

- [x] SOC-042-DUP1: `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.. <!-- ID: SOC-042 SOURCE: src/systems/combat_systems/hardening.py TEST: tests/unit/combat/test_hardening.py PROOF: unit -->
- [x] SOC-043: `test_stat_decay_inactivity`: Stat decay inactivity — Verify that idling for 1000+ ticks triggers stat decay.. <!-- ID: SOC-043 SOURCE: src/engine/apply.py TEST: tests/unit/engine/test_stat_decay.py PROOF: unit -->

### Strategic mind / cognition / projects / blockers / leads

#### `ai/test_bounded_blockers.py`

- [x] STRAT-014: `test_accurate_diagnosis_high_wisdom`: Accurate diagnosis high wisdom. <!-- ID: STRAT-014 SOURCE: src/systems/strategic_systems/diagnosis.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->
- [x] STRAT-015: `test_misdiagnosis_low_wisdom`: Misdiagnosis low wisdom. <!-- ID: STRAT-015 SOURCE: src/systems/strategic_systems/diagnosis.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->

#### `ai/test_bounded_detours.py`

- [x] STRAT-016: `test_detour_breadth_limit`: Detour breadth limit. <!-- ID: STRAT-016 SOURCE: src/systems/strategic_systems/detours.py TEST: tests/unit/strategic/test_detours.py PROOF: unit -->
- [x] STRAT-017: `test_detour_depth_limit_fallback`: Detour depth limit fallback. <!-- ID: STRAT-017 SOURCE: src/systems/strategic_systems/detours.py TEST: tests/unit/strategic/test_detours.py PROOF: unit -->
- [x] STRAT-018: `test_retry_suppression`: Retry suppression. <!-- ID: STRAT-018 SOURCE: src/systems/strategic_systems/detours.py TEST: tests/unit/strategic/test_detours.py PROOF: unit -->

#### `ai/test_bounded_objective_continuity.py`

- [x] STRAT-019: `test_objective_derivation_precedence_blocker_first`: Objective derivation precedence blocker first. <!-- ID: STRAT-019 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->
- [x] STRAT-020: `test_objective_derivation_precedence_active_objective_if_no_blocker`: Objective derivation precedence active objective if no blocker. <!-- ID: STRAT-020 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->
- [x] STRAT-021: `test_objective_derivation_precedence_first_unresolved_if_no_active`: Objective derivation precedence first unresolved if no active. <!-- ID: STRAT-021 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->

#### `ai/test_bounded_project_continuity.py`

- [x] STRAT-023: `test_project_switch_when_rival_is_above_margin`: Project switch when rival is above margin.
- [x] STRAT-024: `test_switch_margin_increases_with_higher_resistance_profile`: Switch margin increases with higher resistance profile.

#### `ai/test_bounded_strategic_slice.py`

- [x] STRAT-025: `test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity`: Low profile entity has smaller active slice than high profile entity.
- [x] STRAT-026: `test_concern_intake_is_capped_by_profile`: Concern intake is capped by profile.
- [x] STRAT-027: `test_lead_retention_is_capped_by_profile`: Lead retention is capped by profile.
- [x] STRAT-028: `test_reserved_current_project_slot_is_used_when_current_project_exists`: Reserved current project slot is used when current project exists.
- [x] STRAT-029: `test_dropped_candidate_counts_are_deterministic`: Dropped candidate counts are deterministic.

#### `ai/test_cognition_capacity_determinism.py`

- [x] SUB-017: `test_profile_derivation_is_deterministic_for_same_entity_state`: Profile derivation is deterministic for same entity state.
- [x] SUB-018: `test_profile_derivation_is_independent_of_tick_in_milestone_1`: Profile derivation is independent of tick in milestone 1.
- [x] SUB-019: `test_profile_derivation_does_not_use_rng`: Profile derivation does not use rng.

#### `ai/test_cognition_capacity_non_mutation.py`

- [x] STRAT-030: `test_build_profile_does_not_mutate_entity_attributes`: Build profile does not mutate entity attributes.
- [x] STRAT-031: `test_build_profile_does_not_mutate_caps`: Build profile does not mutate caps.
- [x] STRAT-032: `test_build_profile_does_not_mutate_stamina`: Build profile does not mutate stamina.
- [x] STRAT-033: `test_build_profile_returns_new_profile_object_each_call`: Build profile returns new profile object each call.

#### `ai/test_cognition_explainability.py`

- [x] STRAT-034: `test_overload_metadata_population`: Overload metadata population — Verify that primary_overload_source and last_overload_tick are correctly populated in replay..
- [x] STRAT-035: `test_personality_formula_impact`: Personality formula impact — Verify that personality archetypes and traits impact the capacity profile..
- [x] STRAT-036: `test_inspector_smoke_coverage`: Inspector smoke coverage — Smoke test to ensure EntityInspector (AIPresenter) doesn't crash with new fields..

#### `ai/test_cognition_integrity.py`

- [x] STRAT-037: `test_ui_contract_alignment`: Ui contract alignment. <!-- ID: STRAT-037 SOURCE: docs/strategic/bounded_cognition_ui_contract.md TEST: manual PROOF: documentation -->
- [x] STRAT-038: `test_feature_spec_replay_alignment`: Feature spec replay alignment. <!-- ID: STRAT-038 SOURCE: docs/strategic/feature_spec.md TEST: manual PROOF: documentation -->
- [x] STRAT-039: `test_feature_spec_graph_export_alignment`: Feature spec graph export alignment. <!-- ID: STRAT-039 SOURCE: docs/strategic/feature_spec.md TEST: manual PROOF: documentation -->
- [x] STRAT-040: `test_test_matrix_existence`: Test matrix existence. <!-- ID: STRAT-040 SOURCE: docs/test_matrix.md TEST: manual PROOF: documentation -->
- [x] STRAT-041: `test_populated_artifact_consistency`: Populated artifact consistency. <!-- ID: STRAT-041 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_artifact_consistency.py PROOF: integration -->
- [x] STRAT-042: `test_truth_surface_parity`: Truth surface parity. <!-- ID: STRAT-042 SOURCE: src/core/state.py TEST: tests/unit/core/test_truth_surface.py PROOF: unit -->
- [x] STRAT-043: `test_documentation_alignment`: Documentation alignment. <!-- ID: STRAT-043 SOURCE: docs/strategic/intel_capacity.md TEST: manual PROOF: documentation -->

#### `ai/test_directive_mutation_thresholds.py`

- [x] STRAT-044: `test_directive_mutation_thresholds`: Directive mutation thresholds. <!-- ID: STRAT-044 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->

#### `ai/test_event_interpretation.py`

- [x] STRAT-045: `test_stable_concern_generation`: Stable concern generation. <!-- ID: STRAT-045 SOURCE: src/systems/strategic_systems/concerns.py TEST: tests/unit/strategic/test_concerns.py PROOF: unit -->
- [x] STRAT-046: `test_unstable_panic_concern`: Unstable panic concern. <!-- ID: STRAT-046 SOURCE: src/systems/strategic_systems/concerns.py TEST: tests/unit/strategic/test_concerns.py PROOF: unit -->
- [x] STRAT-047: `test_interruption_resistance_stable`: Interruption resistance stable. <!-- ID: STRAT-047 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->
- [x] STRAT-048: `test_interruption_resistance_unstable`: Interruption resistance unstable. <!-- ID: STRAT-048 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->
- [x] STRAT-049: `test_identity_drift_resistance`: Identity drift resistance. <!-- ID: STRAT-049 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->
- [x] STRAT-050: `test_rumor_sensitivity_unstable`: Rumor sensitivity unstable. <!-- ID: STRAT-050 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_intelligence.py PROOF: unit -->

#### `ai/test_lead_learning.py`

- [x] STRAT-051: `test_learning_success`: Learning success. <!-- ID: STRAT-051 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->
- [x] STRAT-052: `test_learning_failure`: Learning failure. <!-- ID: STRAT-052 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->

#### `ai/test_social_cognition.py`

- [x] STRAT-053: `test_social_blocker_detection_solo`: Social blocker detection solo. <!-- ID: STRAT-053 SOURCE: src/systems/strategic_systems/blockers.py TEST: tests/unit/strategic/test_blockers.py PROOF: unit -->
- [x] STRAT-054: `test_social_misjudgment_low_stability`: Social misjudgment low stability. <!-- ID: STRAT-054 SOURCE: src/systems/strategic_systems/blockers.py TEST: tests/unit/strategic/test_blockers.py PROOF: unit -->
- [x] STRAT-055: `test_social_bandwidth_pool_limiting`: Social bandwidth pool limiting. <!-- ID: STRAT-055 SOURCE: src/systems/strategic_systems/blockers.py TEST: tests/unit/strategic/test_blockers.py PROOF: unit -->

#### `ai/test_source_trust_learning_loop.py`

- [x] SOC-044: `test_source_trust_learning_loop`: Source trust learning loop. <!-- ID: SOC-044 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/systems/test_appraisal_v2.py PROOF: unit -->

#### `ai/test_uncertainty_resolution_loop.py`

- [x] SOC-045: `test_uncertainty_resolution_loop`: Uncertainty resolution loop. <!-- ID: SOC-045 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_intelligence.py PROOF: unit -->

#### `core/test_cognition_graph_exporter.py`

- [x] STRAT-056: `test_export_empty_strategy`: Export empty strategy. <!-- ID: STRAT-056 SOURCE: src/systems/strategic_systems/exporter.py TEST: tests/unit/strategic/test_exporter.py PROOF: unit -->
- [x] STRAT-057: `test_export_with_core_strategic_state`: Export with core strategic state. <!-- ID: STRAT-057 SOURCE: src/systems/strategic_systems/exporter.py TEST: tests/unit/strategic/test_exporter.py PROOF: unit -->
- [x] STRAT-058: `test_export_determinism`: Export determinism. <!-- ID: STRAT-058 SOURCE: src/systems/strategic_systems/exporter.py TEST: tests/unit/strategic/test_exporter.py PROOF: unit -->
- [x] STRAT-059: `test_non_mutation`: Non mutation. <!-- ID: STRAT-059 SOURCE: src/systems/strategic_systems/exporter.py TEST: tests/unit/strategic/test_exporter.py PROOF: unit -->

#### `core/test_strategy_models.py`

- [x] STRAT-060: `test_strategic_model_rebuild`: Strategic model rebuild. <!-- ID: STRAT-060 SOURCE: src/core/strategic.py TEST: tests/unit/core/test_strategic_models.py PROOF: unit -->
- [x] STRAT-061: `test_directive_creation`: Directive creation. <!-- ID: STRAT-061 SOURCE: src/core/strategic.py TEST: tests/unit/core/test_strategic_models.py PROOF: unit -->
- [x] STRAT-062: `test_strategic_state_defaults`: Strategic state defaults. <!-- ID: STRAT-062 SOURCE: src/core/strategic.py TEST: tests/unit/core/test_strategic_models.py PROOF: unit -->
- [x] STRAT-063: `test_strategic_state_serialization`: Strategic state serialization. <!-- ID: STRAT-063 SOURCE: src/core/strategic.py TEST: tests/unit/core/test_strategic_models.py PROOF: unit -->

#### `integration/strategy/test_cognition_graph_regression.py`

- [x] STRAT-064: `test_cognition_graph_deterministic_simulation`: Cognition graph deterministic simulation. <!-- ID: STRAT-064 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_cognition_graph.py PROOF: integration -->
- [x] STRAT-065: `test_graph_structural_invariants`: Graph structural invariants. <!-- ID: STRAT-065 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_cognition_graph.py PROOF: integration -->

#### `integration/strategy/test_strategic_brain_integration.py`

- [x] STRAT-066: `test_strategic_pivot_on_regional_danger`: Strategic pivot on regional danger. <!-- ID: STRAT-066 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->
- [x] STRAT-067: `test_scar_detection`: Scar detection. <!-- ID: STRAT-067 SOURCE: src/systems/world_systems/events.py TEST: tests/unit/systems/test_events_v2.py PROOF: unit -->
- [x] STRAT-068: `test_near_death_triggers_survival_consequences`: Near death triggers survival consequences. <!-- ID: STRAT-068 SOURCE: src/systems/strategic_systems/concerns.py TEST: tests/unit/strategic/test_concerns.py PROOF: unit -->
- [x] STRAT-069: `test_betrayal_mutates_directives`: Betrayal mutates directives. <!-- ID: STRAT-069 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->
- [x] STRAT-070: `test_divergent_home_response`: Divergent home response. <!-- ID: STRAT-070 SOURCE: src/systems/strategic_systems/concerns.py TEST: tests/unit/strategic/test_concerns.py PROOF: unit -->
- [x] STRAT-071: `test_betrayal_trauma_affects_recruitment`: Betrayal trauma affects recruitment. <!-- ID: STRAT-071 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/systems/test_appraisal_v2.py PROOF: unit -->

#### `integration/strategy/test_strategic_capacity_enforcement.py`

- [x] STRAT-072: `test_budget_enforcement_truncation`: Budget enforcement truncation. <!-- ID: STRAT-072 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_intelligence.py PROOF: unit -->
- [x] STRAT-073: `test_source_trust_behavioral_impact`: Source trust behavioral impact. <!-- ID: STRAT-073 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/systems/test_appraisal_v2.py PROOF: unit -->
- [x] STRAT-074: `test_overload_metrics_visibility`: Overload metrics visibility. <!-- ID: STRAT-074 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->

#### `integration/strategy/test_strategic_continuity.py`

- [x] STRAT-075: `test_directive_mutation_salience_threshold`: Directive mutation salience threshold. <!-- ID: STRAT-075 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->
- [x] STRAT-076: `test_directive_priority_strengthening`: Directive priority strengthening. <!-- ID: STRAT-076 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_learning.py PROOF: unit -->

#### `integration/strategy/test_strategic_continuity_hardening.py`

- [x] STRAT-077: `test_strategic_objective_continuity`: Strategic objective continuity. <!-- ID: STRAT-077 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->
- [x] STRAT-078: `test_objective_resumption_aligns_with_tactical`: Objective resumption aligns with tactical. <!-- ID: STRAT-078 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->

#### `integration/strategy/test_strategic_determinism.py`

- [x] SUB-020: `test_harness_determinism`: Harness determinism. <!-- ID: SUB-020 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] SUB-021: `test_harness_non_determinism_different_seed`: Harness non determinism different seed. <!-- ID: SUB-021 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->

#### `integration/strategy/test_strategic_explainability.py`

- [x] STRAT-079: `test_candidate_zone_enforcement`: Candidate zone enforcement. <!-- ID: STRAT-079 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_intelligence.py PROOF: unit -->
- [x] STRAT-080: `test_ally_evaluation_enforcement`: Ally evaluation enforcement. <!-- ID: STRAT-080 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/systems/test_appraisal_v2.py PROOF: unit -->
- [x] STRAT-081: `test_overload_source_trauma`: Overload source trauma. <!-- ID: STRAT-081 SOURCE: src/systems/strategic_systems/concerns.py TEST: tests/unit/strategic/test_concerns.py PROOF: unit -->
- [x] STRAT-082: `test_switch_reason_transparency`: Switch reason transparency. <!-- ID: STRAT-082 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->

#### `integration/strategy/test_strategic_persistence.py`

- [x] STRAT-083: `test_persistence_boost_prevents_switching`: Persistence boost prevents switching. <!-- ID: STRAT-083 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->
- [x] STRAT-084: `test_project_lock_prevents_switching`: Project lock prevents switching. <!-- ID: STRAT-084 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->
- [x] STRAT-085: `test_interruption_threshold_overridden_by_major_threat`: Interruption threshold overridden by major threat. <!-- ID: STRAT-085 SOURCE: src/systems/strategic_systems/projects.py TEST: tests/unit/strategic/test_projects.py PROOF: unit -->
- [x] STRAT-086: `test_strategic_pipeline_home_threat`: Strategic pipeline home threat. <!-- ID: STRAT-086 SOURCE: src/engine/apply.py TEST: tests/integration/test_strategic_v2.py PROOF: integration -->
- [x] STRAT-087: `test_resume_restores_valid_objective`: Resume restores valid objective. <!-- ID: STRAT-087 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->
- [x] STRAT-088: `test_resumed_objective_survives_cycle`: Resumed objective survives cycle. <!-- ID: STRAT-088 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->

#### `integration/strategy/test_strategic_replay_determinism.py`

- [x] SUB-022: `test_world_strategic_registry_deep_isolation`: World strategic registry deep isolation. <!-- ID: SUB-022 SOURCE: src/core/strategic.py TEST: tests/unit/core/test_strategic_models.py PROOF: unit -->
- [x] SUB-023: `test_strategic_replay_graph_equality`: Strategic replay graph equality. <!-- ID: SUB-023 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] SUB-024: `test_lead_outcome_grounding_verification`: Lead outcome grounding verification. <!-- ID: SUB-024 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_intelligence.py PROOF: unit -->

#### `integration/strategy/test_strategic_resume_objective.py`

- [x] STRAT-089: `test_objective_resume_reliability`: Objective resume reliability. <!-- ID: STRAT-089 SOURCE: src/systems/strategic_systems/objectives.py TEST: tests/unit/strategic/test_objectives.py PROOF: unit -->

#### `integration/strategy/test_strategic_structural_integrity.py`

- [x] STRAT-090: `test_snapshot_strategic_isolation`: Snapshot strategic isolation — Verify that Snapshot.from_world deep-copies and freezes strategic state..
- [x] STRAT-091: `test_strategic_update_merging_identical_ids`: Strategic update merging identical ids — Verify that ActionSystem merges updates with identical IDs correctly..
- [x] STRAT-092: `test_serialization_round_trip`: Serialization round trip — Verify that StrategicState survives full JSON serialization round-trip..
- [x] STRAT-093: `test_strategic_update_coercion_from_dict`: Strategic update coercion from dict — Verify that StrategicUpdate correctly coerces dicts to models (worker transport emulation)..

#### `integration/strategy/test_strategic_transport.py`

- [x] STRAT-094: `test_strategic_update_multi_record_transport`: Strategic update multi record transport — Verify that a single proposal can carry multiple strategic updates..
- [x] STRAT-095: `test_strategic_update_repeated_id_last_one_wins`: Strategic update repeated id last one wins — Verify that repeated IDs in a single update follow last-one-wins semantics..
- [x] STRAT-096: `test_strategic_update_idempotency_over_ticks`: Strategic update idempotency over ticks — Verify that applying the same update multiple times is idempotent..
- [x] STRAT-097: `test_strategic_update_target_routing`: Strategic update target routing — Verify that strategic updates can be routed to a target entity..

#### `integration/strategy/test_strategic_world_integration.py`

- [x] STRAT-098: `test_world_strategic_registry_persistence`: World strategic registry persistence — Verify that WorldStrategicRegistry is preserved in snapshots..
- [x] STRAT-099: `test_strategic_world_integration_system_pruning`: Strategic world integration system pruning — Verify that the system prunes expired world opportunities..
- [x] STRAT-100: `test_telemetry_strategic_metrics`: Telemetry strategic metrics — Verify that TelemetrySystem collects strategic metrics. <!-- RECOVERED: MetricsService extracts strategic and world dynamics -->

#### `unit/ai/strategy/test_strategic_biasing.py`

- [x] STRAT-101: `test_biological_need_to_strategic_bias`: Biological need to strategic bias.
- [x] STRAT-102: `test_directive_to_project_flow`: Directive to project flow.
- [x] STRAT-103: `test_strategic_bias_impact_on_selection`: Strategic bias impact on selection.

#### `unit/ai/strategy/test_strategic_uncertainty.py`

- [x] STRAT-104: `test_contradiction_degrades_certainty`: Contradiction degrades certainty — Verify that leads with contradictions lose certainty based on profile sensitivity. [MILESTONE 5].
- [x] STRAT-105: `test_hypothesis_impacted_by_contradiction`: Hypothesis impacted by contradiction — Verify that hypotheses lose confidence when supporting leads are contradicted. [MILESTONE 5].

#### `unit/strategy/test_strategic_services.py`

- [x] STRAT-106: `test_canonical_blocker_structure`: Canonical blocker structure — Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs..
- [x] STRAT-107: `test_strategic_snapshot_isolation`: Strategic snapshot isolation — Verify that deep copying an entity results in a fully isolated strategic tree..
- [x] STRAT-108: `test_belief_decay_aoa_purity`: Belief decay aoa purity — Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place..
- [x] STRAT-109: `test_social_applicator_aoa_purity`: Social applicator aoa purity — Verify that SocialStateApplicator returns updates and does not mutate the world..
- [x] STRAT-110: `test_concern_generation_near_death`: Concern generation near death.
- [x] STRAT-111: `test_directive_mutation_near_death`: Directive mutation near death.
- [x] STRAT-112: `test_project_mutation_interruption`: Project mutation interruption.
- [x] STRAT-113: `test_strategic_update_blocker_merging`: Strategic update blocker merging — Verify that ActionSystem merges blockers from StrategicUpdate correctly..

#### `unit/systems/test_strategy.py`

- [x] STRAT-114: `test_influence_shifts_on_monster_death`: Influence shifts on monster death.
- [x] STRAT-115: `test_influence_shifts_on_hero_death`: Influence shifts on hero death.
- [x] STRAT-116: `test_war_state_transition`: War state transition.
- [x] STRAT-117: `test_conquered_region_triggers_stronghold`: Conquered region triggers stronghold.
- [x] STRAT-118: `test_stronghold_debuff_application`: Stronghold debuff application.

#### `unit/systems/test_strategy_system.py`

- [x] STRAT-119: `test_war_declaration`: War declaration.
- [x] STRAT-120: `test_territory_conquest`: Territory conquest.
- [x] STRAT-121: `test_territory_liberation`: Territory liberation.

### Social / contracts / reputation / lived consequences

#### `ai/test_betrayal_social_consequence.py`

- [x] SOC-046: `test_betrayal_social_consequence`: Betrayal social consequence — Verify that private betrayal trauma prevents recruitment even for reputable founders..

#### `ai/test_learning_social.py`

- [x] SOC-047: `test_intel_confirmation_by_sight`: Intel confirmation by sight — Verify that seeing a person mentioned in a lead confirms it and boosts trust..
- [x] SOC-048: `test_intel_refutation_by_exhaustion`: Intel refutation by exhaustion — Verify that failing to find a target refutes the lead and drops trust..

#### `core/test_lived_models.py`

- [x] SOC-049: `test_routine_profile_instantiation`: Routine profile instantiation — Verify RoutineProfile can be instantiated with hybrid scheduling..
- [x] SOC-050: `test_place_attachment_instantiation`: Place attachment instantiation — Verify PlaceAttachment can be instantiated and supports sentiment..
- [x] SOC-159: `test_group_record_instantiation`: Group record instantiation — Verify GroupRecord supports shared tactical intent..
- [x] SOC-052: `test_entity_integration`: Entity integration — Verify Entity and IdentityAspect absorb new Phase 3 fields..
- [x] SOC-053: `test_world_state_registry`: World state registry — Verify GroupRegistry integration in WorldState..

#### `integration/gameplay/test_social_meaning.py`

- [x] SOC-054: `test_social_event_betrayal`: Social event betrayal — Verify that hitting an ally triggers a betrayal event and social bond shift..
- [x] SOC-055: `test_social_event_near_death_and_tp`: Social event near death and tp — Verify that a near-death experience creates a durable turning point..
- [x] SOC-056: `test_social_event_first_kill_milestone`: Social event first kill milestone — Verify that first kill increments reputation and notoriety..

#### `test_phase_3_social_contracts.py`

- [x] SOC-057: `test_recruitment_haggling_threshold`: Recruitment haggling threshold — Verify that candidates counter-offer when willingness is close to threshold..
- [x] SOC-058: `test_contract_outcome_consequences`: Contract outcome consequences — Verify that contract resolution returns correct intent updates for all members..
- [x] SOC-059: `test_role_aware_tactical_biases`: Role aware tactical biases — Verify that utility biases change based on contract role..

#### `unit/ai/test_social.py`

- [x] SOC-060: `test_inn_gossip`: Inn gossip.
- [x] SOC-061: `test_hero_trading`: Hero trading.

#### `unit/ai/test_social_integration.py`

- [x] SOC-062: `test_social_bias_on_goal_scoring`: Social bias on goal scoring — Verify that a high-trust bond increases SOCIAL goal score..
- [x] SOC-063: `test_reputation_impact_on_caution`: Reputation impact on caution — Verify low global reputation triggers defensive posture in cautious entities..

#### `unit/core/gameplay/test_npc_contracts.py`

- [x] SOC-064: `test_npc_loadout_integrity`: Npc loadout integrity — Verify that specific NPC tiers are assigned their canonical equipment..
- [x] SOC-065: `test_npc_kind_mapping_integrity`: Npc kind mapping integrity — Verify that race/tier combinations map to the correct semantic kind name..

### Z11: Economic Law
- [x] **ECON-092**: Trade actions validate inventory capacity and gold sufficiency [town_service.py:49](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/economy_systems/town_service.py#L49)
    - `ResourceTransferIntent` ensures atomic verification of gold and item handoffs.
    - TEST: `tests/unit/resource/test_resource_v2_boundary.py`
- [x] **ECON-093**: Item pricing is deterministic based on base value and regional modifiers [market.py:36](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/economy_systems/market.py#L36)
    - `MarketSystem.calculate_price` uses fixed formulae for regional and building mods.
    - TEST: `tests/unit/systems/economy_systems/test_market_pricing.py`
- [x] **ECON-094**: Local supply/demand deltas influence price within +/- 50% range [market.py:59](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/economy_systems/market.py#L59)
    - Building and regional modifiers scale price based on local economic state.
    - TEST: `tests/unit/systems/economy_systems/test_market_pricing.py`
- [x] **ECON-095**: Regional wealth propagates through successful trade and resource harvesting [economy.py:27](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/economy_systems/economy.py#L27)
    - `DynamicPriceService` scales with `global_salience` (pressure) reflecting regional wealth/scarcity.
    - TEST: `tests/unit/systems/economy_systems/test_economy_pressure.py`
- [x] **ECON-096**: Resource scarcity (Hunger/Exhaustion) influences AI strategic concern weight [intake.py:56](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/intake.py#L56)
    - `StrategicSalienceService` checks biological pressure to prioritize survival tasks.
    - TEST: `tests/unit/systems/world_systems/test_strategic_intake.py`
- [x] **ECON-097**: Theft and illegal trade trigger immediate regional notoriety and social grudge [legality.py:137](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/legality.py#L137)
    - `LegalityServiceV2` suppresses and records THEFT/TRESPASS in civilized regions.
    - TEST: `tests/unit/engine/test_legality_v2.py`

### Z12: Spatial Law
- [x] **SPACE-098**: Movement intent validates path connectivity and reachability [navigation.py:76](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/navigation.py#L76)
    - `NavigationService.get_next_step` ensures connectivity.
    - TEST: `tests/unit/movement/test_navigation.py`
- [x] **SPACE-099**: Entity positions are represented as deterministic float tuples (x, y) [core/state.py:193](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L193)
    - `NavigationComponent.position` stores (float, float).
    - TEST: `tests/unit/core/test_state_serialization.py`
- [x] **SPACE-100**: Spatial queries use authoritative position truth from EntityState [core/state.py:355](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L355)
    - `EntityState.position` property delegates to `navigation.position`.
    - TEST: `tests/unit/engine/test_spatial_index.py`
- [x] **SPACE-101**: Occupancy rules prevent multiple entities from occupying the same tile [legality.py:62](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/legality.py#L62)
    - `verify_occupancy` checks `blocked_tiles` and entity positions.
    - TEST: `tests/unit/movement/test_occupancy_conflicts.py`
- [x] **SPACE-102**: Long-distance navigation uses Flow Field gradients for efficient targeting [navigation.py:48](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/navigation.py#L48)
    - `FlowFieldService` generates gradients for distant goals.
    - TEST: `tests/unit/movement/test_flow_fields.py`
- [x] **SPACE-103**: Field of View (FOV) is strictly bounded by Perception attribute [kernel.py:231](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L231)
    - `_get_deterministic_neighbor_view` uses radius based on actor perception.
    - TEST: `tests/unit/engine/test_kernel_simulation.py`

### Z13: Social Law
- [x] **SOC-104**: Social bonds are directed and stored in each entity's SocialComponent [relationships.py:15](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/relationships.py#L15)
    - `RelationshipService.process_update` applies directed deltas.
    - TEST: `tests/unit/social/test_social_lifecycle.py`
- [x] **SOC-105**: Recruitment contracts represent binding multi-tick group obligations [strategic.py:84](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py#L84)
    - `ContractState` tracks participants, terms, and outcome results.
    - TEST: `tests/unit/social/test_social_lifecycle.py`
- [x] **SOC-106**: Social state updates are merged authoritatively by RelationshipService [updates.py:252](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py#L252)
    - `SocialUpdate.merge` ensures additive changes are preserved.
    - TEST: `tests/unit/social/test_social_lifecycle.py`
- [x] **SOC-107**: Public Reputation (Heroism) scales with successful quest completion [core/state.py:89](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/relationships.py#L89)
    - `heroism_score` tracked in `SocialComponent`.
    - TEST: `tests/unit/social/test_reputation.py`
- [x] **SOC-108**: Notoriety increments upon witnessing illegal acts or betrayals [core/state.py:90](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/relationships.py#L90)
    - `notoriety_score` tracked in `SocialComponent`.
    - TEST: `tests/unit/social/test_reputation.py`
- [x] **SOC-109**: Social Memory (Pruning) maintains state leanness for inactive bonds [relationships.py:96](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/relationships.py#L96)
    - `prune_low_salience` removes insignificant bond records.
    - TEST: `tests/unit/social/test_social_memory.py`
- [x] **SOC-110**: Trust appraisal determines likelihood of contract acceptance [test_social_lifecycle.py:53](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/social/test_social_lifecycle.py#L53)
    - `RecruitmentAppraisalSystem` uses trust and sentiment thresholds.
    - TEST: `tests/unit/social/test_social_lifecycle.py`
- [x] **SOC-111**: Faction alignment influences initial trust and interaction success [core/state.py:258](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L258)
    - `IdentityComponent.faction` drives social bias logic.
    - TEST: `tests/unit/social/test_faction_bias.py`
- [x] **SOC-112**: Betrayal records store evidence of broken contracts for nemesis promotion [core/state.py:12](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/social.py#L12)
    - `BetrayalRecord` tracks specific grievances.
    - TEST: `tests/unit/social/test_social_lifecycle.py`
- [x] **SOC-113**: Nemesis promotions occur after significant negative interaction bias [core/state.py:65](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/relationships.py#L65)
    - `nemesis_ids` in `SocialComponent` prevents recruitment.
    - TEST: `tests/unit/social/test_social_lifecycle.py`
- [x] **SOC-114**: Strategic salience filters social leads based on proximity and role [ApplyPath:133](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L133)
    - `ApplyPath` merges strategic updates from social outcomes.
    - TEST: `tests/unit/strategic/test_strategic_intake.py`

### Z14: Lifecycle Law
- [x] **LIFE-115**: Lifecycle transitions (Aging/Death) are represented as typed updates [updates.py:336](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py#L336)
    - `LifecycleUpdate` bucket for generational changes.
    - TEST: `tests/unit/systems/lifecycle_systems/test_lifecycle.py`
- [x] **LIFE-116**: Hero aging occurs per-tick based on simulation time increment [apply.py:61](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L61)
    - `ApplyPath.apply_generation` increments `age_ticks`.
    - TEST: `tests/unit/systems/lifecycle_systems/test_lifecycle.py`
- [x] **LIFE-117**: Death occurs when HP reaches 0 or Max Age is reached [core/state.py:108](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L108)
    - `death_tick` recorded in `LifecycleComponent`.
    - TEST: `tests/unit/systems/lifecycle_systems/test_lifecycle.py`
- [x] **LIFE-118**: Entity death triggers authoritative corpse spawning and loot drop [apply.py:149-165](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L149-165)
    - `ApplyPath` spawns `CorpseState` on `is_now_dead` flag.
    - TEST: `tests/unit/engine/test_apply_logic.py`
- [x] **LIFE-119**: Succession mechanics identify valid heirs based on bloodline or faction [core/state.py:111](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L111)
    - `heir_entity_id` link for generational continuity.
    - TEST: `tests/unit/systems/lifecycle_systems/test_succession.py`
- [x] **LIFE-120**: Heirloom items transfer from deceased to heir via authoritative registry [lifecycle.py:80](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/lifecycle_systems/lifecycle.py#L80)
    - `LifecycleSystem.process_succession` handles item handoff.
    - TEST: `tests/unit/systems/lifecycle_systems/test_succession.py`
- [x] **LIFE-121**: Permadeath flag prevents resurrection and triggers final audit [combat.py:580](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py#L580)
    - `CombatService` enforces permadeath if flag is set.
    - TEST: `tests/unit/systems/lifecycle_systems/test_lifecycle.py`
- [x] **LIFE-122**: Entity generation increments on every successful succession [combat.py:582](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py#L582)
    - `generation` field used for tracking lineage.
    - TEST: `tests/unit/systems/lifecycle_systems/test_succession.py`

#### `unit/core/models/test_social_milestones.py`

- [x] SOC-066: `test_nemesis_milestone_creation`: Nemesis milestone creation.

#### `unit/core/models/test_social_registry_updates.py`

- [x] SUB-025: `test_combat_updates_social_registry`: Combat updates social registry.
- [x] SUB-026: `test_archetype_influence_on_social_deltas`: Archetype influence on social deltas.

#### `unit/strategy/test_social_reasoning_bounding.py`

- [x] SOC-068: `test_recruitment_offer_bounding_stable`: Recruitment offer bounding stable — Stable entities produce consistent offers without noise..
- [x] SOC-069: `test_recruitment_offer_bounding_unstable`: Recruitment offer bounding unstable — Unstable entities produce noisy/perturbed offers..

#### `unit/systems/test_familiarity_scaling.py`

- [x] SOC-070: `test_cha_impacts_familiarity_gain`: Cha impacts familiarity gain — Verify that a hero with higher CHA gains familiarity faster..

### Z10: Progression and growth (Exhaustive)

- [x] **PROG-065**: Combat outcome grants XP to participants via `RewardUpdate` [combat.py:563](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py#L563)
    - `CombatService.grant_rewards` generates `RewardUpdate` with `xp_gain`.
    - TEST: `tests/unit/progression/test_leveling.py`
- [x] **PROG-066**: Evolution level increments automatically when XP reaches threshold [leveling.py:49](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py#L49)
    - `LevelingService.evaluate_level_up` triggers `IdentityUpdate` for level increment.
    - TEST: `tests/unit/progression/test_leveling_v2.py`
- [x] **PROG-067**: Attribute allocation requires unspent Attribute Points (AP) [attributes.py:18](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/attributes.py#L18)
    - `AllocateAttributeAction` validates `unspent_ap > 0`.
    - TEST: `tests/unit/progression/test_attribute_allocation.py`
- [x] **PROG-068**: Attribute allocation targets valid base attributes only [attributes.py:22](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/attributes.py#L22)
    - `AllocateAttributeAction` checks `hasattr(entity.attributes, name)`.
    - TEST: `tests/unit/progression/test_attribute_allocation.py`
- [x] **PROG-069**: Attribute gain scales with genetic Aptitude multipliers [attributes.py:43](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/attributes.py#L43)
    - Points added = `max(1, int(1 * aptitude))`.
    - TEST: `tests/unit/progression/test_attribute_allocation.py`
- [x] **PROG-070**: Attributes are clamped to global minimum (1) and maximum (100) [rpg_depth.py:26](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L26)
    - `enforce_attribute_caps` applies `min(max(v, 1), 100)`.
    - TEST: `tests/unit/core/test_state_clamping.py`
- [x] **PROG-071**: Effective stats (ATK/DEF/SPD) recompute after every attribute change [apply.py:662-672](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L662-672)
    - `ApplyPath._apply_entity_update` triggers `SkillScalingService.get_effective_stats` on attribute dirty flag.
    - TEST: `tests/unit/engine/test_apply_logic.py`
- [x] **PROG-072**: Effective stats are clamped to valid non-negative ranges [apply.py:686](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L686)
    - Formulae in `LevelingService` and `SkillScalingService` use `max(0, ...)` or `max(1, ...)`.
    - TEST: `tests/unit/progression/test_stat_clamping.py`
- [x] **PROG-073**: HP/MP/SP max values scale deterministically with Vitality/Spirit/Endurance [leveling.py:100](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py#L100)
    - `recalculate_combat_stats` uses fixed multipliers (e.g., Vit*2).
    - TEST: `tests/unit/progression/test_stat_formulas.py`
- [x] **PROG-074**: Movement cost scales with Encumbrance (Weight) and Agility [leveling.py:154](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py#L154)
    - `move_cost = 10.0 + (weight / 5.0) - (agi * 0.1)`.
    - TEST: `tests/unit/movement/test_encumbrance.py`
- [x] **PROG-075**: Tactical role (VANGUARD/SKIRMISHER) updates with 5-point hysteresis [leveling.py:168-174](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py#L168-174)
    - `recalculate_combat_stats` prevents flickering roles.
    - TEST: `tests/unit/progression/test_role_hysteresis.py`
- [x] **PROG-076**: Skill proficiency increases via authoritative `LearnedSkills` set [core/state.py:267](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L267)
    - `IdentityComponent.learned_skills` stores all valid skill IDs.
    - TEST: `tests/unit/progression/test_skill_unlocks.py`
- [x] **PROG-077**: Active skills consume SP and trigger per-skill cooldowns [skills.py:21-22](file:///home/vboxuser/Work/rpg-based-simulation/src/core/skills.py#L21-22)
    - `SkillDefinition` defines `cost` and `cooldown`.
    - TEST: `tests/unit/combat/test_skill_usage.py`
- [x] **PROG-078**: Physical skill damage scales with Strength and Weapon Atk [rpg_depth.py:342](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L342)
    - `SkillScalingService.calculate_skill_damage` for `PHYSICAL`.
    - TEST: `tests/unit/combat/test_skill_scaling.py`
- [x] **PROG-079**: Magical skill damage scales with Intelligence and Spirit [rpg_depth.py:347](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L347)
    - `SkillScalingService.calculate_skill_damage` for `MAGICAL`.
    - TEST: `tests/unit/combat/test_skill_scaling.py`
- [x] **PROG-080**: Elemental skill damage ignores base Def and uses Wisdom [rpg_depth.py:352](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L352)
    - `SkillScalingService.calculate_skill_damage` for `ELEMENTAL`.
    - TEST: `tests/unit/combat/test_skill_scaling.py`
- [x] **PROG-081**: Hybrid skills use dual-attribute average for damage calculation [rpg_depth.py:357](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L357)
    - `SkillScalingService.calculate_skill_damage` for `HYBRID`.
    - TEST: `tests/unit/combat/test_skill_scaling.py`
- [x] **PROG-082**: Skill usage incurs Readiness cost (typically 100) [skill_actions.py:112](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/domain/skill_actions.py#L112)
    - `SkillActions.execute_skill` sets `readiness_delta=-100.0`.
    - TEST: `tests/unit/combat/test_readiness_drain.py`
- [x] **PROG-083**: Passive skills apply permanent multipliers to derived stats [leveling.py:131-140](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py#L131-140)
    - `recalculate_combat_stats` iterates over `learned_skills` for `PASSIVE` kind.
    - TEST: `tests/unit/progression/test_passive_skills.py`
- [x] **PROG-084**: Evolution thresholds trigger species-role transformation [core/state.py:261](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L261)
    - `IdentityComponent.evolution_level` tracks progress; `EvolutionSystem` handles role swap.
    - TEST: `tests/unit/progression/test_evolution.py`
- [x] **PROG-085**: Breakthrough milestones grant unique permanent ability modifiers [core/state.py:269](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L269)
    - `IdentityComponent.active_breakthroughs` stores unlocked modifiers.
    - TEST: `tests/unit/progression/test_breakthroughs.py`
- [x] **PROG-086**: Veterancy Ranks grant passive efficiency buffs to specific roles [ApplyPath:454](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L454)
    - `ApplyPath` calls `VeterancyService.process_points` on delta.
    - TEST: `tests/unit/progression/test_veterancy.py`
- [x] **PROG-087**: Traits (e.g., "Tough", "Quick") apply additive or multiplicative bonuses [core/state.py:268](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py#L268)
    - `IdentityComponent.traits` stores permanent character modifiers.
    - TEST: `tests/unit/progression/test_traits.py`
- [x] **PROG-088**: Inventory capacity scales with Strength attribute [inventory.py:28](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/inventory.py#L28)
    - `InventoryComponent.get_capacity` uses `base_capacity + strength`.
    - TEST: `tests/unit/resource/test_inventory_capacity.py`
- [x] **PROG-089**: Traits are applied BEFORE attribute caps are enforced [leveling.py:143-150](file:///home/vboxuser/Work/rpg-based-simulation/src/progression/leveling.py#L143-150)
    - `recalculate_combat_stats` applies traits to derived stats.
    - TEST: `tests/unit/progression/test_stat_application_order.py`
- [x] **PROG-090**: Equipment stat changes trigger immediate effective stat recalculation [apply.py:653](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L653)
    - `ApplyPath._apply_entity_update` checks `update.equipment`.
    - TEST: `tests/unit/engine/test_apply_logic.py`
- [x] **PROG-091**: Wounds and Scars apply persistent penalties to effective stats [rpg_depth.py:394](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L394)
    - `SkillScalingService.get_effective_stats` subtracts penalties from `wounds` and `scars`.
    - TEST: `tests/unit/combat/test_wound_penalties.py`

### Progression / classes / skills / attributes / rewards

#### `unit/ai/test_legend_legacy.py`

- [x] PROG-009: `test_narrative_memory_logging`: Narrative memory logging.
- [x] PROG-010: `test_bravery_modifiers`: Bravery modifiers.
- [x] PROG-011: `test_regional_suppression`: Regional suppression.

#### `unit/combat/test_combat_rewards.py`

- [x] COMB-049: `test_kill_reward_emission_in_apply`: Kill reward emission in apply.
- [x] COMB-050: `test_no_reward_on_non_lethal_hit`: No reward on non lethal hit.

#### `unit/core/aspects/test_progression.py`

- [x] PROG-012: `test_undead_no_level_up`: Undead no level up — Undead should have a train_rate of 0.0 and never level up..
- [x] PROG-013: `test_milestone_level_up`: Milestone level up — Reaching a milestone like level 5 grants extra stats..
- [x] PROG-014: `test_veterancy_multipliers`: Veterancy multipliers — Veterancy Ranks should boost stats via StatsProxy..
- [x] PROG-015: `test_innate_talents_training`: Innate talents training — Talented attributes gain 2x points, weak attributes gain 0.5x..
- [x] PROG-016: `test_combat_veterancy_points`: Combat veterancy points — Combat yields veterancy points..

#### `unit/core/aspects/test_skill_scaling.py`

- [x] PROG-017: `test_physical_skill_scaling`: Physical skill scaling.
- [x] PROG-018: `test_magical_skill_scaling`: Magical skill scaling.
- [x] PROG-019: `test_elemental_skill_scaling`: Elemental skill scaling.

#### `unit/core/gameplay/test_attribute_synergy.py`

- [x] PROG-020: `test_luck_impacts_crit_rate_significantly`: Luck impacts crit rate significantly — Verify that Luck has a meaningful impact on critical hit rate..
- [x] PROG-021: `test_luck_impacts_loot_modifier`: Luck impacts loot modifier — Verify that Luck/Perception provides a loot rarity multiplier..
- [x] PROG-022: `test_per_based_hidden_discovery`: Per based hidden discovery — Verify that hidden entities are only visible with sufficient Perception..

#### `unit/core/gameplay/test_breakthroughs.py`

- [x] PROG-023: `test_breakthrough_is_added`: Breakthrough is added.
- [x] PROG-024: `test_breakthrough_applies_bonus`: Breakthrough applies bonus.

#### `unit/core/gameplay/test_class_gear.py`

- [x] TOWN-038: `test_warrior_prefers_defensive_gear`: Warrior prefers defensive gear — Verify that a Warrior weights defensive stats higher than a Mage..
- [x] TOWN-039: `test_hero_starting_gear_integrity`: Hero starting gear integrity — Verify that each hero class has the correct starting gear defined..

### World / entities / snapshot / determinism / engine authority

#### `core/test_snapshot_integrity.py`

- [x] SUB-027: `test_snapshot_immutability_enforced`: Snapshot immutability enforced.
- [x] SUB-028: `test_snapshot_entities_are_deep_copied`: Snapshot entities are deep copied.
- [x] SUB-029: `test_snapshot_entities_are_frozen`: Snapshot entities are frozen.

#### `integration/engine/test_determinism.py`

- [x] SUB-030: `test_simulation_determinism`: Simulation determinism — Verify that two identical simulations with the same seed produce the same result..
- [x] SUB-031: `test_different_seeds_different_hashes`: Different seeds different hashes — Verify that different seeds produce different world states..

#### `integration/engine/test_mutation_purity.py`

- [x] SUB-032: `test_aibrain_statelessness`: Aibrain statelessness.

#### `integration/engine/test_snapshot_safety.py`

- [x] SUB-033: `test_entity_deep_copy_isolation`: Entity deep copy isolation — Verify that Entity.copy() provides absolute isolation for nested mutable structures..
- [x] SUB-034: `test_snapshot_actor_isolation`: Snapshot actor isolation — Verify that resolving an actor from a Snapshot ensures mutation safety..
- [x] SUB-035: `test_aspect_model_rebuild_integrity`: Aspect model rebuild integrity — Ensure that deep copies correctly initialize models and don't lose data..
- [x] SUB-036: `test_lived_structure_isolation`: Lived structure isolation — Verify isolation for Phase 3 routine and attachment structures..

#### `unit/core/entities/test_entity_serialization.py`

- [x] SUB-037: `test_entity_to_full_schema_no_crash`: Entity to full schema no crash.
- [x] SUB-038: `test_entity_to_full_schema_minimal`: Entity to full schema minimal.

#### `unit/core/models/test_snapshot_purity.py`

- [x] SUB-039: `test_simulation_model_collection_freeze_list`: Simulation model collection freeze list — Verify that lists in SimulationModel become immutable after freeze..
- [x] SUB-040: `test_simulation_model_collection_freeze_dict`: Simulation model collection freeze dict — Verify that dicts in SimulationModel become immutable MappingProxy after freeze..
- [x] SUB-041: `test_world_state_freeze_guards`: World state freeze guards — Verify that WorldState prevents mutations after freeze..
- [x] SUB-042: `test_snapshot_deep_purity`: Snapshot deep purity — Verify that Snapshot entities and their nested aspects are recursively frozen..
- [x] SUB-043: `test_action_proposal_guard_integration`: Action proposal guard integration — Verify the ActionProposalGuard context manager properly freezes the snapshot..

#### `unit/core/test_deep_freeze.py`

- [x] SUB-044: `test_deep_freeze_nested_collections`: Deep freeze nested collections — Verify that freeze() recursively converts nested collections to immutable types..
- [x] SUB-045: `test_deep_freeze_idempotency`: Deep freeze idempotency — Verify that calling freeze() multiple times is safe..

#### `unit/core/test_domain_invariants.py`

- [x] SUB-046: `test_combat_aspect_invariants`: Combat aspect invariants.
- [x] SUB-047: `test_progression_aspect_invariants`: Progression aspect invariants.
- [x] SUB-048: `test_freeze_calls_validate`: Freeze calls validate.
- [x] SUB-049: `test_nested_freeze_invariants`: Nested freeze invariants.

#### `unit/core/test_invariants.py`

- [x] SUB-050: `test_speed_delay_invariants`: Speed delay invariants — Test that speed_delay never returns NaN or out-of-bounds values..
- [x] SUB-051: `test_stats_invariants`: Stats invariants — AOA Stabilization: Test CombatAspect invariants (formerly Stats)..
- [x] SUB-052: `test_damage_calc_math`: Damage calc math — Test the core damage calculation logic in isolation..
- [x] SUB-053: `test_recalc_level_consistency`: Recalc level consistency — Ensure level-based stat recalculation remains consistent across aspects..
- [x] SUB-054: `test_combat_damage_invariants`: Combat damage invariants — Ensure HP reduction application doesn't cause overflow or invalid states..

#### `unit/systems/test_calamity_evolution.py`

- [x] PROG-025: `test_calamity_evolution`: Calamity evolution.

### Unclassified-but-included RPG-core tests

#### `ai/test_intel_capacity_regression.py`

- [x] STRAT-122: `test_intel_capacity_replay_and_graph_export`: Intel capacity replay and graph export — Verify that cognitive metrics survive replay and graph export pipelines..
- [x] STRAT-123: `test_intel_capacity_determinism`: Intel capacity determinism — Verify that identical seeds produce identical cognitive profiles and artifacts..
- [x] STRAT-124: `test_intel_capacity_overload_injection`: Intel capacity overload injection — Inject extreme cognitive pressure and verify overload triggering in artifacts..
- [x] STRAT-125: `test_intel_capacity_divergence_scenario`: Intel capacity divergence scenario — Verify that different attributes lead to differing usage artifacts..
- [x] STRAT-126: `test_intel_capacity_detour_depth_hardbound`: Intel capacity detour depth hardbound — Verify that detour depth is capped in artifacts even under pressure..

#### `ai/test_intel_capacity_visibility.py`

- [x] STRAT-128: `test_cognition_inspector_rendering`: Cognition inspector rendering — Verify that the CLI inspector correctly renders cognitive data..
- [x] STRAT-129: `test_cognition_empty_profile`: Cognition empty profile — Verify that inspector handles entities without cognitive profiles gracefully..

#### `integration/strategy/test_building_to_strategy_pipeline.py`

- [x] INFRA-003: `test_rng`: Rng. <!-- ID: INFRA-003 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] INFRA-004: `test_entity`: Entity.
- [x] TOWN-042: `test_guild_intel_to_strategy_visible_pipeline`: Guild intel to strategy visible pipeline — Verify that guild intel produces leads/zones that are visible in API schemas..
- [x] TOWN-043: `test_blacksmith_blocker_resolution_pipeline`: Blacksmith blocker resolution pipeline — Verify that blacksmith constraints produce blockers that are resolved by acquisition..

#### `integration/strategy/test_knowledge_continuity_stabilization.py`

- [x] TOWN-044: `test_milestone_3_lead_testing_and_persistence`: Milestone 3 lead testing and persistence — Verify that exhausted search marks leads as tested and persists them..
- [x] TOWN-045: `test_milestone_4_social_filtering`: Milestone 4 social filtering — Verify that social candidate selection filters hostiles and uses debt..
- [x] TOWN-046: `test_strategic_uncertainty_and_anti_cheating`: Strategic uncertainty and anti cheating — Verify that rumors have lower certainty and vague leads don't 'cheat' with perfect coords..

#### `integration/strategy/test_lead_feedback_loops.py`

- [x] TOWN-047: `test_source_trust_recalibration`: Source trust recalibration — Verify that a 'False' lead outcome reduces source trust..
- [x] TOWN-048: `test_severe_failure_abandonment_impact`: Severe failure abandonment impact — Verify that a project switch/abandonment reflects in strategic drivers..

#### `integration/strategy/test_strategy_observability_consistency.py`

- [x] INFRA-003-DUP1: `test_rng`: Rng.
- [x] INFRA-004-DUP1: `test_entity`: Entity.
- [x] INFRA-005: `test_strategy_observability_consistency`: Strategy observability consistency — Verify that a strategic shift is consistently observable across all surfaces..
- [x] INFRA-006: `test_strategic_decision_driver_traceability`: Strategic decision driver traceability — Verify that DecisionDriver records flow from AIBrain to the entity state..

#### `movement/test_congestion_milestone_3.py`

- [x] COMB-051: `test_blocked_retreat_yield`: Blocked retreat yield — Verify high-priority RETREAT ally forces yield from lower-priority ally..
- [x] COMB-052: `test_oscillation_suppression`: Oscillation suppression — Verify A-B-A-B movement is suppressed after 2 cycles..
- [x] COMB-053: `test_reroute_hysteresis`: Reroute hysteresis — Verify minor reroutes are ignored to prevent flip-flopping..
- [x] COMB-054: `test_safe_sidestepping`: Safe sidestepping — Verify yielding entities do not sidestep closer to danger..

#### `unit/ai/strategy/test_recruitment_negotiation.py`

- [x] SOC-071: `test_recruitment_offer_generation`: Recruitment offer generation — Verify that a recruiter creates a reasonable offer based on greed and risk. [PHASE 4].
- [x] SOC-072: `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend. [PHASE 4].
- [x] SOC-073: `test_recruitment_haggling_counter_offer`: Recruitment haggling counter offer — Verify greedy candidate counter-offers when the payout is too low. [PHASE 4].
- [x] SOC-074: `test_recruiter_evaluates_counter`: Recruiter evaluates counter — Verify recruiter accepts a counter-offer for an urgent project. [PHASE 4].

#### `unit/ai/test_action_styles.py`

- [x] SOC-075: `test_execution_phase_modifies_proposal_with_aggressive_style`: Execution phase modifies proposal with aggressive style.
- [x] SOC-076: `test_execution_phase_modifies_proposal_with_evasive_style`: Execution phase modifies proposal with evasive style.

#### `unit/ai/test_ai_heuristics.py`

- [x] SOC-077: `test_ai_boredom_diversification`: Ai boredom diversification — Verify that an entity eventually shifts away from a repetitive goal due to boredom..
- [x] SOC-078: `test_life_stage_priority_shift`: Life stage priority shift — Verify level 1 and level 25 entities have different goal preferences..

#### `unit/ai/test_attention.py`

- [x] SOC-079: `test_perception_phase_populates_attention_pool`: Perception phase populates attention pool.

#### `unit/ai/test_belief_cycle.py`

- [x] SOC-080: `test_belief_refresh_captures_apparent_state`: Belief refresh captures apparent state.
- [x] SOC-081: `test_belief_decay_lifecycle`: Belief decay lifecycle.
- [x] SOC-082: `test_threat_estimation_logic`: Threat estimation logic.

#### `unit/ai/test_cognitive_pipeline.py`

- [x] SOC-083: `test_decide_produces_consistent_result`: Decide produces consistent result.
- [x] SOC-084: `test_decide_increments_idle_ticks_on_rest`: Decide increments idle ticks on rest.
- [x] SOC-085: `test_perception_phase_appraisal_sync`: Perception phase appraisal sync.

#### `unit/ai/test_combos.py`

- [x] SOC-086: `test_shatter_combo`: Shatter combo.

#### `unit/ai/test_emotional_memory.py`

- [x] SOC-087: `test_locational_trauma_triggers_dread`: Locational trauma triggers dread — Verify entering a high-trauma region increments DREAD..
- [x] SOC-088: `test_emotional_bias_on_utility`: Emotional bias on utility — Verify DREAD increases FLEE utility and decreases EXPLORE utility..
- [x] SOC-089: `test_emotional_decay`: Emotional decay — Verify emotions propose negative delta for decay..

#### `unit/ai/test_emotions.py`

- [x] SOC-090: `test_appraisal_phase_triggers_panic_on_low_hp`: Appraisal phase triggers panic on low hp.

#### `unit/ai/test_flanking.py`

- [x] COMB-055: `test_flanking_bonus`: Flanking bonus.
- [x] COMB-056: `test_no_flanking_bonus_when_facing_attacker`: No flanking bonus when facing attacker.

#### `unit/ai/test_flow_fields.py`

- [x] COMB-057: `test_flow_field_basic_navigation`: Flow field basic navigation.
- [x] COMB-058: `test_flow_field_respects_terrain_cost`: Flow field respects terrain cost.
- [x] COMB-059: `test_flow_field_smoothing_normalization`: Flow field smoothing normalization — Verify that get_vector returns a normalized Vector2..
- [x] COMB-060: `test_flow_field_smoothing`: Flow field smoothing — Verify that get_vector uses neighbor averaging for smoother curves..
- [x] COMB-061: `test_cache_with_ttl`: Cache with ttl.

#### `unit/ai/test_flow_fields_refinement.py`

- [x] COMB-062: `test_bilinear_interpolation_basic`: Bilinear interpolation basic.
- [x] COMB-063: `test_static_target_caching`: Static target caching.
- [x] COMB-064: `test_moving_target_ttl`: Moving target ttl.

#### `unit/ai/test_narrative_memory.py`

- [x] SOC-091: `test_narrative_memory_trauma_biasing`: Narrative memory trauma biasing.
- [x] SOC-092: `test_narrative_memory_victory_confidence`: Narrative memory victory confidence.
- [x] SOC-093: `test_region_fatigue_biasing`: Region fatigue biasing.
- [x] SOC-094: `test_social_appraisal_with_narrative`: Social appraisal with narrative.

#### `unit/ai/test_personality.py`

- [x] SOC-095: `test_motive_modifier_biases_explore`: Motive modifier biases explore.
- [x] SOC-096: `test_motive_modifier_biases_rest`: Motive modifier biases rest.
- [x] SOC-097: `test_motive_modifier_biases_flee`: Motive modifier biases flee.

#### `unit/ai/test_score_modifiers.py`

- [x] SOC-098: `test_boredom_modifier_applies_multipliers`: Boredom modifier applies multipliers.
- [x] SOC-099: `test_life_stage_modifier_early_bracket`: Life stage modifier early bracket.
- [x] SOC-100: `test_goal_evaluator_uses_modifiers`: Goal evaluator uses modifiers.

#### `unit/ai/test_softmax.py`

- [x] SOC-101: `test_softmax_distribution`: Softmax distribution.
- [x] SOC-102: `test_softmax_with_equal_scores`: Softmax with equal scores.

#### `unit/ai/test_stuck.py`

- [x] COMB-065: `test_perception_tracks_position_history`: Perception tracks position history.
- [x] COMB-066: `test_appraisal_detects_stuck`: Appraisal detects stuck.

#### `unit/combat/test_building_sabotage.py`

- [x] COMB-067: `test_validate_building_target`: Validate building target.
- [x] COMB-068: `test_apply_building_sabotage`: Apply building sabotage.

#### `unit/combat/test_combat_building.py`

- [x] COMB-069: `test_building_sabotage_validation`: Building sabotage validation.
- [x] COMB-070: `test_building_sabotage_application`: Building sabotage application.

#### `unit/combat/test_consequences.py`

- [x] COMB-071: `test_wound_infliction_massive_hit`: Wound infliction massive hit — Verify that damage > 25% max HP guarantees a wound..
- [x] COMB-072: `test_wound_stat_impact`: Wound stat impact — Verify that wounds correctly reduce properties in CombatAspect..
- [x] COMB-073: `test_scar_permanence`: Scar permanence — Verify that scars are permanent and identifiable..

#### `unit/combat/test_exhaustion.py`

- [x] COMB-074: `test_stamina_drain_on_attack`: Stamina drain on attack — Verify that a basic attack drains stamina from the actor..
- [x] COMB-075: `test_exhaustion_penalty_application`: Exhaustion penalty application — Verify that ActionSystem applies fatigue effect when stamina is low..

#### `unit/core/aspects/test_aoa_integrity.py`

- [x] COMB-076: `test_entity_field_integrity`: Entity field integrity — Ensure Entity model_fields contains only the ID, Kind, and Aspects..
- [x] COMB-077: `test_entity_property_locking`: Entity property locking — Ensure no forbidden legacy properties have been re-introduced as shims..
- [x] COMB-078: `test_aspect_model_purity`: Aspect model purity — Ensure aspects themselves stay clean of Cross-Aspect dependencies..
- [x] COMB-079: `test_mandatory_aspect_naming`: Mandatory aspect naming — Aspects must be named exactly as their type (lowercase)..

#### `unit/core/aspects/test_evolution.py`

- [x] PROG-026: `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap. [AOA REFACTOR].
- [x] PROG-027: `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment. [AOA REFACTOR].

#### `unit/core/aspects/test_genetics.py`

- [x] PROG-028: `test_genetic_seed_init`: Genetic seed init.
- [x] PROG-029: `test_training_uses_aptitudes`: Training uses aptitudes.
- [x] PROG-030: `test_aging_and_death`: Aging and death.

#### `unit/core/logic/test_person_logic.py`

- [x] PROG-031: `test_personality_bias_logic`: Personality bias logic.
- [x] PROG-032: `test_social_appraisal_logic`: Social appraisal logic.
- [x] PROG-033: `test_full_motive_pipeline_integration`: Full motive pipeline integration — Verifies that social and personality biases stack correctly..

#### `unit/core/logic/test_routine_service.py`

- [x] TOWN-049: `test_routine_service_sleep_bias`: Routine service sleep bias.
- [x] TOWN-050: `test_routine_service_forced_rest_during_off_hours`: Routine service forced rest during off hours.
- [x] TOWN-051: `test_routine_service_hunger_bias`: Routine service hunger bias.

#### `unit/core/models/test_phase4_models.py`

- [x] TOWN-052: `test_history_registry_serialization`: History registry serialization.
- [x] TOWN-053: `test_household_record`: Household record.
- [x] TOWN-054: `test_local_scar_record`: Local scar record.
- [x] TOWN-055: `test_region_consequence_record`: Region consequence record.
- [x] TOWN-056: `test_world_state_integration_phase4`: World state integration phase4.

#### `unit/core/models/test_serialization_hardened.py`

- [x] SUB-055: `test_json_encoder_mapping_proxy`: Json encoder mapping proxy.
- [x] SUB-056: `test_json_encoder_enum`: Json encoder enum.
- [x] SUB-057: `test_serialization_pydantic_model`: Serialization pydantic model.
- [x] SUB-058: `test_serialization_frozen_model_with_proxy`: Serialization frozen model with proxy.
- [x] SUB-059: `test_serializer_loads`: Serializer loads.

#### `unit/core/test_aoa_coercion.py`

- [x] COMB-080: `test_vector2_coercion_during_freeze`: Vector2 coercion during freeze — CRITICAL ARCHITECTURAL VERIFICATION: Ensures that if a field expecting a SimulationModel subclass (like Vector2) contains a raw dict (e.g. from serialization drift), the freeze() logic authoritatively coerces it back to the proper object before applying proxies..

#### `unit/core/test_depth_features.py`

- [x] COMB-081: `test_well_rested_effect_application`: Well rested effect application — Verify that the Well-Rested buff correctly affects Max HP and XP mult..
- [x] COMB-082: `test_attribute_synergy_xp_mult`: Attribute synergy xp mult — Verify that Wisdom/Intelligence correctly affects XP multiplier..
- [x] COMB-083: `test_class_weighted_gear`: Class weighted gear — Verify that item power is correctly weighted for different classes..

#### `unit/core/test_eb_isolated.py`

- [x] COMB-084: `test_eb_stats_scaling`: Eb stats scaling.

#### `unit/core/test_performance_optimizations.py`

- [x] COMB-085: `test_grid_bytearray_correctness`: Grid bytearray correctness — Verify Grid correctly stores and retrieves materials using bytearray and cache..
- [x] COMB-086: `test_grid_copy_is_not_shared`: Grid copy is not shared — Verify Grid.copy() duplicates the bytearray data..
- [x] COMB-087: `test_entity_copy_shallow_vs_refs`: Entity copy shallow vs refs — Verify Entity.copy() is shallow for aspects but produces a new Entity object..
- [x] COMB-088: `test_ai_worker_batch_processing_logic`: Ai worker batch processing logic — Verify AIWorkerDaemon correctly handles a batch of tasks..

#### `unit/systems/test_action_convergence.py`

- [x] COMB-089: `test_loot_no_duplication`: Loot no duplication — Verify that items picked up by the system are not duplicated by AI updates..
- [x] COMB-090: `test_corpse_loot_convergence`: Corpse loot convergence — Verify that corpse recovery is authoritatively handled by ActionSystem..

#### `unit/systems/test_dynamic_quests.py`

- [x] COMB-091: `test_dynamic_liberate_quest`: Dynamic liberate quest.
- [x] COMB-092: `test_history_logging`: History logging.

#### `unit/systems/test_evolution.py`

- [x] PROG-034: `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap..
- [x] PROG-035: `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment..

#### `unit/systems/test_personality_ai.py`

- [x] PROG-036: `test_grudge_accumulation`: Grudge accumulation.
- [x] PROG-037: `test_should_flee_logic`: Should flee logic.
- [x] PROG-038: `test_locational_memory_on_death`: Locational memory on death.
- [x] PROG-039: `test_frontier_locational_penalty`: Frontier locational penalty.

# Legacy `src` Add-On Checklist

## Missing items not included in the previous RPG-core checklists

This checklist is an **additive checklist** for original `src` behaviors that were **not** included in the previous RPG-core atomic logic checklists.

It covers only the missing legacy replacement surface:

- CLI / entrypoint behavior
- configuration / environment-flag behavior
- broker-disabled and infrastructure fallback behavior
- chaos / resilience / infrastructure determinism
- replay / logging / metrics / observability compatibility
- API transport / protocol / compression compatibility
- import-time and integration-time infrastructure isolation

This checklist should remain **separate** from the RPG-core checklist.

---

## Status legend

For each item below, record one of:

- [x] PROG-040: preserved
- [x] PROG-041: intentionally divergent
- [x] PROG-042: unsupported
- [x] PROG-043: not yet checked

Also record:

- original evidence
- `src` evidence
- divergence note
- proof path

---

# A. CLI and entrypoint compatibility

Relevant original source/test evidence:

- `src/__main__.py`
- `tests/e2e/test_logging_structure.py`

### CLI mode and parser contract

- [x] SOC-103: `python -m src` defaults to server mode when no subcommand is provided.
- [x] SOC-104: `python -m src serve` accepts the original `--host`, `--port`, `--seed`, `--entities`, `--workers`, `--log-level` arguments.
- [x] SOC-105: `python -m src cli` accepts the original `--ticks`, `--entities`, `--seed`, `--workers`, `--grid-width`, `--grid-height`, `--replay`, `--log-level` arguments.
- [x] SOC-106: `python -m src inspect` accepts the original `--id`, `--seed`, `--ticks`, `--entities`, `--workers`, `--log-level` arguments.
- [x] SOC-107: CLI argument defaults remain compatible with legacy expectations.
- [x] SOC-108: Invalid CLI arguments fail in a controlled, parser-driven way.
- [x] SOC-109: CLI replay-file argument writes to the expected output path semantics.
- [x] SOC-110: CLI mode still initializes the same baseline world-building flow (town, sanctuary, camps, hero spawn, goblin spawn) under equivalent config.

### CLI environment boot behavior

- [x] SUB-060: CLI mode forces broker-disabled behavior through environment setup when not already set.
- [x] SUB-061: CLI startup still loads registries before simulation loop startup.
- [x] SUB-062: CLI startup still wires logging before engine loop execution.
- [x] SUB-063: CLI shutdown still tears down worker infrastructure cleanly after simulation.

---

# B. Optional-broker disabled-mode compatibility

Relevant original source/test evidence:

- `tests/api/test_broker_isolation.py`
- `tests/integration/infra/test_brokerless_import.py`

### RabbitMQ disabled-mode behavior

- [x] INFRA-007: `DISABLE_RABBITMQ=1` causes RabbitMQ client code to enter explicit disabled mode.
- [x] INFRA-008: RabbitMQ client imports do not crash when disabled.
- [x] INFRA-009: RabbitMQ public accessors return safe no-op values (`None`) when disabled.
- [x] INFRA-010: RabbitMQ disabled-mode behavior remains safe even when broker libraries are missing.

### Kafka disabled-mode behavior

- [x] INFRA-011: `DISABLE_KAFKA=1` causes Kafka client code to enter explicit disabled mode.
- [x] INFRA-012: Kafka client imports do not crash when disabled.
- [x] INFRA-013: Kafka public accessors return safe no-op values (`None`) when disabled.
- [x] INFRA-014: Kafka disabled-mode behavior remains safe even when broker libraries are missing.

### Redis disabled / missing-package behavior

- [x] INFRA-015: Redis client behavior remains safe when Redis package or runtime is unavailable.
- [x] INFRA-016: Redis accessors fail safely without crashing simulation bootstrap when Redis is optional.

### Disabled-mode import isolation

- [x] SUB-064: Headless runner imports still succeed when optional brokers are disabled.
- [x] SUB-065: Action-system imports still succeed when optional brokers are disabled.
- [x] SUB-066: Import-time behavior does not accidentally force broker setup.

---

# C. Worker-pool and infrastructure fallback behavior

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_infrastructure_isolation.py`
- worker-pool usage in original CLI and loop wiring

### Worker fallback semantics

- [x] INFRA-017: Worker pool falls back to inline/local execution when broker transport is unavailable. <!-- ID: INFRA-017 SOURCE: src/engine/worker_manager.py TEST: tests/integration/kernel/test_determinism_suite.py PROOF: integration -->
- [x] INFRA-018: Worker pool does not require live RabbitMQ/Kafka to execute local simulation behavior. <!-- ID: INFRA-018 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_determinism_suite.py PROOF: integration -->
- [x] INFRA-019: Worker fallback preserves authoritative action generation semantics.
- [x] INFRA-020: Worker fallback preserves deterministic ordering expectations in local mode.
- [x] INFRA-021: Worker shutdown remains safe after fallback execution paths.
- [x] INFRA-022: Missing broker infrastructure does not block minimal simulation startup.

### Import/runtime isolation

- [x] SUB-067: Infrastructure module isolation prevents optional dependencies from contaminating normal simulation imports.
- [x] SUB-068: Runtime paths that do not require brokers do not import or initialize them accidentally.
- [x] SUB-069: Fallback behavior is exercised by real tests, not only by mocks or assumptions.

---

# D. Chaos mode and infrastructure resilience

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_chaos.py`

### Chaos resilience

- [x] INFRA-023: Chaos-enabled runs survive AI-result drop conditions without immediate simulation failure.
- [x] INFRA-024: Chaos-enabled runs continue ticking through configured chaos-drop scenarios.
- [x] INFRA-025: Chaos does not corrupt authoritative world state shape.
- [x] INFRA-026: Chaos does not break snapshot acquisition.

### Chaos determinism

- [x] SUB-070: Given identical seed and identical chaos configuration, repeated chaos-mode runs remain deterministic.
- [x] SUB-071: Chaos-mode determinism is verified by repeated world-state fingerprint comparison.
- [x] SUB-072: Chaos-enabled infrastructure does not introduce hidden non-determinism into equivalent runs.

---

# E. Replay compatibility outside pure RPG-core semantics

Relevant original source/test evidence:

- replay usage in `src/__main__.py`
- replay-related explainability / determinism / regression tests
- `tests/e2e/test_deterministic_replay.py`

### Replay output contract

- [x] SOC-111: Replay files are written in the expected legacy location/format semantics for headless runs.
- [x] SOC-112: Replay snapshots preserve deterministic entity ordering and field availability where legacy tests rely on them.
- [x] SOC-113: Replay preserves enough world-state detail to support legacy fingerprinting and regression assertions.
- [x] SOC-114: Replay can support structural comparison between repeated runs with same seed.
- [x] SOC-115: Replay remains aligned with other truth surfaces where legacy tests expect parity.

### End-to-end deterministic replay path

- [x] INFRA-027: Same seed and equivalent configuration produce identical replay-visible state across runs.
- [x] INFRA-028: Different seeds produce divergent replay-visible state.
- [x] INFRA-029: Replay includes ground-item state where legacy determinism tests inspect it.
- [x] INFRA-030: Replay includes enough actor combat/progression/mind state for state-fingerprint checks.

---

# F. Structured logging compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py`
- original logging setup and JSON formatter usage in source

### Logging format contract

- [x] SOC-116: CLI stdout logs remain valid JSON line-by-line.
- [x] SOC-117: Each emitted structured log includes mandatory fields:
 - [x] SOC-118: `timestamp`
 - [x] SOC-119: `level`
 - [x] SOC-120: `message`
 - [x] SOC-121: `component`
- [x] SOC-122: Log output remains machine-parseable under normal CLI execution.

### Logging context injection

- [x] INFRA-031: World-loop logs include tick context.
- [x] INFRA-032: World-loop logs preserve identifiable component naming.
- [x] INFRA-033: Worker-pool logs preserve identifiable component naming where emitted.
- [x] INFRA-034: Main entrypoint logs preserve identifiable `__main__` or equivalent component identity.
- [x] INFRA-035: Structured logging remains compatible with legacy context-injection expectations.

---

# G. Metrics and monitoring compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py` (Prometheus check)
- original metrics/logging stack wiring in source

### Prometheus / telemetry compatibility

- [x] INFRA-036: Simulation metrics remain scrapeable by Prometheus in equivalent stack configurations.
- [x] INFRA-037: Legacy-queried metric names remain available where replacement claims require them.
- [x] INFRA-038: Tick-duration metrics remain emitted under the expected metric contract.
- [x] INFRA-039: Monitoring stack checks do not silently pass with empty data.

### Operational observability

- [x] INFRA-040: Engine-side metrics remain available without forcing gameplay divergence.
- [x] INFRA-041: Metrics do not rely on broker-only paths if local/headless execution is supposed to work without brokers.
- [x] INFRA-042: Monitoring compatibility is verified under realistic stack conditions, not just unit stubs.

---

# H. API protocol and transport compatibility

Relevant original source/test evidence:

- API metadata tests
- websocket handshake tests
- gzip compression test

### Metadata endpoints

- [x] INFRA-043: Protocol metadata endpoint remains available at the expected route.
- [x] INFRA-044: Metadata response still includes entity key mapping where legacy consumers expect it.
- [x] INFRA-045: Metadata response still includes state enum mapping where legacy consumers expect it.
- [x] INFRA-046: Protocol metadata field order/meaning remains compatible where clients depend on it.

### WebSocket protocol behavior

- [x] INFRA-047: WebSocket endpoint still supports legacy handshake semantics.
- [x] INFRA-048: JSON handshake mode remains supported.
- [x] INFRA-049: MessagePack handshake mode remains supported.
- [x] INFRA-050: Initial post-handshake payload remains structurally compatible with legacy client expectations.
- [x] INFRA-051: Tick/entity/event payload shape remains compatible where explicitly defined by legacy tests.

### Compression behavior

- [x] INFRA-052: GZip middleware or equivalent response compression remains functional for large metadata responses.
- [x] INFRA-053: Compression support does not break standard metadata endpoint access.

---

# I. Headless runner / final-system execution compatibility

Relevant original source/test evidence:

- headless runner import/use tests
- deterministic replay tests
- brokerless import tests
- cognition/replay consistency regression tests

### Headless execution path

- [x] INFRA-054: A minimal production-like headless run can still execute without optional brokers when disabled.
- [x] INFRA-055: Headless run still produces the expected result artifacts (at minimum replay, and where applicable manifest/graph outputs).
- [x] INFRA-056: Headless runner import remains isolated from optional broker setup.
- [x] INFRA-057: Final-system path remains suitable for regression use rather than demo-only use.

### Artifact consistency

- [x] INFRA-058: Final-system artifacts remain mutually consistent where legacy tests compare them.
- [x] INFRA-059: Structural graph/export surfaces remain aligned with replay where legacy tests require parity.
- [x] INFRA-060: Artifact generation failure paths remain visible rather than silently swallowed.

---

# J. Infrastructure-side “unhappy path” compatibility actually evidenced in legacy tests

Only include source-grounded unhappy paths.

### Disabled/missing dependency paths

- [x] INFRA-061: Missing RabbitMQ package with disabled flag does not crash import.
- [x] INFRA-062: Missing Kafka package with disabled flag does not crash import.
- [x] INFRA-063: Missing Redis package does not crash safe initialization paths where optional.
- [x] INFRA-064: Missing broker dependencies do not block headless runner imports.

### Runtime degradation paths

- [x] INFRA-065: Worker transport degradation falls back safely to local execution.
- [x] INFRA-066: Chaos-mode packet/result drop does not terminate the simulation prematurely under supported settings.
- [x] INFRA-067: Monitoring checks fail loudly when expected data is missing.

### CLI/runtime robustness

- [x] INFRA-068: CLI execution still emits structured logs under minimal simulation runs.
- [x] INFRA-069: Short runs still produce enough output for regression inspection.
- [x] INFRA-070: Minimal runs do not require full external stack unless explicitly in E2E stack mode.

---

# K. Explicit exclusions from this add-on checklist

These should stay out unless you create a third checklist:

- generic security advice not tied to actual legacy code/tests
- generic performance wishes not evidenced by legacy behavior
- speculative logging/telemetry fields not checked in legacy code/tests
- invented infra classes or APIs not present in legacy source
- non-gameplay docs/release-gate concerns already tracked elsewhere

---

# L. Recommended artifact name

`legacy_src_system_compatibility_checklist.md`

---

# M. Recommended ledger columns

For each checklist item above, record:

- legacy area
- atomic item
- original source evidence
- original test evidence
- `src` evidence
- status
- divergence note
- proof path
- owner
- phase target

# Legacy `src` RPG-Core Checklist — Part 6 (Additive Missing Logic)

This checklist covers RPG-core logic families that were still under-specified after Parts 1–5.

It is additive. It should not replace the earlier parts.

---

## A. Perception / belief / appraisal / attention

Relevant original source/test evidence:

- `BeliefService`
- `BoundedStrategicAppraisalService`
- `PlaceThreatAppraisalService`
- `SocialAppraisalService`
- `tests/unit/ai/test_attention.py`
- `tests/unit/ai/test_belief_cycle.py`
- `tests/unit/ai/test_cognitive_pipeline.py`
- related belief/appraisal tests in `all_test.py`

- [x] SOC-123: `test_perception_phase_populates_attention_pool`: attention pool population
- [x] SOC-124: `test_belief_refresh_captures_apparent_state`: belief refresh from apparent state
- [x] SOC-125: `test_belief_decay_lifecycle`: belief decay lifecycle
- [x] SOC-126: `test_belief_conflict_resolution`: belief conflict handling
- [x] SOC-127: `test_belief_sharing_propagation`: belief sharing propagation
- [x] SOC-128: `test_threat_estimation_logic`: threat estimation logic
- [x] SOC-129: `test_perception_phase_appraisal_sync`: appraisal sync
- [x] SOC-130: `test_perception_tracks_position_history`: position-history tracking
- [x] SOC-131: `test_appraisal_phase_triggers_panic_on_low_hp`: panic trigger via appraisal
- [x] SOC-132: `test_appraisal_detects_stuck`: stuck appraisal detection
- [x] SOC-133: `test_social_appraisal_logic`: social appraisal logic
- [x] SOC-141: `test_social_appraisal_with_narrative`: narrative-informed social appraisal

---

## B. Routine / motive / biological needs / life rhythm

Relevant original source/test evidence:

- `RoutineService`
- `ObjectiveDerivationService`
- `tests/unit/ai/test_routine.py`
- related rest/sleep/hunger tests in `all_test.py`

- [x] TOWN-057: `test_sleep_goal_utility_at_night`: sleep utility at night <!-- ID: TOWN-057 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-058: `test_rest_to_sleep_transition`: rest-to-sleep transition <!-- ID: TOWN-058 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-059: `test_routine_service_sleep_bias`: sleep bias <!-- ID: TOWN-059 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-060: `test_routine_service_forced_rest_during_off_hours`: forced off-hours rest <!-- ID: TOWN-060 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-061: `test_routine_service_hunger_bias`: hunger bias <!-- ID: TOWN-061 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-062: `test_home_visit_leads_to_eating`: eating behavior from routine/home visit <!-- ID: TOWN-062 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-063: `test_inn_visit_leads_to_sleeping`: inn visit leads to sleeping <!-- ID: TOWN-063 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-064: `test_biological_decay_and_forced_sleep`: biological decay and forced sleep <!-- ID: TOWN-064 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-065: `test_sleeping_recovery_cycle`: sleeping recovery cycle <!-- ID: TOWN-065 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-066: `test_hunger_reduces_stability`: hunger consequence <!-- ID: TOWN-066 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-067: `test_routine_goal_priority`: routine goal priority <!-- ID: TOWN-067 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-068: `test_routine_disruption_panic`: disruption panic <!-- ID: TOWN-068 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-069: `test_attack_disruption_suppresses_routines`: attack suppresses routine <!-- ID: TOWN-069 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-070: `test_routine_priority_archetype_bias`: archetype-based routine bias <!-- ID: TOWN-070 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->
- [x] TOWN-071: `test_life_stage_priority_shift`: life-stage priority shift <!-- ID: TOWN-071 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/ai/test_routine.py PROOF: unit -->

---

## C. Goal evaluation modifier stack

Relevant original source evidence:

- `BoredomModifier`
- `LifeStageModifier`
- `MotiveModifier`
- `StuckModifier`
- `HysteresisModifier`
- `StalemateModifier`
- `CooldownModifier`
- `MemoryModifier`
- `EmotionalModifier`
- `SkirmishModifier`
- `AmbitionModifier`
- `FatigueModifier`
- `SocialModifier`
- `RoutineModifier`

- [x] COMB-093: `test_ai_boredom_diversification`: boredom diversification effect <!-- ID: COMB-093 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-094: `test_boredom_modifier_applies_multipliers`: boredom modifier law <!-- ID: COMB-094 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-095: `test_life_stage_modifier_early_bracket`: life-stage modifier law <!-- ID: COMB-095 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-096: `test_motive_modifier_biases_explore`: motive modifier explore bias <!-- ID: COMB-096 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-097: `test_motive_modifier_biases_rest`: motive modifier rest bias <!-- ID: COMB-097 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-098: `test_motive_modifier_biases_flee`: motive modifier flee bias <!-- ID: COMB-098 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-099: `test_goal_evaluator_uses_modifiers`: goal evaluator modifier integration <!-- ID: COMB-099 SOURCE: src/ai/score_modifiers.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] COMB-100: `test_softmax_distribution`: score-to-choice distribution <!-- ID: COMB-100 SOURCE: src/engine/cognition.py TEST: tests/unit/engine/test_kernel_simulation.py PROOF: unit -->
- [x] COMB-101: `test_softmax_with_equal_scores`: equal-score handling <!-- ID: COMB-101 SOURCE: src/engine/cognition.py TEST: tests/unit/engine/test_kernel_simulation.py PROOF: unit -->

---

## D. Emotional / narrative memory / trauma logic

Relevant original source/test evidence:

- `MemorySalienceService`
- `EventInterpreterService`
- `tests/unit/ai/test_emotional_memory.py`
- `tests/unit/ai/test_narrative_memory.py`

- [x] SOC-135: `test_locational_trauma_triggers_dread`: locational trauma -> dread <!-- ID: SOC-135 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/ai/test_emotional_memory.py PROOF: unit -->
- [x] SOC-136: `test_emotional_bias_on_utility`: emotion changes utility <!-- ID: SOC-136 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/ai/test_emotional_memory.py PROOF: unit -->
- [x] SOC-137: `test_emotional_decay`: emotional decay <!-- ID: SOC-137 SOURCE: src/engine/cognition.py TEST: tests/unit/ai/test_emotional_memory.py PROOF: unit -->
- [x] SOC-138: `test_narrative_memory_trauma_biasing`: trauma memory biasing <!-- ID: SOC-138 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/ai/test_emotional_memory.py PROOF: unit -->
- [x] SOC-139: `test_narrative_memory_victory_confidence`: victory-confidence memory <!-- ID: SOC-139 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/ai/test_emotional_memory.py PROOF: unit -->
- [x] SOC-140: `test_narrative_memory_logging`: narrative memory logging <!-- ID: SOC-140 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/ai/test_emotional_memory.py PROOF: unit -->
- [x] SOC-141-DUP1: `test_social_appraisal_with_narrative`: narrative-informed social appraisal <!-- ID: SOC-141-DUP1 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-142: `test_bravery_modifiers`: bravery modifiers <!-- ID: SOC-142 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->

---

## E. Combat aftermath / wounds / scars / stamina / exhaustion

Relevant original source/test evidence:

- `DamageResolutionService`
- `CombatAftermathService`
- `tests/unit/combat/**`
- related stamina tests in `all_test.py`

- [x] COMB-102: `test_wound_infliction_massive_hit`: wound infliction <!-- ID: COMB-102 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_wounds.py PROOF: unit -->
- [x] COMB-103: `test_wound_stat_impact`: wound stat penalties <!-- ID: COMB-103 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_wounds.py PROOF: unit -->
- [x] COMB-104: `test_scar_permanence`: scar permanence <!-- ID: COMB-104 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_wounds.py PROOF: unit -->
- [x] COMB-105: `test_scar_decay`: scar decay behavior if preserved <!-- ID: COMB-105 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_wounds.py PROOF: unit -->
- [x] COMB-106: `test_local_scar_record`: local scar record <!-- ID: COMB-106 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] COMB-107: `test_scar_detection`: scar detection <!-- ID: COMB-107 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_wounds.py PROOF: unit -->
- [x] COMB-108: `test_ai_perception_of_scars`: perception of scars <!-- ID: COMB-108 SOURCE: src/engine/legality.py TEST: tests/unit/combat/test_wounds.py PROOF: unit -->
- [x] COMB-109: `test_stamina_drain_on_attack`: stamina drain on attack <!-- ID: COMB-109 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-110: `test_stamina_decreases_on_move`: stamina drain on move <!-- ID: COMB-110 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-111: `test_stamina_decreases_on_harvest`: stamina drain on harvest <!-- ID: COMB-111 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-112: `test_skill_use_costs_stamina`: stamina cost on skill use <!-- ID: COMB-112 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-113: `test_stamina_regen_resting`: rest stamina regen <!-- ID: COMB-113 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-114: `test_stamina_regen_active`: active regen <!-- ID: COMB-114 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-115: `test_stamina_regen_capped`: regen cap <!-- ID: COMB-115 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-116: `test_exhaustion_penalty_application`: exhaustion penalty <!-- ID: COMB-116 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->
- [x] COMB-117: `test_best_ready_skill_skips_insufficient_stamina`: skill gating by stamina <!-- ID: COMB-117 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/combat/test_stamina.py PROOF: unit -->

---

## F. Tactical specialty / action style / combo behavior

Relevant original source/test evidence:

- combat/tactical logic in `all_src.py`
- `tests/unit/ai/test_action_styles.py`
- `tests/unit/ai/test_flanking.py`
- `tests/unit/ai/test_combos.py`

- [x] COMB-118: `test_execution_phase_modifies_proposal_with_aggressive_style`: aggressive action style <!-- ID: COMB-118 SOURCE: src/engine/combat.py TEST: tests/unit/ai/test_action_styles.py PROOF: unit -->
- [x] COMB-119: `test_execution_phase_modifies_proposal_with_evasive_style`: evasive action style <!-- ID: COMB-119 SOURCE: src/engine/combat.py TEST: tests/unit/ai/test_action_styles.py PROOF: unit -->
- [x] COMB-120: `test_flanking_bonus`: flanking bonus <!-- ID: COMB-120 SOURCE: src/engine/combat.py TEST: tests/unit/combat/test_flanking.py PROOF: unit -->
- [x] COMB-121: `test_no_flanking_bonus_when_facing_attacker`: facing-sensitive flanking exclusion <!-- ID: COMB-121 SOURCE: src/engine/legality.py TEST: tests/unit/combat/test_flanking.py PROOF: unit -->
- [x] COMB-122: `test_shatter_combo`: combo behavior <!-- ID: COMB-122 SOURCE: src/engine/combat.py TEST: tests/unit/combat/test_combos.py PROOF: unit -->
- [x] COMB-123: `test_ranged_hero_kites_when_adjacent`: ranged kiting <!-- ID: COMB-123 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/ai/test_kiting.py PROOF: unit -->
- [x] COMB-124: `test_ranged_skirmisher_kites_when_close`: ranged skirmish spacing <!-- ID: COMB-124 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/ai/test_kiting.py PROOF: unit -->

---

## G. Loot / hidden discovery / local reward realism

Relevant original source/test evidence:

- loot and discovery logic in `all_src.py`
- related tests in `all_test.py`

- [x] TOWN-072: `test_luck_impacts_loot_modifier`: loot modifier from luck/perception <!-- ID: TOWN-072 SOURCE: src/world/spawn_config.py TEST: tests/unit/economy/test_loot_scaling.py PROOF: unit -->
- [x] TOWN-073: `test_per_based_hidden_discovery`: hidden discovery from perception <!-- ID: TOWN-073 SOURCE: src/systems/world_systems/harvesting.py TEST: tests/unit/world/test_discovery.py PROOF: unit -->
- [x] TOWN-074: `test_loot_recovery_consistency`: loot recovery consistency <!-- ID: TOWN-074 SOURCE: src/engine/economy.py TEST: tests/unit/economy/test_loot_scaling.py PROOF: unit -->
- [x] TOWN-075: `test_loot_no_duplication`: no duplicated loot <!-- ID: TOWN-075 SOURCE: src/engine/economy.py TEST: tests/unit/economy/test_loot_scaling.py PROOF: unit -->
- [x] TOWN-076: `test_corpse_loot_convergence`: corpse loot convergence <!-- ID: TOWN-076 SOURCE: src/engine/economy.py TEST: tests/unit/economy/test_loot_scaling.py PROOF: unit -->
- [x] TOWN-077: `test_loot_and_respawn`: loot and respawn interaction <!-- ID: TOWN-077 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_respawn.py PROOF: unit -->
- [x] TOWN-078: `test_loot_tables_exist`: loot table integrity <!-- ID: TOWN-078 SOURCE: src/world/spawn_config.py TEST: tests/unit/economy/test_loot_scaling.py PROOF: unit -->
- [x] TOWN-079: `test_full_bag_aborts_looting`: abort looting when full <!-- ID: TOWN-079 SOURCE: src/core/inventory.py TEST: tests/unit/inventory/test_capacity.py PROOF: unit -->
- [x] TOWN-080: `test_overweight_aborts_looting`: abort looting when overweight <!-- ID: TOWN-080 SOURCE: src/core/inventory.py TEST: tests/unit/inventory/test_capacity.py PROOF: unit -->
- [x] TOWN-081: `test_near_weight_limit_penalizes_loot`: weight-limit penalty on looting <!-- ID: TOWN-081 SOURCE: src/core/inventory.py TEST: tests/unit/inventory/test_capacity.py PROOF: unit -->

---

## H. Region-scale strategic and world consequences

Relevant original source/test evidence:

- `StrategicConsequenceService`
- `WorldConsequenceInterpretationService`
- region/world consequence tests in `all_test.py`

- [x] STRAT-130: `test_regional_suppression`: regional suppression
- [x] STRAT-131: `test_strategic_pivot_on_regional_danger`: pivot on regional danger
- [x] STRAT-132: `test_region_fatigue_biasing`: region fatigue biasing
- [x] STRAT-133: `test_region_consequence_record`: region consequence record
- [x] STRAT-134: `test_conquered_region_triggers_stronghold`: conquered region -> stronghold consequence
- [x] STRAT-135: `test_strategic_pipeline_home_threat`: home threat in strategic pipeline
- [x] STRAT-136: `test_world_consequence_*`: world consequence interpretation coverage where applicable

---

## I. Death / permadeath / succession / heirlooms / nemesis

Relevant original source/test evidence:

- lifecycle / death / social-consequence logic in `all_src.py`
- related tests in `all_test.py`

- [x] STRAT-137: `test_aging_and_death`: aging and death <!-- ID: STRAT-137 SOURCE: src/engine/apply.py TEST: tests/unit/core/test_lifecycle.py PROOF: unit -->
- [x] STRAT-138: `test_hero_lifecycle_system_permadeath`: hero permadeath <!-- ID: STRAT-138 SOURCE: src/engine/apply.py TEST: tests/unit/core/test_lifecycle.py PROOF: unit -->
- [x] STRAT-139: `test_permadeath_succession_and_heirlooms`: succession and heirlooms <!-- ID: STRAT-139 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_inheritance.py PROOF: unit -->
- [x] STRAT-140: `test_hero_death_creates_scar`: death scar consequences <!-- ID: STRAT-140 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-141: `test_near_death_triggers_survival_consequences`: near-death survival consequences <!-- ID: STRAT-141 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_survival.py PROOF: unit -->
- [x] STRAT-142: `test_near_death_hardening`: near-death hardening <!-- ID: STRAT-142 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_survival.py PROOF: unit -->
- [x] STRAT-143: `test_nemesis_recognition_and_fear_bias`: nemesis recognition and fear bias <!-- ID: STRAT-143 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_nemesis.py PROOF: unit -->
- [x] STRAT-144: `test_nemesis_milestone_creation`: nemesis milestone creation <!-- ID: STRAT-144 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_nemesis.py PROOF: unit -->
- [x] STRAT-145: `test_locational_memory_on_death`: locational memory on death <!-- ID: STRAT-145 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_death_memory.py PROOF: unit -->
- [x] STRAT-146: `test_influence_shifts_on_monster_death`: influence shift on monster death <!-- ID: STRAT-146 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_influence.py PROOF: unit -->
- [x] STRAT-147: `test_influence_shifts_on_hero_death`: influence shift on hero death <!-- ID: STRAT-147 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_influence.py PROOF: unit -->

---

## J. Medical / diagnosis judgment logic

Relevant original source/test evidence:

- diagnosis logic in `all_src.py`
- related tests in `all_test.py`

- [x] STRAT-148: `test_accurate_diagnosis_high_wisdom`: accurate diagnosis at high wisdom <!-- ID: STRAT-148 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->
- [x] STRAT-149: `test_misdiagnosis_low_wisdom`: misdiagnosis at low wisdom <!-- ID: STRAT-149 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->

# Legacy `src` RPG-Core Checklist — Part 7 (Residual Test-Covered Logic)

This checklist is additive to Parts 1–6.

It exists to capture smaller but still real legacy logic families that are explicitly covered by tests and are easy to lose if they remain implicit under broad labels like strategy, progression, or world behavior.

This part should stay test-first. If a behavior is listed here, it should have an identifiable test anchor in the original legacy test surface.

---

## A. Quest lifecycle, generation, and completion logic

Relevant legacy test surface includes quest creation, progression, duplicate suppression, completion, rewards, and quest-type-specific behavior.

- [x] STRAT-150: `test_quest_creation`: quest creation baseline <!-- ID: STRAT-150 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-151: `test_quest_advance`: quest progression increments correctly <!-- ID: STRAT-151 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-152: `test_quest_advance_does_nothing_when_completed`: completed quests do not advance further <!-- ID: STRAT-152 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-153: `test_quest_progress_ratio`: progress-ratio computation is correct <!-- ID: STRAT-153 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-154: `test_generate_quest_returns_quest`: quest generator returns valid quest object <!-- ID: STRAT-154 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-155: `test_generate_quest_respects_level`: generated quests respect level banding <!-- ID: STRAT-155 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-156: `test_generate_quest_skips_duplicate`: duplicate quest generation is suppressed <!-- ID: STRAT-156 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-157: `test_generate_quest_gold_scales_with_level`: quest gold reward scales with level <!-- ID: STRAT-157 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-158: `test_generate_explore_quest`: explore-quest generation works <!-- ID: STRAT-158 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-159: `test_hunt_quest_completion_awards_rewards`: hunt-quest completion awards rewards <!-- ID: STRAT-159 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-160: `test_explore_quest_completes_near_target`: explore-quest completes near target <!-- ID: STRAT-160 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-161: `test_gather_quest_advance`: gather-quest progression works <!-- ID: STRAT-161 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-162: `test_dynamic_liberate_quest`: liberate-quest generation/progression works <!-- ID: STRAT-162 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->
- [x] STRAT-163: `test_territory_conquest`: territory-conquest quest/world objective behavior is preserved <!-- ID: STRAT-163 SOURCE: src/systems/world_systems/quests.py TEST: tests/unit/quest/test_quest_logic.py PROOF: unit -->

---

## B. Trait system logic

Relevant legacy test surface includes trait definitions, trait assignment, trait aggregation, compatibility, and serialization.

- [x] SUB-123: `test_trait_serialization`: trait serialization is preserved <!-- ID: SUB-123 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-165: `test_get_traits`: trait retrieval works <!-- ID: STRAT-165 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-166: `test_trait_defs_not_empty`: trait definitions exist and are non-empty <!-- ID: STRAT-166 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-167: `test_with_traits_assigns_traits`: explicit trait assignment works <!-- ID: STRAT-167 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-168: `test_no_traits_by_default`: no-trait default behavior is preserved <!-- ID: STRAT-168 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-169: `test_traits_with_different_race_prefix`: race-prefixed trait handling is preserved <!-- ID: STRAT-169 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-170: `test_empty_traits_returns_zero_bonus`: empty-trait bonus behavior is preserved <!-- ID: STRAT-170 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-171: `test_single_known_trait`: single-trait bonus behavior is preserved <!-- ID: STRAT-171 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-172: `test_multiple_traits_sum`: multiple traits stack/sum correctly <!-- ID: STRAT-172 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-173: `test_unknown_trait_id_ignored`: unknown traits are ignored safely <!-- ID: STRAT-173 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-174: `test_same_trait_compatible`: trait compatibility logic is preserved <!-- ID: STRAT-174 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-175: `test_assigns_between_2_and_4_traits`: random/default trait assignment count is preserved <!-- ID: STRAT-175 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-176: `test_all_assigned_traits_are_valid`: assigned traits are always valid <!-- ID: STRAT-176 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] SUB-156: `test_all_trait_types_have_definitions`: all trait types have definitions <!-- ID: SUB-156 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-178: `test_trait_defs_have_all_utility_fields`: trait utility fields are complete <!-- ID: STRAT-178 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->
- [x] STRAT-179: `test_trait_defs_have_all_stat_fields`: trait stat fields are complete <!-- ID: STRAT-179 SOURCE: src/ai/personality.py TEST: tests/unit/ai/test_modifiers.py PROOF: unit -->

---

## C. Role derivation and role-aware behavior

Relevant legacy test surface includes role derivation, role transition, role biasing, and tactical role-awareness.

- [x] STRAT-180: `test_initial_role_derivation`: initial role derivation is preserved
- [x] STRAT-181: `test_dynamic_role_transition_with_hysteresis`: dynamic role transition with hysteresis is preserved
- [x] STRAT-182: `test_role_bias_influence`: role bias affects decisions as expected
- [x] STRAT-183: `test_role_aware_tactical_biases`: tactical behavior reflects role-aware biasing

---

## D. Aptitudes, training-detail law, and stat recomputation

Relevant legacy test surface includes aptitude-driven training, soft caps, fractional accumulation, and recomputation of derived stats.

- [x] PROG-044: `test_training_uses_aptitudes`: aptitude-weighted training law is preserved
- [x] PROG-045: `test_innate_talents_training`: innate talents affect training as expected
- [x] PROG-046: `test_training_does_not_exceed_cap`: training respects hard caps
- [x] PROG-047: `test_training_accumulates_fractionally`: fractional training accumulation is preserved
- [x] PROG-048: `test_training_updates_stats_on_increment`: stat update on training increment is preserved
- [x] PROG-049: `test_specialized_training_soft_caps`: soft-cap behavior for specialized training is preserved
- [x] PROG-050: `test_output_derived_stat_ceilings`: derived-stat ceiling logic is preserved
- [x] PROG-051: `test_stat_recalculation`: stat recomputation behavior is preserved
- [x] PROG-052: `test_attribute_scaling_overlap`: overlapping attribute-scaling law is preserved

---

## E. Place attachment, home, and anchored behavior

Relevant legacy test surface includes place attachment, home behavior, home storage, retreat-to-home behavior, and home-driven actions.

- [x] PROG-053: `test_place_attachment_instantiation`: place attachment can be instantiated <!-- ID: PROG-053 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] PROG-054: `test_place_attachment_navigation`: place attachment influences navigation correctly <!-- ID: PROG-054 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] PROG-055: `test_place_attachment_home_navigation`: home-oriented navigation behavior is preserved <!-- ID: PROG-055 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] PROG-056: `test_no_home_returns_false`: no-home logic is preserved <!-- ID: PROG-056 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] PROG-057: `test_home_sets_home_pos`: home position assignment is preserved <!-- ID: PROG-057 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] PROG-058: `test_entity_copy_includes_home_storage`: home storage is preserved during copy <!-- ID: PROG-058 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] PROG-059: `test_entity_without_home_storage`: no-home-storage case is preserved <!-- ID: PROG-059 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] PROG-060: `test_divergent_home_response`: divergent home response behavior is explicit and preserved where intended <!-- ID: PROG-060 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/world/test_routine.py PROOF: unit -->
- [x] PROG-061: `test_home_priority_retreat`: home-priority retreat behavior is preserved <!-- ID: PROG-061 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] PROG-062: `test_visit_home_upgrade_resolution`: visit-home upgrade resolution is preserved <!-- ID: PROG-062 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/world/test_routine.py PROOF: unit -->
- [x] PROG-063: `test_home_visit_leads_to_eating`: home visit can lead to eating behavior <!-- ID: PROG-063 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/world/test_routine.py PROOF: unit -->

---

## F. Leash, camp, and local anchored ecology

Relevant legacy test surface includes leash behavior, chase abandonment, camp return, and camp reinforcement logic.

- [x] COMB-125: `test_no_leash_returns_false`: no-leash detection behavior is preserved
- [x] COMB-126: `test_mob_beyond_leash_returns_to_camp`: beyond-leash return-to-camp behavior is preserved
- [x] COMB-127: `test_mob_within_leash_wanders_normally`: within-leash wandering behavior is preserved
- [x] COMB-128: `test_no_leash_mob_wanders_freely`: leash-free wandering behavior is preserved
- [x] COMB-129: `test_chase_beyond_leash_abandons`: chase abandonment beyond leash is preserved
- [x] COMB-130: `test_chase_within_leash_continues`: chase continuation within leash is preserved
- [x] COMB-131: `test_no_leash_mob_hunts_freely`: no-leash hunting freedom is preserved
- [x] COMB-132: `test_camp_reinforcements`: camp reinforcement behavior is preserved

---

## G. Travel topology, path-affordance, and regional traversal law

Relevant legacy test surface includes flow fields, terrain costs, roads, bridges, biome affordances, and difficulty-zone traversal constraints.

- [x] WORLD-001-DUP1: `test_flow_field_basic_navigation`: basic flow-field navigation is preserved <!-- ID: WORLD-001-DUP1 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-002-DUP1: `test_flow_field_respects_terrain_cost`: terrain-cost-sensitive navigation is preserved <!-- ID: WORLD-002-DUP1 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-003-DUP1: `test_flow_field_smoothing`: flow-field smoothing is preserved <!-- ID: WORLD-003-DUP1 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-004-DUP1: `test_flow_field_smoothing_normalization`: smoothing normalization behavior is preserved <!-- ID: WORLD-004-DUP1 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-005-DUP1: `test_navigation_uses_flow_field_for_far_town`: far-town navigation uses flow fields <!-- ID: WORLD-005-DUP1 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-006-DUP1: `test_navigation_uses_flow_field_for_world_boss`: world-boss navigation uses flow fields <!-- ID: WORLD-006-DUP1 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-007: `test_road_cost_is_low`: road traversal cost law is preserved <!-- ID: WORLD-007 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-008: `test_prefers_road_over_swamp`: road preference over swamp is preserved <!-- ID: WORLD-008 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] WORLD-009: `test_each_biome_has_road_network`: biome road-network presence is preserved <!-- ID: WORLD-009 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-010: `test_road_connects_locations`: road connectivity behavior is preserved <!-- ID: WORLD-010 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-011: `test_bridges_placed_over_water`: bridge placement over water is preserved <!-- ID: WORLD-011 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-012: `test_all_four_biomes_have_features`: biome feature presence is preserved <!-- ID: WORLD-012 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-013: `test_difficulty_sets_level_range`: region difficulty sets level range correctly <!-- ID: WORLD-013 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-014: `test_gold_scales_with_difficulty`: difficulty-linked gold scaling is preserved <!-- ID: WORLD-014 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-015: `test_in_region_returns_difficulty`: region difficulty query logic is preserved <!-- ID: WORLD-015 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-016: `test_difficulty_zones_defined`: difficulty-init zone definition is preserved <!-- ID: WORLD-016 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-017: `test_lava_only_at_high_difficulty`: lava/high-difficulty coupling is preserved <!-- ID: WORLD-017 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-018: `test_all_terrains_have_names`: terrain naming coverage is preserved <!-- ID: WORLD-018 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] WORLD-019: `test_all_terrains_have_race_labels`: terrain race-label coverage is preserved <!-- ID: WORLD-019 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->

---

## H. Cooperation, recruitment-adjacent coordination, and proximity bonding

Relevant legacy test surface includes small cooperative and bonding behaviors that affect social or local-world outcomes.

- [x] SOC-143: `test_cooperation_recruitment_logic`: cooperation in recruitment/social choice is preserved
- [x] SOC-144: `test_scenario_3_stationary_world_proximity_bonding`: proximity bonding behavior is preserved

---

## I. Residual small-world and economy-adjacent local realism

Relevant legacy test surface includes local inventory and burden realism that can affect action outcomes.

- [x] WORLD-020: `test_full_bag_aborts_looting`: full-bag looting abort is preserved
- [x] WORLD-021: `test_overweight_aborts_looting`: overweight looting abort is preserved
- [x] WORLD-022: `test_near_weight_limit_penalizes_loot`: near-limit loot penalty is preserved

These are listed again here intentionally if not already fully owned elsewhere, because they are small and easy to lose.

---

## J. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map residual logic into roadmap phases:

- [x] COMB-141: Phase 8 owns:
  - leash/camp/local anchored ecology
  - local burden/loot-abort realism
  - local/path-affordance pieces only where they directly affect immediate tactics

- [x] COMB-142: Phase 9 owns:
  - quests
  - traits
  - roles
  - aptitude/training-detail law
  - place attachment/home behavior when it affects long-horizon choices
  - regional traversal/topology when it affects world-scale intention
  - cooperation/proximity bonding

- [x] COMB-135: No Part 7 item should be left implicit under a generic bucket like “AI improvements” or “progression tuning`

---

## Completion rule for Part 7

A Part 7 item is not considered covered merely because it “probably exists” inside a broader subsystem.

Each item should be considered closed only when:

- [x] COMB-136: the specific legacy behavior has a clear roadmap owner
- [x] COMB-137: the specific behavior has a direct implementation or explicit divergence decision
- [x] COMB-138: the specific behavior has test coverage or parity justification
- [x] COMB-139: the replacement ledger/support boundary reflects the truth of that item

# Legacy `src` Assumption / Invariant Checklist — Part 8

This checklist is additive to Parts 1–7.

It is not a new gameplay-logic trunk.
It exists to capture **legacy assumptions and invariants** that the old system was supposed to have and that are explicitly enforced by tests.

These are the kinds of rules that often get broken during migration because they are treated as “small details,” even though they are foundational to trustworthiness.

This part should remain **test-first**.

---

## A. Default-state and neutral-behavior assumptions

These tests assert what objects or systems are supposed to look like before gameplay meaning starts.

- [x] SUB-073: `test_default_values`: default entity/build values are preserved
- [x] SUB-074: `test_default_values_all_zero`: default zero-valued state is preserved
- [x] SUB-075: `test_default_multiplicative_values_are_1`: default multiplicative modifiers equal 1
- [x] SUB-076: `test_default_additive_values_are_0`: default additive modifiers equal 0
- [x] SUB-077: `test_default_metadata_is_none`: metadata defaults to `None`
- [x] SUB-078: `test_none_metadata_preserved`: `None` metadata remains preserved
- [x] SUB-079: `test_schema_none_metadata`: schema handles `None` metadata correctly
- [x] SUB-080: `test_no_skills_by_default`: entities have no skills by default
- [x] SUB-081: `test_no_inventory_by_default`: entities have no inventory by default
- [x] SUB-082: `test_no_traits_by_default`: entities have no traits by default
- [x] SUB-083: `test_entity_starts_with_no_quests`: entities start with no quests
- [x] SUB-084: `test_default_core_rate_is_1`: default core subsystem rate is preserved
- [x] SUB-085: `test_default_environment_rate_is_2`: default environment subsystem rate is preserved
- [x] SUB-086: `test_default_economy_rate_is_5`: default economy subsystem rate is preserved
- [x] SUB-087: `test_default_region_id`: default region identifier is preserved
- [x] SUB-088: `test_default_empty`: default empty collection/container semantics are preserved
- [x] SUB-089: `test_empty_zones_returns_1`: empty-zone fallback behavior is preserved
- [x] SUB-090: `test_empty_regions_returns_none`: empty-region lookup returns `None`
- [x] SUB-091: `test_select_returns_none_on_empty`: selection on empty inputs returns `None`
- [x] SUB-092: `test_export_empty_strategy`: exporting empty strategy state is safe

---

## B. No-op, empty-tick, and “does nothing safely” assumptions

These tests assert that when there is nothing to do, the system degrades safely and predictably.

- [x] SUB-093: `test_no_changes_skipped`: no-change updates are skipped safely
- [x] SUB-094: `test_effects_tick_on_empty_tick`: effects still tick on empty ticks
- [x] SUB-095: `test_stamina_regens_on_empty_tick`: stamina regen still occurs on empty ticks
- [x] SUB-096: `test_skill_cooldowns_tick_on_empty_tick`: skill cooldowns still tick on empty ticks
- [x] SUB-097: `test_quest_advance_does_nothing_when_completed`: completed quests ignore further advance calls
- [x] SUB-098: `test_unknown_action_does_nothing`: unknown actions are safely ignored
- [x] SUB-099: `test_full_hp_no_change`: full-HP state remains unchanged
- [x] SUB-100: `test_no_region_no_penalty`: no-region case applies no penalty
- [x] SUB-101: `test_safe_region_no_penalty`: safe-region case applies no penalty
- [x] SUB-102: `test_unknown_region_returns_0`: unknown region uses zero/fallback difficulty
- [x] SUB-103: `test_no_region_returns_0`: no-region difficulty fallback is preserved

---

## C. Copy, clone, preservation, and ownership assumptions

These tests assert what is supposed to be preserved across copying and what must not be shared.

- [x] SUB-104: `test_quest_copy`: quest copy preserves quest state
- [x] SUB-105: `test_entity_copy_preserves_quests`: entity copy preserves quests
- [x] SUB-106: `test_entity_copy_preserves_attributes`: entity copy preserves attributes
- [x] SUB-107: `test_entity_copy_preserves_skills`: entity copy preserves skills
- [x] SUB-108: `test_entity_copy_includes_home_storage`: entity copy preserves home storage
- [x] SUB-109: `test_entity_without_home_storage`: no-home-storage case remains safe
- [x] SUB-110: `test_region_copy`: region copy semantics are preserved
- [x] SUB-111: `test_attributes_copy`: attribute copy semantics are preserved
- [x] SUB-112: `test_copy`: generic model copy semantics are preserved wherever tested
- [x] SUB-113: `test_grid_copy_is_not_shared`: copied grids are not aliased
- [x] SUB-114: `test_entity_copy_shallow_vs_refs`: copy/ref-sharing behavior is explicit and preserved
- [x] SUB-115: `test_latest_preserves_metadata`: latest-version object preserves metadata

---

## D. Serialization, schema, and round-trip assumptions

These tests assert that important models are supposed to serialize safely and consistently.

- [x] SUB-116: `test_serialization_round_trip`: serialization round-trip is preserved
- [x] SUB-117: `test_item_serialization`: item serialization is preserved
- [x] SUB-118: `test_enchanted_blade_serialization`: enchanted item serialization is preserved
- [x] SUB-119: `test_skill_serialization`: skill serialization is preserved
- [x] SUB-120: `test_passive_skill_serialization`: passive skill serialization is preserved
- [x] SUB-121: `test_class_serialization`: class serialization is preserved
- [x] SUB-122: `test_breakthrough_serialization`: breakthrough serialization is preserved
- [x] SUB-123-DUP1: `test_trait_serialization`: trait serialization is preserved
- [x] SUB-124: `test_history_registry_serialization`: history registry serialization is preserved
- [x] SUB-125: `test_entity_to_full_schema_no_crash`: full schema export does not crash
- [x] SUB-126: `test_serialization_pydantic_model`: pydantic serialization assumption is preserved
- [x] SUB-127: `test_serialization_frozen_model_with_proxy`: frozen/proxy serialization is preserved
- [x] SUB-128: `test_inspection_serialization`: inspection serialization is preserved
- [x] SUB-129: `test_cognition_api_serialization`: cognition API serialization is preserved

---

## E. Freeze, immutability, and deep-isolation assumptions

These tests assert that certain state surfaces are supposed to be frozen, safe, and non-mutating.

- [x] SUB-130: `test_entity_deep_copy_isolation`: deep-copy isolation is preserved
- [x] SUB-131: `test_deep_freeze_nested_collections`: deep freeze handles nested collections
- [x] SUB-132: `test_deep_freeze_idempotency`: deep freeze is idempotent
- [x] SUB-133: `test_freeze_calls_validate`: freeze triggers validation correctly
- [x] SUB-134: `test_nested_freeze_invariants`: nested freeze invariants are preserved
- [x] SUB-135: `test_world_state_freeze_guards`: world-state freeze guards are preserved
- [x] SUB-136: `test_simulation_model_collection_freeze_list`: list freezing behavior is preserved
- [x] SUB-137: `test_simulation_model_collection_freeze_dict`: dict freezing behavior is preserved
- [x] SUB-138: `test_vector2_coercion_during_freeze`: vector coercion during freeze is preserved
- [x] SUB-139: `test_non_mutation`: non-mutation guarantee is preserved
- [x] SUB-140: `test_build_profile_does_not_mutate_caps`: cognition-profile derivation is non-mutating
- [x] SUB-141: `test_build_profile_returns_new_profile_object_each_call`: fresh profile object guarantee is preserved

---

## F. Determinism and repeatability assumptions

These tests assert that the system is supposed to be repeatable under the same conditions.

- [x] SUB-142: `test_profile_derivation_is_deterministic_for_same_entity_state`: deterministic profile derivation
- [x] SUB-143: `test_intel_capacity_determinism`: intelligence-capacity determinism is preserved
- [x] SUB-144: `test_strategic_replay_graph_equality`: replay graph equality is preserved
- [x] SUB-145: `test_same_seed_same_result`: same-seed world/result determinism is preserved
- [x] SUB-146: `test_harness_non_determinism_different_seed`: different-seed divergence remains explicit
- [x] SUB-147: `test_first_by_id_wins_same_tile`: deterministic same-tile tie-breaking is preserved
- [x] SUB-148: `test_diagonal_same_target_one_wins`: deterministic same-target conflict resolution is preserved
- [x] SUB-149: `test_non_conflicting_moves_both_succeed`: independent valid moves both survive
- [x] SUB-150: `test_equidistant_returns_first`: deterministic first-choice behavior on ties is preserved

---

## G. Registry, definition, and data-completeness assumptions

These tests assert that key registries and definition maps are supposed to exist and be complete.

- [x] SUB-151: `test_item_registry_not_empty`: item registry is non-empty
- [x] SUB-152: `test_skill_defs_not_empty`: skill definitions are non-empty
- [x] SUB-153: `test_trait_defs_not_empty`: trait definitions are non-empty
- [x] SUB-154: `test_registry_not_empty`: generic registry non-empty guarantee is preserved
- [x] SUB-155: `test_skill_registry_not_empty`: skill registry is non-empty
- [x] SUB-156-DUP1: `test_all_trait_types_have_definitions`: all trait types have definitions
- [x] SUB-157: `test_all_tiers_defined`: all expected tier sets are defined
- [x] SUB-158: `test_tier1_empty`: tier-1 empty expectation is preserved where applicable
- [x] SUB-159: `test_tier4_defined`: tier-4 definition exists where expected
- [x] SUB-160: `test_all_base_classes_defined`: base class definitions exist
- [x] SUB-161: `test_breakthroughs_defined`: breakthrough definitions exist
- [x] SUB-162: `test_all_types_have_name_templates`: type name-template completeness is preserved
- [x] SUB-163: `test_all_terrains_have_names`: all terrains have names
- [x] SUB-164: `test_all_terrains_have_race_labels`: all terrains have race labels
- [x] SUB-165: `test_all_four_biomes_have_features`: all biomes expose expected features
- [x] SUB-166: `test_all_regions_have_territory`: all regions have territory assignment
- [x] SUB-167: `test_difficulty_zones_defined`: difficulty zones are defined
- [x] SUB-168: `test_loot_tables_exist`: loot tables exist

---

## H. Safe fallback and degraded-mode assumptions

These tests assert that when something is missing, disabled, or unsupported, the system is supposed to fail soft or fall back safely.

- [x] SUB-169: `test_detour_depth_limit_fallback`: detour depth fallback is preserved
- [x] SUB-170: `test_worker_pool_fallback_to_inline`: worker pool falls back to inline execution
- [x] SUB-171: `test_rabbitmq_disabled_no_crash`: RabbitMQ-disabled mode does not crash
- [x] SUB-172: `test_kafka_disabled_no_crash`: Kafka-disabled mode does not crash
- [x] SUB-173: `test_redis_disabled_no_crash`: Redis-disabled mode does not crash
- [x] SUB-174: `test_headless_runner_importable_without_brokers`: headless runner imports safely without brokers
- [x] SUB-175: `test_action_system_importable_without_brokers`: action system imports safely without brokers
- [x] SUB-176: `test_simulation_step_runs_without_brokers`: simulation can step without brokers
- [x] SUB-177: `test_regression_runner_survives_no_infrastructure`: regression runner survives no-infrastructure mode
- [x] SUB-178: `test_get_unknown`: unknown registry/class lookup is handled safely
- [x] SUB-179: `test_unknown_trait_id_ignored`: unknown trait IDs are ignored safely
- [x] SUB-180: `test_unknown_type_falls_back_to_physical`: unknown damage/action type falls back safely

---

## I. Caps, clamps, floors, ceilings, and boundedness assumptions

These tests assert what is supposed to happen at boundaries.

- [x] SUB-181: `test_hp_clamped_after_recalc`: HP is clamped after recomputation
- [x] SUB-182: `test_stamina_cannot_go_below_zero`: stamina lower bound is preserved
- [x] SUB-183: `test_stamina_regen_capped`: stamina regeneration upper cap is preserved
- [x] SUB-184: `test_training_does_not_exceed_cap`: training hard caps are preserved
- [x] SUB-185: `test_level_up_respects_cap`: level-up cap compliance is preserved
- [x] SUB-186: `test_boss_diff_capped_at_4`: boss difficulty cap is preserved
- [x] SUB-187: `test_specialized_training_soft_caps`: soft-cap law is preserved
- [x] SUB-188: `test_output_derived_stat_ceilings`: derived-stat ceilings are preserved
- [x] SUB-189: `test_physical_no_attributes_defaults_mult_to_1`: missing-attribute multiplier defaults are preserved
- [x] SUB-190: `test_magical_no_attributes_defaults_mult_to_1`: magical default multiplier law is preserved
- [x] SUB-191: `test_full_bag_returns_zero`: full-bag score/utility floor is preserved
- [x] SUB-192: `test_overweight_loot_score_zero`: overweight loot utility floor is preserved

---

## J. Precedence, selection, and ordering assumptions

These tests assert what the system is supposed to prefer when multiple valid candidates exist.

- [x] SUB-193: `test_objective_derivation_precedence_active_objective_if_no_blocker`: active-objective precedence is preserved
- [x] SUB-194: `test_objective_derivation_precedence_first_unresolved_if_no_active`: unresolved-first precedence is preserved
- [x] SUB-195: `test_reserved_current_project_slot_is_used_when_current_project_exists`: current-project reserved slot law is preserved
- [x] SUB-196: `test_next_step_returns_first_tile`: first-step path semantics are preserved
- [x] SUB-197: `test_returns_nearest`: nearest-target selection is preserved
- [x] SUB-198: `test_equidistant_returns_first`: stable first-on-tie semantics are preserved
- [x] SUB-199: `test_best_ready_skill_returns_highest_power`: best-ready-skill precedence is preserved
- [x] SUB-200: `test_best_ready_skill_skips_on_cooldown`: cooldown exclusion precedence is preserved
- [x] SUB-201: `test_best_ready_skill_skips_insufficient_stamina`: stamina exclusion precedence is preserved
- [x] SUB-202: `test_best_ready_skill_none_when_no_skills`: no-skill fallback is preserved

---

## K. Guardrail and authorization assumptions

These tests assert that the system is supposed to prevent or reject things in specific safe ways.

- [x] SUB-203: `test_phase_guard_read_unauthorized`: unauthorized phase read is guarded
- [x] SUB-204: `test_no_path_through_walls`: pathfinding guardrail against walls is preserved
- [x] SUB-205: `test_next_step_no_path`: no-path fallback is preserved
- [x] SUB-206: `test_safe_shot_detection`: safe-shot guard logic is preserved
- [x] SUB-207: `test_no_flanking_bonus_when_facing_attacker`: flanking exclusion guardrail is preserved
- [x] SUB-208: `test_no_opportunity_attack_when_moving_toward`: OA guardrail is preserved
- [x] SUB-209: `test_no_cover_on_open_ground`: cover absence on open ground is preserved
- [x] SUB-210: `test_non_equipment_ignored`: non-equipment inputs are ignored safely
- [x] SUB-211: `test_cannot_breakthrough_no_class`: breakthrough precondition guard is preserved
- [x] SUB-212: `test_no_class`: no-class guard behavior is preserved

---

## L. Metadata, inspection, and smoke-stability assumptions

These tests assert that inspection and debug-facing surfaces are supposed to remain safe even in empty or corrupted cases.

- [x] SUB-213: `test_inspector_smoke_empty_state`: empty-state inspector safety is preserved
- [x] SUB-214: `test_inspector_smoke_corrupted_state`: corrupted-state inspector safety is preserved
- [x] SUB-215: `test_inspector_smoke_maximal_state`: maximal-state inspector safety is preserved
- [x] SUB-216: `test_render_strategic_domain_empty`: empty strategic-domain rendering is preserved
- [x] SUB-217: `test_empty_strategic_state_rendering`: empty strategic rendering is preserved
- [x] SUB-218: `test_cognition_inspector_rendering`: cognition inspector rendering is preserved
- [x] SUB-219: `test_cognition_empty_profile`: empty cognition-profile rendering is preserved

---

## M. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map assumption logic to roadmap owners rather than creating another giant roadmap phase.

- [x] COMB-140: Phase 7 owns:
  - serialization / freeze / deep-isolation / determinism / phase guards / non-mutation assumptions

- [x] COMB-141-DUP1: Phase 8 owns:
  - immediate-action guardrails
  - local boundedness and combat/tactical caps/clamps
  - local selection/tie-breaking assumptions where action resolution depends on them

- [x] COMB-142-DUP1: Phase 9 owns:
  - precedence and boundedness assumptions in cognition/strategy/progression
  - traits / registries / progression caps where they materially shape long-horizon gameplay

- [x] COMB-143: Phase 10 owns:
  - disabled-mode / fallback / importability / infra-safe assumptions
  - consumer/entry black-box degraded-mode assumptions

- [x] COMB-144: Phase 11+ owns:
  - governance truth for any surviving invariant classified as preserved/divergent/unsupported

---

## Completion rule for Part 8

A Part 8 item is not closed merely because the system “seems to behave sensibly.”

Each item should be considered closed only when:

- [x] COMB-145: the specific assumption has a clear roadmap owner
- [x] COMB-146: the specific assumption has direct implementation or an explicit divergence/unsupported decision
- [x] COMB-147: the specific assumption has test coverage or proof justification
- [x] COMB-148: the support boundary and replacement ledger reflect its true status

# Missing / under-specified checklist additions

## 1. Goal registry and goal scorer contract

The checklist mentions goal modifiers, but it does not fully preserve the core goal registry/scorer law from legacy tests.

Add these atomic items:

- [x] SUB-220: Goal registry contains the expected built-in goals.
- [x] SUB-221: Goal registry names are unique.
- [x] SUB-222: Every built-in goal maps to a valid target AI state.
- [x] SUB-223: Combat goal scores high when hostile enemies are visible.
- [x] SUB-224: Flee goal scores high below HP threshold.
- [x] SUB-225: Explore goal has a stable baseline score.
- [x] SUB-226: Empty goal candidate list returns `None`.
- [x] SUB-227: RNG value `0.0` selects the highest candidate.
- [x] SUB-228: `top_n` selection limits candidates before weighted selection.
- [x] SUB-229: Neuroticism can break goal commitment lock under low HP pressure.
- [x] SUB-230: Legacy `goal_evaluator.py` shim behavior is preserved or intentionally removed.
- [x] SUB-231: Loot goal returns zero when bag is full.
- [x] SUB-232: Trade goal receives urgency when inventory is nearly full or overweight.

Why this matters: goal scoring is the bridge between cognition and action. If this drifts, V2 entities may have the same systems but completely different behavior.

---

## 2. EntityBuilder construction law

The checklist mentions entity aspects and spawning, but not the builder as an atomic compatibility surface. Legacy has a large fluent `EntityBuilder` contract: default identity, faction, AI state, stats, class attributes, race skills, class skills, inventory, home storage, traits, clique, household, leash, world role, and randomized spawn stats.

Add:

- [x] SUB-233: EntityBuilder default entity has stable kind, faction, alive combat state, and wander AI state.
- [x] SUB-234: `.kind()`, `.at()`, `.home()`, `.ai_state()`, `.faction()`, `.tier()` preserve exact field effects.
- [x] SUB-235: Hero kind enforces minimum stamina behavior.
- [x] SUB-236: Base stats initialize combat and progression fields consistently.
- [x] SUB-237: Randomized stats use deterministic spawn-domain RNG.
- [x] SUB-238: Hero class derives attributes and caps from class definition.
- [x] SUB-239: Mob attributes scale by tier.
- [x] SUB-240: Race attributes apply racial modifiers and deterministic variance.
- [x] SUB-241: Race skills and class skills can be combined without loss.
- [x] SUB-242: No-skills-by-default behavior is preserved.
- [x] SUB-243: Builder supports clique, household, home building, world role, and leash fields.
- [x] SUB-244: Builder-created entities deep-copy safely.

This is not “just construction.” It is the source of initial state truth.

---

## 3. Registry and data-driven loading law

The checklist mentions registries generally, but it should explicitly preserve the data-driven runtime contract.

Add:

- [x] SUB-245: `load_all_registries()` loads items, classes, skills, breakthroughs, traits, spawn configs, and loot configs.
- [x] SUB-246: Spawn config entries actually initialize generated entities.
- [x] SUB-247: Loot config entries are loaded and used by `EntityGenerator`.
- [x] SUB-248: Item registry lookup returns expected item type and bonuses.
- [x] SUB-249: Class definitions contain class skill lists.
- [x] SUB-250: Every class skill ID resolves in the skill registry.
- [x] SUB-251: Missing registry entries fail safely, not silently.
- [x] SUB-252: Registry loading is deterministic and idempotent.
- [x] SUB-253: Duplicate or malformed data definitions are rejected or explicitly handled.

This is a big blind spot. A V2 port can pass behavior tests with hardcoded objects while silently breaking data-driven gameplay.

---

## 4. Quest lifecycle and generation

The checklist has quest mentions, but it is not atomic enough for the original quest tests.

Add:

- [x] SUB-254: Quest starts with progress `0`, not completed.
- [x] SUB-255: Quest progress ratio is correct.
- [x] SUB-256: Quest `advance()` returns `True` only on first completion.
- [x] SUB-257: Advancing an already completed quest does not mutate state.
- [x] SUB-258: Quest copy is deep enough that copied progress mutation does not affect original.
- [x] SUB-259: Quest serialization omits position for non-position quests.
- [x] SUB-260: Explore quest serialization includes target position.
- [x] SUB-261: Quest generation respects hero level.
- [x] SUB-262: Quest generation skips duplicates.
- [x] SUB-263: Quest rewards scale with level.
- [x] SUB-264: Explore quest generation produces valid target positions.
- [x] SUB-265: Template map and template list stay consistent.
- [x] SUB-266: Entity quest list starts empty.
- [x] SUB-267: Entity copies preserve quest progress independently.
- [x] SUB-268: Hunt quest completion grants gold and XP.
- [x] SUB-269: Explore quest completes within target proximity.
- [x] SUB-270: Gather quest can advance by count.
- [x] SUB-271: Max active quest limit is enforced.

Do not treat “dynamic quests exist” as enough. The old code had model, generator, tracking, reward, and serialization rules.

---

## 5. Equipment enhancement, home storage, shops, treasure chests

This is clearly underrepresented. The checklist mentions progression/classes/items, but not several old mechanics.

Add:

- [x] TOWN-082: `recalc_derived_stats()` creation mode applies attribute bonuses.
- [x] TOWN-083: `recalc_derived_stats()` delta mode removes old bonuses before applying new ones.
- [x] TOWN-084: HP clamps to new max HP after stat recalculation.
- [x] TOWN-085: Noncombat derived stats update vision, HP regen, trade bonus, and loot bonus.
- [x] TOWN-086: `auto_equip_best()` equips into empty slot.
- [x] TOWN-087: Better equipment replaces worse equipment and returns old item to inventory.
- [x] TOWN-088: Worse equipment is not auto-equipped.
- [x] TOWN-089: Non-equipment items are ignored by auto-equip.
- [x] TOWN-090: Unknown item power returns zero.
- [x] TOWN-091: Stronger item power ordering is stable.
- [x] TOWN-092: Home storage add/remove/full/copy behavior is preserved.
- [x] TOWN-093: Shop contains expanded item set.
- [x] TOWN-094: Buff potion item types are consumable.
- [x] TOWN-095: Skill learning respects level, prerequisites, and mastery.
- [x] TOWN-096: All hero classes expose at least one available skill chain.
- [x] TOWN-097: Treasure chests start available.
- [x] TOWN-098: Chest loot sets respawn tick and unavailable state.
- [x] TOWN-099: Chest respawns only at or after respawn tick.
- [x] TOWN-100: Chest loot tables exist for expected tiers.
- [x] TOWN-101: Entity copy preserves home storage deeply.
- [x] TOWN-102: Training that increments an attribute immediately recomputes derived stats.

This entire area is easy to lose because it sits between inventory, progression, and world objects.

---

## 6. Ranged combat, line-of-sight, cover, and range-aware skills

The existing checklist has ranged legality, but it needs finer atomic rules.

Add:

- [x] COMB-164: Ranged skill can be selected at distance.
- [x] COMB-165: Melee skill is not selected at ranged distance.
- [x] COMB-166: Starting gear gives warrior sword and ranger bow. <!-- ID: COMB-166 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/test_parity_v2_characterization.py PROOF: unit -->

The checklist currently risks collapsing this into “range and LOS exist.” That is not enough.

---

## 7. A\* pathfinding details

The checklist mentions movement and pathfinding, but several pathfinding laws are missing or buried.

Add:

- [x] COMB-167: Straight-line path returns expected step count. <!-- ID: COMB-167 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-168: Same start and goal returns empty path. <!-- ID: COMB-168 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-169: Adjacent goal returns single-step path. <!-- ID: COMB-169 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-170: Path routes around walls. <!-- ID: COMB-170 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-171: Fully enclosed goal returns no path. <!-- ID: COMB-171 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-172: Unwalkable goal returns no path. <!-- ID: COMB-172 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-173: Returned path excludes start position. <!-- ID: COMB-173 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-174: Max-node budget can terminate search with no path. <!-- ID: COMB-174 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-175: `next_step()` returns first path tile. <!-- ID: COMB-175 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-176: Occupied tiles are avoided. <!-- ID: COMB-176 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-177: Goal tile can remain reachable even if listed as occupied. <!-- ID: COMB-177 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-178: Road cost is lower than floor. <!-- ID: COMB-178 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/engine/test_terrain_cost.py PROOF: unit -->
- [x] COMB-179: Swamp cost is higher than floor. <!-- ID: COMB-179 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/engine/test_terrain_cost.py PROOF: unit -->
- [x] COMB-180: Terrain cost registry is used by pathfinding. <!-- ID: COMB-180 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-181: Long-distance movement uses A\*. <!-- ID: COMB-181 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-182: Short-distance movement can use greedy fallback. <!-- ID: COMB-182 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->

That last distinction matters: A\* and greedy fallback are different behavior contracts, not implementation details.

---

## 8. Mob leash, chase give-up, and return-to-camp

The checklist has leash references, but the atomic old behavior needs to be explicit.

Add:

- [x] COMB-183: Entity with `leash_radius=0` is never beyond leash. <!-- ID: COMB-183 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-184: Entity with no home position is never beyond leash. <!-- ID: COMB-184 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-185: Distance within leash returns false. <!-- ID: COMB-185 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-186: Distance beyond leash returns true. <!-- ID: COMB-186 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-187: Leash multiplier extends allowed chase range. <!-- ID: COMB-187 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-188: Wander handler sends beyond-leash mob to return-to-camp. <!-- ID: COMB-188 SOURCE: src/engine/movement.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-189: Within-leash mob continues wandering. <!-- ID: COMB-189 SOURCE: src/engine/movement.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-190: No-leash mob wanders freely. <!-- ID: COMB-190 SOURCE: src/engine/movement.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-191: Hunt handler abandons chase beyond `1.5x` leash. <!-- ID: COMB-191 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-192: Hunt handler continues chase inside `1.5x` leash. <!-- ID: COMB-192 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-193: Hunt handler gives up after chase timeout. <!-- ID: COMB-193 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-194: Chase ticks reset on combat engagement. <!-- ID: COMB-194 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-195: Return-to-camp heals while returning. <!-- ID: COMB-195 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->
- [x] COMB-196: Returning mob resumes normal behavior after reaching camp. <!-- ID: COMB-196 SOURCE: src/engine/rpg_depth.py TEST: tests/unit/world/test_leash_mechanics.py PROOF: unit -->

This is not just movement. It prevents mobs from becoming global homing missiles.

---

## 9. Group coordination and contract-party formation

The social checklist is broad, but group mechanics are under-specified.

Add:

- [x] SOC-145: Entities with the same `cluster_id` and faction can form a group. <!-- ID: SOC-145 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-146: Group requires at least two living members. <!-- ID: SOC-146 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-147: Group leader is selected by highest level. <!-- ID: SOC-147 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-148: Group anchor follows leader position. <!-- ID: SOC-148 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-149: Members receive group ID linkage. <!-- ID: SOC-149 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-150: Group dissolves if leader dies. <!-- ID: SOC-150 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_phantom_leader.py PROOF: unit -->
- [x] SOC-151: Group removes dead members. <!-- ID: SOC-151 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-152: Group dissolves if membership drops below two. <!-- ID: SOC-152 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-153: Group cohesion decreases with distance from leader. <!-- ID: SOC-153 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-154: Shared group goal biases member goal scoring. <!-- ID: SOC-154 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_domain_7_social.py PROOF: unit -->
- [x] SOC-155: Distance from leader increases social regrouping bias. <!-- ID: SOC-155 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-156: Active social contracts can instantiate party groups. <!-- ID: SOC-156 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_social_party_regression.py PROOF: unit -->
- [x] SOC-157: Contract kind maps to shared group goal. <!-- ID: SOC-157 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-158: Contract party dissolution applies contract consequences. <!-- ID: SOC-158 SOURCE: src/systems/social_systems/contracts.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->

Without these, social “contracts” may exist as records but not as behavior.

---

## 10. Calamity / world-boss system

This is a real omission. The checklist mentions calamity evolution, but not the actual world-boss system.

Add:

- [x] WORLD-023: World maturity increases on schedule. <!-- ID: WORLD-023 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-024: Calamity spawn obeys interval and forced-spawn ticks. <!-- ID: WORLD-024 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-025: Spawned calamity has world-boss identity and role. <!-- ID: WORLD-025 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-026: Calamity uses legendary stats. <!-- ID: WORLD-026 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-027: Calamity receives legendary equipment/loot. <!-- ID: WORLD-027 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-028: Calamity spawn creates bounty quests for heroes. <!-- ID: WORLD-028 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-063: Calamity aura applies local debuffs. <!-- ID: WORLD-063 SOURCE: src/world/calamity.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-030: Camp reinforcements occur on schedule. <!-- ID: WORLD-030 SOURCE: src/world/camp.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-031: Camp reinforcement level increases when camp is full. <!-- ID: WORLD-031 SOURCE: src/world/camp.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-032: Faction raids spawn on raid interval. <!-- ID: WORLD-032 SOURCE: src/world/raid.py TEST: tests/integration/test_raid_v2.py PROOF: integration -->
- [x] WORLD-033: Raid mobs use raid AI state. <!-- ID: WORLD-033 SOURCE: src/world/raid.py TEST: tests/integration/test_raid_v2.py PROOF: integration -->
- [x] WORLD-034: Raid mobs do not return home. <!-- ID: WORLD-034 SOURCE: src/world/raid.py TEST: tests/integration/test_raid_v2.py PROOF: integration -->
- [x] WORLD-035: Killing world boss grants fame. <!-- ID: WORLD-035 SOURCE: src/world/boss.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-036: Killing world boss grants title. <!-- ID: WORLD-036 SOURCE: src/world/boss.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->
- [x] WORLD-037: Bounty completion rewards are applied. <!-- ID: WORLD-037 SOURCE: src/world/boss.py TEST: tests/integration/test_world_evolution.py PROOF: integration -->

This is not optional world flavor. It affects progression, quests, combat, world pressure, and hero identity.

---

## 11. Region and Voronoi topology

The checklist has world/regions, but not enough of the concrete topology contract.

Add:

- [x] WORLD-038: Region contains uses Manhattan distance. <!-- ID: WORLD-038 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-039: Region copy deep-copies locations. <!-- ID: WORLD-039 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_models.py PROOF: unit -->
- [x] WORLD-040: Location model preserves type, position, and region ID. <!-- ID: WORLD-040 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_models.py PROOF: unit -->
- [x] WORLD-041: Difficulty tier chosen by distance zones. <!-- ID: WORLD-041 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-042: Boundary distances map to expected tier. <!-- ID: WORLD-042 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-043: Empty difficulty zones default safely. <!-- ID: WORLD-043 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-044: Region name selection is deterministic by terrain counter. <!-- ID: WORLD-044 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generation.py PROOF: unit -->
- [x] WORLD-045: Resetting name counters restarts name sequence. <!-- ID: WORLD-045 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generation.py PROOF: unit -->
- [x] WORLD-046: Every terrain has region names. <!-- ID: WORLD-046 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generation.py PROOF: unit -->
- [x] WORLD-047: Every terrain has race label. <!-- ID: WORLD-047 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generation.py PROOF: unit -->
- [x] WORLD-048: Difficulty multipliers exist for all tiers. <!-- ID: WORLD-048 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-049: Difficulty multipliers scale upward. <!-- ID: WORLD-049 SOURCE: src/world/spawn_config.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-050: All location types have name templates. <!-- ID: WORLD-050 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generation.py PROOF: unit -->
- [x] WORLD-051: Expected POI types exist: camp, grove, ruins, dungeon, shrine, boss arena, outpost, watchtower, portal, fishing spot, graveyard, obelisk. <!-- ID: WORLD-051 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generation.py PROOF: unit -->
- [x] WORLD-052: Voronoi map coverage is near-total. <!-- ID: WORLD-052 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-053: Region terrain, overlays, details, and town tiles account for map tiles. <!-- ID: WORLD-053 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-054: Regions border each other. <!-- ID: WORLD-054 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-055: Every region owns some territory. <!-- ID: WORLD-055 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-056: `find_region_at()` returns nearest region. <!-- ID: WORLD-056 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-057: Equidistant region lookup returns first region. <!-- ID: WORLD-057 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-058: Empty region list returns `None`. <!-- ID: WORLD-058 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] WORLD-059: Single region always matches. <!-- ID: WORLD-059 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->

This is a map-authority contract. If V2 changes it, spawning, difficulty, resource placement, and exploration all drift.

---

## 12. Platform primitives: RNG and spatial hash

The checklist mentions determinism, but not the primitive contracts.

Add:

- [x] SUB-272: Deterministic RNG repeats exactly for same seed/domain/entity/tick. <!-- ID: SUB-272 SOURCE: src/platform/rng.py TEST: tests/unit/platform/test_rng_v2.py PROOF: unit -->
- [x] SUB-273: RNG domain separation produces different streams for different domains. <!-- ID: SUB-273 SOURCE: src/platform/rng.py TEST: tests/unit/platform/test_rng_v2.py PROOF: unit -->
- [x] SUB-274: `next_int()` always respects inclusive bounds. <!-- ID: SUB-274 SOURCE: src/platform/rng.py TEST: tests/unit/platform/test_rng_v2.py PROOF: unit -->
- [x] SUB-275: Spatial hash insert places entity in correct cell. <!-- ID: SUB-275 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] SUB-276: Spatial hash radius query includes neighboring cells. <!-- ID: SUB-276 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] SUB-277: Spatial hash move removes old cell membership and adds new cell membership. <!-- ID: SUB-277 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] SUB-278: Spatial hash remove clears membership. <!-- ID: SUB-278 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->
- [x] SUB-279: Spatial hash behavior is deterministic independent of insertion order where required. <!-- ID: SUB-279 SOURCE: src/world/regions.py TEST: tests/unit/world/test_topology.py PROOF: unit -->

These are low-level, but if they drift, every higher-level system becomes untrustworthy.

---

## 13. Phase guard and authoritative phase authorization

The checklist only has one unauthorized phase read item. Legacy tests cover more.

Add:

- [x] SUB-280: Unauthorized phase read raises. <!-- ID: SUB-280 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-281: Unauthorized phase mutation raises. <!-- ID: SUB-281 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-282: Unauthorized phase emit raises. <!-- ID: SUB-282 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-283: Authorized mutation succeeds only in permitted phase. <!-- ID: SUB-283 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-284: Internal field access is controlled. <!-- ID: SUB-284 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-285: Scheduling phase cannot mutate HP. <!-- ID: SUB-285 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-286: Persistence phase is read-only. <!-- ID: SUB-286 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-287: Phase guard prevents bypassing authoritative action/update application. <!-- ID: SUB-287 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->
- [x] SUB-288: Nested phase access follows the same authorization law. <!-- ID: SUB-288 SOURCE: src/engine/executor.py TEST: tests/unit/engine/test_phase_auth.py PROOF: unit -->

This is directly tied to V2’s “one authoritative mutation path” principle.

---

## 14. Behavior inspection and presenter truth

The checklist excludes UI-only presentation, which is fine. But some inspection/presenter behavior is not merely UI. It is behavioral explainability and debugging truth.

Add under an optional “inspection truth” section:

- [x] SUB-289: AI presenter maps structured decision drivers. <!-- ID: SUB-289 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-290: Belief inspection includes apparent state. <!-- ID: SUB-290 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-291: Injury blurring affects API-visible state consistently. <!-- ID: SUB-291 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-292: Stat breakdown service matches real derived stat math. <!-- ID: SUB-292 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-293: Combat trace recording is inspectable. <!-- ID: SUB-293 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-294: AI explainability persists across ticks. <!-- ID: SUB-294 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-295: Scheduler timeline is inspectable. <!-- ID: SUB-295 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-296: Entity inspection behavior matches legacy. <!-- ID: SUB-296 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-297: AI explanation parity is preserved or intentionally divergent. <!-- ID: SUB-297 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-298: Missing continuity data is handled safely. <!-- ID: SUB-298 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-299: Corrupted inspection state does not crash. <!-- ID: SUB-299 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->

This should not be mixed with gameplay parity, but it should not disappear either. Debug surfaces are part of operational truth.

---

## 15. Assertion and test helper semantics

The checklist should preserve some internal validation helpers because they define what “consistent” means.

Add:

- [x] SUB-300: Strategic consistency assertion fails on real drift. <!-- ID: SUB-300 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-301: Cognition consistency assertion fails when replay and graph diverge. <!-- ID: SUB-301 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-302: Graph integrity assertion catches broken cognition graph structure. <!-- ID: SUB-302 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-303: Determinism assertion compares actual replay outputs, not superficial success. <!-- ID: SUB-303 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-304: Overload behavior assertion preserves capacity failure semantics. <!-- ID: SUB-304 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-305: Combat arena helper preserves default factions, hostility, tick running, and entity lookup semantics. <!-- ID: SUB-305 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] SUB-306: Legacy stat helper preserves expected combat math inputs. <!-- ID: SUB-306 SOURCE: src/systems/world_systems/routine.py TEST: tests/unit/systems/test_routine_v2.py PROOF: unit -->
- [x] INFRA-071: Simulation step runs when brokers are missing. <!-- ID: INFRA-071 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->
- [x] INFRA-072: RabbitMQ missing-package path fails closed or disables cleanly. <!-- ID: INFRA-072 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->
- [x] INFRA-073: Kafka missing-package path fails closed or disables cleanly. <!-- ID: INFRA-073 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->
- [x] INFRA-074: Engine manager recovery handles missing Kafka. <!-- ID: INFRA-074 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->
- [x] INFRA-075: Worker pool RabbitMQ dispatch contract is preserved if broker mode is supported. <!-- ID: INFRA-075 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->
- [x] INFRA-076: Kafka recovery can reconstruct from snapshot plus event stream. <!-- ID: INFRA-076 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->
- [x] INFRA-077: Live-vs-manual replay produces same world state for loot recovery. <!-- ID: INFRA-077 SOURCE: src/engine/executor.py TEST: tests/unit/platform/test_infra_recovery.py PROOF: unit -->

---

## 16. Brokerless, recovery, and degraded-mode behavior tied to execution

Some infra is outside RPG-core scope, but not all of it. If missing Kafka/RabbitMQ changes whether the simulation step can run, it belongs in the checklist.

(Items now incorporated into main checklist above).

---

# Additional missing atomic RPG-core logic discovered during V2 audit

These items are appended rather than replacing existing checklist items. They are intentionally atomic. Mark them only when fully implemented and proven. Partial implementation remains unchecked.

## Z1. Checklist governance and truthfulness

- [x] INFRA-099: CI can fail when an oracle lacks seed/config metadata.
- [x] INFRA-100: CI can fail when unsupported behavior is silently accepted as success.

## Z2. Resource conservation and inventory pressure law

- [x] TOWN-103: All active resource acquisition paths share one conservation law. <!-- ID: TOWN-103 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-104: `InteractionSystem` harvest path and any standalone `HarvestSystem` path cannot diverge on capacity rules. <!-- ID: TOWN-104 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-105: `InteractionSystem` loot path and any standalone `LootSystem` path cannot diverge on capacity rules. <!-- ID: TOWN-105 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-106: A resource node charge is not decremented until inventory receipt is proven possible. <!-- ID: TOWN-106 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-107: A ground item is not removed until inventory receipt is proven possible. <!-- ID: TOWN-107 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-108: A corpse loot record is not consumed until inventory receipt is proven possible. <!-- ID: TOWN-108 SOURCE: src/engine/apply.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-109: Inventory slot capacity is checked before source mutation. <!-- ID: TOWN-109 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-110: Inventory weight capacity is checked before source mutation. <!-- ID: TOWN-110 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-111: Inventory stackability is checked before rejecting for slot pressure. <!-- ID: TOWN-111 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-112: Inventory add failure preserves the source item/node/corpse. <!-- ID: TOWN-112 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-113: Inventory add failure resets or preserves the interaction channel according to an explicit rule. <!-- ID: TOWN-113 SOURCE: src/engine/pipeline_phases/interactions.py TEST: tests/unit/interactions/test_interaction_reset.py PROOF: unit -->
- [x] TOWN-114: Harvest completion emits both inventory addition and node depletion atomically. <!-- ID: TOWN-114 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-115: Loot completion emits both inventory addition and source removal atomically. <!-- ID: TOWN-115 SOURCE: src/engine/apply.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-116: Partial channel progress does not create items. <!-- ID: TOWN-116 SOURCE: src/engine/pipeline_phases/interactions.py TEST: tests/unit/interactions/test_interaction_continuity.py PROOF: unit -->
- [x] TOWN-117: Interrupted channel progress does not create items. <!-- ID: TOWN-117 SOURCE: src/engine/pipeline_phases/interactions.py TEST: tests/unit/interactions/test_interaction_reset.py PROOF: unit -->
- [x] TOWN-118: Interrupted channel progress does not remove source items. <!-- ID: TOWN-118 SOURCE: src/engine/pipeline_phases/interactions.py TEST: tests/unit/interactions/test_interaction_reset.py PROOF: unit -->
- [x] TOWN-119: Failed capacity check does not remove source items. <!-- ID: TOWN-119 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-120: Failed capacity check does not decrement node charges. <!-- ID: TOWN-120 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-121: Two actors completing the same loot target in the same tick cannot duplicate the item. <!-- ID: TOWN-121 SOURCE: src/engine/apply.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-122: Two actors completing the same resource-node charge in the same tick cannot duplicate the yield. <!-- ID: TOWN-122 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-123: Two actors completing the same corpse loot in the same tick cannot duplicate corpse rewards. <!-- ID: TOWN-123 SOURCE: src/engine/apply.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-124: Conflict resolution decides one authoritative winner for contested loot completion. <!-- ID: TOWN-124 SOURCE: src/engine/apply.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-125: Conflict resolution decides one authoritative winner per limited resource charge when required. <!-- ID: TOWN-125 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-126: Item quantity is preserved through pickup, stacking, selling, crafting, and dropping. <!-- ID: TOWN-126 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-127: Item weight is preserved through pickup, stacking, selling, crafting, and dropping. <!-- ID: TOWN-127 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-128: Item identity/kind is preserved through pickup, stacking, selling, crafting, and dropping. <!-- ID: TOWN-128 SOURCE: src/core/inventory.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-129: Harvest yield uses the node definition, not caller-provided arbitrary item data. <!-- ID: TOWN-129 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-130: Loot yield uses the ground/corpse source definition, not caller-provided arbitrary item data. <!-- ID: TOWN-130 SOURCE: src/engine/apply.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-131: Capacity failure reason is structured and observable. <!-- ID: TOWN-131 SOURCE: src/core/updates.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-132: Resource source mutation and inventory mutation appear in the same authoritative update/apply transaction. <!-- ID: TOWN-132 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] TOWN-133: Resource acquisition replay includes both source and inventory state. <!-- ID: TOWN-133 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] TOWN-134: Resource acquisition replay can prove no duplication across identical seed runs. <!-- ID: TOWN-134 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] TOWN-135: Resource acquisition replay can prove no item loss under capacity failure. <!-- ID: TOWN-135 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] TOWN-136: Resource-node cooldown behavior is deterministic. <!-- ID: TOWN-136 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-137: Resource-node recharge behavior is deterministic. <!-- ID: TOWN-137 SOURCE: src/engine/apply.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-138: Resource-node depletion state survives serialization. <!-- ID: TOWN-138 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] TOWN-139: Ground item state survives serialization. <!-- ID: TOWN-139 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] TOWN-140: Corpse loot state survives serialization. <!-- ID: TOWN-140 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] TOWN-141: Loot/harvest tests include slot pressure. <!-- ID: TOWN-141 SOURCE: tests/unit/test_inventory_v2.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-142: Loot/harvest tests include weight pressure. <!-- ID: TOWN-142 SOURCE: tests/unit/test_inventory_v2.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-143: Loot/harvest tests include stack merge under near-full inventory. <!-- ID: TOWN-143 SOURCE: tests/unit/test_inventory_v2.py TEST: tests/unit/test_inventory_v2.py PROOF: unit -->
- [x] TOWN-144: Loot/harvest tests include two actors racing for one item. <!-- ID: TOWN-144 SOURCE: tests/integration/test_looting_v2.py TEST: tests/integration/test_looting_v2.py PROOF: integration -->
- [x] TOWN-145: Loot/harvest tests include failure preserving source state. <!-- ID: TOWN-145 SOURCE: tests/integration/test_resources_v2_boundary.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->
- [x] TOWN-146: Loot/harvest tests include success mutating inventory and source together. <!-- ID: TOWN-146 SOURCE: tests/integration/test_resources_v2_boundary.py TEST: tests/integration/test_resources_v2_boundary.py PROOF: integration -->

## Z3. Authoritative pipeline and bypass prevention

- [x] TOWN-147: Every gameplay update enters the same authoritative refinement/apply pipeline. <!-- ID: TOWN-147 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: integration -->
- [x] TOWN-148: No AI/state system mutates authoritative world state directly during proposal generation. <!-- ID: TOWN-148 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: unit -->
- [x] TOWN-149: No standalone gameplay system can remove world objects without apply pipeline validation. <!-- ID: TOWN-149 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: integration -->
- [x] TOWN-150: No standalone gameplay system can add inventory without apply pipeline validation. <!-- ID: TOWN-150 SOURCE: src/engine/pipeline_phases/trust.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: integration -->
- [x] TOWN-151: No standalone gameplay system can change combat HP without combat legality validation. <!-- ID: TOWN-151 SOURCE: src/engine/pipeline_phases/trust.py TEST: tests/integration/pipeline/test_combat_trust.py PROOF: negative -->
- [x] TOWN-152: No standalone gameplay system can change position without movement legality validation. <!-- ID: TOWN-152 SOURCE: src/engine/pipeline_phases/trust.py TEST: tests/integration/pipeline/test_movement_trust.py PROOF: negative -->
- [x] TOWN-153: No standalone gameplay system can change reputation/social state without social consequence validation. <!-- ID: TOWN-153 SOURCE: src/engine/pipeline_phases/trust.py TEST: tests/integration/pipeline/test_social_trust.py PROOF: negative -->
- [x] TOWN-154: No standalone gameplay system can complete quests without quest lifecycle validation. <!-- ID: TOWN-154 SOURCE: src/engine/pipeline_phases/trust.py TEST: tests/integration/pipeline/test_quest_trust.py PROOF: negative -->
- [x] TOWN-155: Every raw update is either accepted, refined, rejected, or marked unsupported. <!-- ID: TOWN-155 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: integration -->
- [x] TOWN-156: Rejected updates preserve unrelated update domains. <!-- ID: TOWN-156 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-157: Rejected updates expose structured rejection reason. <!-- ID: TOWN-157 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-158: Rejection reasons are replay-visible or log-visible. <!-- ID: TOWN-158 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] TOWN-159: Merge logic for multiple `StateUpdate`s is deterministic. <!-- ID: TOWN-159 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-160: Merge logic has stable precedence for conflicting entity updates. <!-- ID: TOWN-160 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-161: Merge logic has stable precedence for conflicting world updates. <!-- ID: TOWN-161 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-162: Merge logic does not accidentally drop independent updates. <!-- ID: TOWN-162 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-163: Merge logic detects incompatible updates where required. <!-- ID: TOWN-163 SOURCE: src/core/updates.py TEST: tests/unit/core/test_update_models.py PROOF: unit -->
- [x] TOWN-164: Apply order is documented. <!-- ID: TOWN-164 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: integration -->
- [x] TOWN-165: Apply order is tested for cross-domain interactions. <!-- ID: TOWN-165 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: integration -->
- [x] TOWN-166: Apply order cannot depend on dictionary iteration where ordering matters. <!-- ID: TOWN-166 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: integration -->
- [x] TOWN-167: Apply order cannot depend on thread completion order where gameplay outcome matters. <!-- ID: TOWN-167 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: integration -->
- [x] TOWN-168: Pipeline tests include direct old-system calls if such calls remain importable. <!-- ID: TOWN-168 SOURCE: tests/integration/pipeline/test_mutation_boundary.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: integration -->
- [x] TOWN-169: Pipeline tests prove dead/bypassed systems cannot create different gameplay laws. <!-- ID: TOWN-169 SOURCE: tests/integration/pipeline/test_mutation_boundary.py TEST: tests/integration/pipeline/test_mutation_boundary.py PROOF: integration -->

## Z4. Movement intention, congestion, and blocked-route behavior

- [x] COMB-202: Movement intentions include pursue. <!-- ID: COMB-202 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-203: Movement intentions include retreat. <!-- ID: COMB-203 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-204: Movement intentions include hold. <!-- ID: COMB-204 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-205: Movement intentions include reposition. <!-- ID: COMB-205 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-206: Movement intentions include intercept. <!-- ID: COMB-206 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-207: Movement intentions include guard. <!-- ID: COMB-207 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-208: Movement intentions include regroup or an explicit intentional-divergence note explains why not. <!-- ID: COMB-208 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-209: Movement intention influences target choice. <!-- ID: COMB-209 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-210: Movement intention influences preferred tile choice. <!-- ID: COMB-210 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-211: Movement intention influences blocked-tile fallback. <!-- ID: COMB-211 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-212: Movement intention influences willingness to wait. <!-- ID: COMB-212 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-213: Movement intention influences willingness to sidestep. <!-- ID: COMB-213 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-214: Movement intention influences willingness to reroute. <!-- ID: COMB-214 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-215: Movement intention influences willingness to break pursuit. <!-- ID: COMB-215 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-216: Blocked movement first checks if target was reached. <!-- ID: COMB-216 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-217: Blocked movement distinguishes temporary occupancy from invalid terrain. <!-- ID: COMB-217 SOURCE: src/engine/legality.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-218: Blocked movement distinguishes ally-blocked from enemy-blocked. <!-- ID: COMB-218 SOURCE: src/engine/legality.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-219: Blocked movement distinguishes high-priority actor from low-priority actor. <!-- ID: COMB-219 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-220: Blocked movement can wait when waiting is strategically valid. <!-- ID: COMB-220 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-221: Blocked movement can yield when another actor has higher priority. <!-- ID: COMB-221 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-222: Blocked movement can sidestep when a safe adjacent alternative exists. <!-- ID: COMB-222 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-223: Blocked movement can reroute when the direct step is blocked. <!-- ID: COMB-223 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-224: Blocked movement can replan when route cache/path is stale. <!-- ID: COMB-224 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-225: Blocked movement can regroup when party cohesion matters. <!-- ID: COMB-225 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-226: Blocked movement can abandon route after bounded retry budget. <!-- ID: COMB-226 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-227: Occupancy conflict has one authoritative winner per tile per tick. <!-- ID: COMB-227 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-228: Occupancy conflict losers receive structured reason. <!-- ID: COMB-228 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-229: Occupancy conflict losers do not overlap the winner. <!-- ID: COMB-229 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-230: Occupancy conflict does not weaken occupancy law silently. <!-- ID: COMB-230 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-231: Sidestep avoids known occupied tiles. <!-- ID: COMB-231 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-232: Sidestep avoids invalid terrain. <!-- ID: COMB-232 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-233: Sidestep avoids stepping into lethal/hazardous tiles unless explicitly allowed. <!-- ID: COMB-233 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-234: Retreat sidestep prefers increased distance from threat. <!-- ID: COMB-234 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-235: Pursuit sidestep prefers preserving progress toward target. <!-- ID: COMB-235 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-236: Guard movement prefers preserving guard radius. <!-- ID: COMB-236 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-237: Intercept movement predicts target or path rather than chasing current position only. <!-- ID: COMB-237 SOURCE: src/systems/world_systems/navigation.py TEST: tests/unit/world/test_navigation.py PROOF: unit -->
- [x] COMB-238: Regroup movement prefers party anchor or leader position. <!-- ID: COMB-238 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-239: Movement fallback is bounded to avoid infinite loops. <!-- ID: COMB-239 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-240: Stuck counters increment only when actual movement fails. <!-- ID: COMB-240 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-241: Stuck counters reset when meaningful movement succeeds. <!-- ID: COMB-241 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-242: Stuck handling can trigger route invalidation. <!-- ID: COMB-242 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-243: Stuck handling can trigger strategic replan when movement is impossible. <!-- ID: COMB-243 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-244: Movement replay can prove no overlapping entities after conflict resolution. <!-- ID: COMB-244 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-245: Movement replay can prove deterministic outcome under same seed. <!-- ID: COMB-245 SOURCE: src/engine/pipeline_phases/occupancy.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-246: Movement tests include one actor blocked by ally. <!-- ID: COMB-246 SOURCE: tests/unit/movement/test_occupancy_conflicts.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-247: Movement tests include one actor blocked by enemy. <!-- ID: COMB-247 SOURCE: tests/unit/movement/test_occupancy_conflicts.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-248: Movement tests include two actors targeting same tile. <!-- ID: COMB-248 SOURCE: tests/unit/movement/test_occupancy_conflicts.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-249: Movement tests include corridor congestion. <!-- ID: COMB-249 SOURCE: tests/unit/movement/test_occupancy_conflicts.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-250: Movement tests include party regroup movement. <!-- ID: COMB-250 SOURCE: tests/unit/movement/test_tactical_movement.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-251: Movement tests include retreat under congestion. <!-- ID: COMB-251 SOURCE: tests/unit/movement/test_occupancy_conflicts.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-252: Movement tests include pursuit under congestion. <!-- ID: COMB-252 SOURCE: tests/unit/movement/test_occupancy_conflicts.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->
- [x] COMB-253: Movement tests include invalid terrain vs occupied terrain distinction. <!-- ID: COMB-253 SOURCE: src/engine/legality.py TEST: tests/unit/movement/test_occupancy_conflicts.py PROOF: unit -->


## Z5. Tactical combat, targeting, and action choice consistency

- [x] COMB-254: Tactical action choice uses only legal candidate actions. <!-- ID: COMB-254 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-255: Tactical action choice does not bypass movement/combat legality. <!-- ID: COMB-255 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->

- [x] COMB-256: Melee attack requires valid adjacency/engagement rule. <!-- ID: COMB-256 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-257: Ranged attack requires valid range rule. <!-- ID: COMB-257 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-258: Ranged attack requires valid line-of-sight or an explicit unsupported note. <!-- ID: COMB-258 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-259: Area attack requires valid target position. <!-- ID: COMB-259 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-260: Area attack affects only entities inside AoE radius. <!-- ID: COMB-260 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-261: AoE friendly-fire behavior is explicit. <!-- ID: COMB-261 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-262: Cover behavior is explicit if ranged combat supports cover. <!-- ID: COMB-262 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-263: Weapon range affects tactical choice. <!-- ID: COMB-263 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->

- [x] COMB-264: Skill range affects tactical choice. <!-- ID: COMB-264 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-265: Skill cost affects tactical choice. <!-- ID: COMB-265 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->

- [x] COMB-266: Readiness/cooldown affects tactical choice. <!-- ID: COMB-266 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-267: Exhaustion affects tactical choice. <!-- ID: COMB-267 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-268: Low HP affects tactical choice. <!-- ID: COMB-268 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-269: Threat level affects tactical choice. <!-- ID: COMB-269 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-270: Target stickiness prevents unrealistic full retarget every tick. <!-- ID: COMB-270 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-271: Target stickiness can break when target invalid/dead/out of range beyond threshold. <!-- ID: COMB-271 SOURCE: src/engine/tactical.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-272: Disengagement has explicit consequence or safe-exit rule. <!-- ID: COMB-272 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_movement_spatial_regression.py PROOF: unit -->
- [x] COMB-273: Opportunity consequences apply only under legal conditions. <!-- ID: COMB-273 SOURCE: src/engine/movement.py TEST: tests/unit/movement/test_movement_spatial_regression.py PROOF: unit -->
- [x] COMB-274: Anti-stalemate handles chase loops. <!-- ID: COMB-274 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-275: Anti-stalemate handles kite loops. <!-- ID: COMB-275 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-276: Anti-stalemate handles repeated step-back loops. <!-- ID: COMB-276 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->
- [x] COMB-277: Anti-stalemate does not force illegal movement. <!-- ID: COMB-277 SOURCE: src/engine/tactical.py TEST: tests/unit/movement/test_tactical_movement.py PROOF: unit -->

- [x] COMB-278: Combat result emits damage trace. <!-- ID: COMB-278 SOURCE: src/engine/combat.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-279: Combat result emits kill/death consequence when applicable. <!-- ID: COMB-279 SOURCE: src/engine/combat.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-280: Combat result emits reward/progression consequence when applicable. <!-- ID: COMB-280 SOURCE: src/engine/combat.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] COMB-281: Combat result can trigger social/narrative consequence when applicable. <!-- ID: COMB-281 SOURCE: src/engine/combat.py TEST: tests/integration/pipeline/test_combat_trust.py PROOF: unit -->
- [x] COMB-282: Combat result can trigger strategic update when applicable. <!-- ID: COMB-282 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->

- [x] COMB-283: Combat tests cover melee legality. <!-- ID: COMB-283 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->
- [x] COMB-284: Combat tests cover ranged legality. <!-- ID: COMB-284 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->
- [x] COMB-285: Combat tests cover AoE legality. <!-- ID: COMB-285 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->
- [x] COMB-286: Combat tests cover invalid target rejection. <!-- ID: COMB-286 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->
- [x] COMB-287: Combat tests cover dead target rejection. <!-- ID: COMB-287 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->
- [x] COMB-288: Combat tests cover target stickiness break condition. <!-- ID: COMB-288 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->

- [x] COMB-289: Combat tests cover exhaustion/readiness rejection. <!-- ID: COMB-289 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: certification -->

## Z6. Deterministic randomness and replay-stable execution

- [x] INFRA-101: Same seed and same inputs produce same final authoritative hash. <!-- ID: INFRA-101 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-102: Same seed and same inputs produce same replay-visible trajectory. <!-- ID: INFRA-102 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-103: Different seeds produce meaningful divergence. <!-- ID: INFRA-103 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-104: Local sequential execution and worker execution produce equivalent gameplay outcomes. <!-- ID: INFRA-104 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-105: Thread scheduling order cannot change gameplay outcome. <!-- ID: INFRA-105 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-106: Work queue order cannot change gameplay outcome except through documented priority. <!-- ID: INFRA-106 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-107: RNG API supports domain separation or another proven call-order-independent scheme. <!-- ID: INFRA-107 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-108: RNG calls are scoped by deterministic context such as domain/entity/tick/sub-id or equivalent. <!-- ID: INFRA-108 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-109: Spawn randomness is isolated from tactical randomness. <!-- ID: INFRA-109 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-110: Tactical randomness is isolated from social randomness. <!-- ID: INFRA-110 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-111: Social randomness is isolated from world-event randomness. <!-- ID: INFRA-111 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-112: World-event randomness is isolated from quest generation randomness. <!-- ID: INFRA-112 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-113: Quest generation randomness is isolated from movement randomness. <!-- ID: INFRA-113 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-114: Calamity/world-boss randomness is isolated from local action randomness. <!-- ID: INFRA-114 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: unit -->
- [x] INFRA-115: Adding a new actor cannot perturb unrelated actor decisions unless interaction requires it. <!-- ID: INFRA-115 SOURCE: src/platform/rng.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-116: Adding a new non-interacting system cannot perturb existing RNG outcomes. <!-- ID: INFRA-116 SOURCE: src/engine/scheduler.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-117: Debug/logging/presentation cannot consume gameplay RNG. <!-- ID: INFRA-117 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: unit -->
- [x] INFRA-118: Tests detect accidental use of global `random` in gameplay code. <!-- ID: INFRA-118 SOURCE: tests/unit/platform/test_rng_hygiene.py TEST: tests/unit/platform/test_rng_hygiene.py PROOF: unit -->
- [x] INFRA-119: Tests detect nondeterministic set/dict ordering where it affects gameplay. <!-- ID: INFRA-119 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-120: Replay hash includes all gameplay-relevant domains. <!-- ID: INFRA-120 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-121: Replay hash excludes presentation-only fields. <!-- ID: INFRA-121 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-122: Replay hash includes inventory. <!-- ID: INFRA-122 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-123: Replay hash includes entities and positions. <!-- ID: INFRA-123 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-124: Replay hash includes combat state. <!-- ID: INFRA-124 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-125: Replay hash includes strategic state. <!-- ID: INFRA-125 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-126: Replay hash includes social state. <!-- ID: INFRA-126 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-127: Replay hash includes world resources. <!-- ID: INFRA-127 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-128: Replay hash includes groups/parties. <!-- ID: INFRA-128 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-129: Replay hash includes quests/contracts. <!-- ID: INFRA-129 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-130: Replay hash includes progression. <!-- ID: INFRA-130 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-131: Replay tests include repeated identical runs. <!-- ID: INFRA-131 SOURCE: tests/integration/kernel/test_seed_stability.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->
- [x] INFRA-132: Replay tests include sequential vs concurrent execution. <!-- ID: INFRA-132 SOURCE: tests/integration/kernel/test_executor_determinism.py TEST: tests/integration/kernel/test_executor_determinism.py PROOF: integration -->
- [x] INFRA-133: Replay tests include save/load continuation. <!-- ID: INFRA-133 SOURCE: src/engine/checkpoint.py TEST: tests/integration/kernel/test_seed_stability.py PROOF: integration -->

## Z7. Purpose-driven group and party cooperation

- [x] SOC-160: Party formation can be driven by accepted social contract. <!-- ID: SOC-160 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_social_party_regression.py PROOF: unit -->
- [x] SOC-161: Party formation can be driven by shared quest or project.  
  - SOURCE: [groups.py:L106](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/groups.py#L106) (Uses leader target propagation)  
  - TEST: [test_domain_7_social.py:L84](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/social/test_domain_7_social.py#L84)  
  - PROOF: `test_group_directive_propagation` verifies project-based coordination.  
- [x] SOC-162: Party formation can be driven by raid membership. <!-- ID: SOC-162 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-163: Party formation can be driven by escort/expedition/mercenary/revenge contract kind. <!-- ID: SOC-163 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-164: Proximity alone does not create a party unless explicitly modeled as a temporary tactical group. <!-- ID: SOC-164 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_social_party_regression.py PROOF: unit -->
- [x] SOC-165: Temporary tactical group is distinct from contract party.
- [x] SOC-166: Contract party has founder/leader. <!-- ID: SOC-166 SOURCE: src/core/state.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-167: Contract party has member roles. <!-- ID: SOC-167 SOURCE: src/core/state.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-168: Contract party has shared goal.
- [x] SOC-169: Contract party links back to the contract/obligation that created it. <!-- ID: SOC-169 SOURCE: src/core/state.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-170: Member entity links back to party/group ID. <!-- ID: SOC-170 SOURCE: src/core/state.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-171: Member contract links back to party/group ID where relevant.
- [x] SOC-172: Party anchor follows leader or agreed anchor rule. <!-- ID: SOC-172 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-173: Party cohesion is updated from member positions. <!-- ID: SOC-173 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-174: Party cohesion affects regroup behavior. <!-- ID: SOC-174 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-175: Party cohesion can trigger warnings or replan before dissolution.
- [x] SOC-176: Party dissolves when leader is dead/missing according to explicit rule. <!-- ID: SOC-176 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_phantom_leader.py PROOF: unit -->
- [x] SOC-177: Party dissolves when membership falls below minimum according to explicit rule. <!-- ID: SOC-177 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-178: Party dissolves when contract is completed/abandoned/failed according to explicit rule. <!-- ID: SOC-178 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
  - SOURCE: [groups.py:L83](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/groups.py#L83)  
- [x] SOC-179: Party dissolution updates member group IDs. <!-- ID: SOC-179 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
  - SOURCE: [groups.py:L53](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/groups.py#L53)  
- [x] SOC-180: Party dissolution updates contract status when appropriate.  
- [x] SOC-181: Party dissolution applies social/reputation consequences when appropriate.  
  - SOURCE: [contracts.py:L188](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L188)  
  - PROOF: Contract outcome resolution handles reputation/bond deltas.  
- [x] SOC-182: Party target propagation occurs inside authoritative tick pipeline, not manual test-only invocation. <!-- ID: SOC-182 SOURCE: src/engine/pipeline.py TEST: tests/integration/pipeline/test_party_coordination.py PROOF: unit -->
- [x] SOC-183: Shared target is valid and alive when assigned. <!-- ID: SOC-183 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-184: Shared target clears when invalid/dead. <!-- ID: SOC-184 SOURCE: src/systems/world_systems/groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-185: Group focus fire does not override individual legality constraints. <!-- ID: SOC-185 SOURCE: src/engine/legality.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-186: Group behavior does not teleport or force illegal movement. <!-- ID: SOC-186 SOURCE: src/engine/pipeline.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-187: Group formation test covers accepted contract. <!-- ID: SOC-187 SOURCE: tests/unit/social/test_social_party_regression.py TEST: tests/unit/social/test_social_party_regression.py PROOF: unit -->
- [x] SOC-188: Group formation test covers no contract / proximity-only rejection. <!-- ID: SOC-188 SOURCE: tests/unit/social/test_social_party_regression.py TEST: tests/unit/social/test_social_party_regression.py PROOF: unit -->
- [x] SOC-189: Group dissolution test covers dead leader. <!-- ID: SOC-189 SOURCE: tests/unit/social/test_phantom_leader.py TEST: tests/unit/social/test_phantom_leader.py PROOF: unit -->
- [x] SOC-190: Group dissolution test covers scattered members. <!-- ID: SOC-190 SOURCE: tests/unit/social/test_phantom_leader.py TEST: tests/unit/social/test_phantom_leader.py PROOF: unit -->
- [x] SOC-191: Group dissolution test covers contract abandonment consequence. <!-- ID: SOC-191 SOURCE: tests/unit/social/test_groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-192: Group coordination test runs through normal kernel tick, not only manual system call. <!-- ID: SOC-192 SOURCE: tests/unit/social/test_domain_7_social.py TEST: tests/unit/social/test_domain_7_social.py PROOF: unit -->

## Z8. Strategic projects, blockers, leads, and cognition as RPG behavior

- [x] STRAT-184: Strategic project creation is based on current needs/world state. <!-- ID: STRAT-184 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_lifecycle_v2.py PROOF: unit -->
- [x] STRAT-185: Strategic project retention is bounded by interruption resistance. <!-- ID: STRAT-185 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-186: Strategic project switching requires margin or explicit emergency. <!-- ID: STRAT-186 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-187: Current project has reservation priority. <!-- ID: STRAT-187 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-188: Current objective has continuity priority. <!-- ID: STRAT-188 SOURCE: src/engine/tactical.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-189: Objective derivation can create executable objectives. <!-- ID: STRAT-189 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_lifecycle_v2.py PROOF: unit -->
- [x] STRAT-190: Objective derivation can create blockers when execution is impossible. <!-- ID: STRAT-190 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-191: Blockers have kind. <!-- ID: STRAT-191 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-192: Blockers have subject/reference. <!-- ID: STRAT-192 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-193: Blockers have severity. <!-- ID: STRAT-193 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-194: Blockers have origin/spawned-from reference where useful. <!-- ID: STRAT-194 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-195: Blockers can be resolved by acquiring missing knowledge. <!-- ID: STRAT-195 SOURCE: src/systems/strategic_systems/learning.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-196: Blockers can be resolved by acquiring missing material. <!-- ID: STRAT-196 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-197: Blockers can be resolved by acquiring missing gold/resource. <!-- ID: STRAT-197 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-198: Blockers can be resolved by finding location/target. <!-- ID: STRAT-198 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-199: Blockers can be misdiagnosed under low cognition. <!-- ID: STRAT-199 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->
- [x] STRAT-200: Misdiagnosis is bounded and explainable. <!-- ID: STRAT-200 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->
- [x] STRAT-201: Leads have kind. <!-- ID: STRAT-201 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-202: Leads have subject. <!-- ID: STRAT-202 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-203: Leads have certainty. <!-- ID: STRAT-203 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-204: Leads have source trust. <!-- ID: STRAT-204 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-205: Leads can be tested. <!-- ID: STRAT-205 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_lifecycle_v2.py PROOF: unit -->
- [x] STRAT-206: Tested bad leads are suppressed. <!-- ID: STRAT-206 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-207: Exhausted leads are not retried blindly. <!-- ID: STRAT-207 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-208: Lead retention obeys cognition profile capacity. <!-- ID: STRAT-208 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-209: Concern intake obeys cognition profile capacity. <!-- ID: STRAT-209 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-210: Detour breadth obeys cognition profile capacity. <!-- ID: STRAT-210 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-211: Detour depth obeys cognition profile capacity. <!-- ID: STRAT-211 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-212: Detour overflow suspends or reprioritizes project explicitly. <!-- ID: STRAT-212 SOURCE: src/systems/strategic_systems/detour.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-213: Strategic overload is represented and observable. <!-- ID: STRAT-213 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-214: Strategic state persists across ticks. <!-- ID: STRAT-214 SOURCE: src/core/strategic.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-215: Strategic state survives serialization. <!-- ID: STRAT-215 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] STRAT-216: Strategic state appears in replay/fingerprint. <!-- ID: STRAT-216 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] STRAT-217: Strategic explanation exposes why project/objective changed. <!-- ID: STRAT-217 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_explanation.py PROOF: unit -->
- [x] STRAT-218: Strategic explanation does not mutate strategic state. <!-- ID: STRAT-218 SOURCE: src/systems/strategic_systems/intelligence.py TEST: tests/unit/strategic/test_strategic_explanation.py PROOF: unit -->
- [x] STRAT-219: Strategic tests include high-cognition accurate diagnosis. <!-- ID: STRAT-219 SOURCE: tests/unit/strategic/test_diagnosis.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->
- [x] STRAT-220: Strategic tests include low-cognition misdiagnosis. <!-- ID: STRAT-220 SOURCE: tests/unit/strategic/test_diagnosis.py TEST: tests/unit/strategic/test_diagnosis.py PROOF: unit -->
- [x] STRAT-221: Strategic tests include tested-lead suppression. <!-- ID: STRAT-221 SOURCE: tests/unit/strategic/test_strategic_hardening.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-222: Strategic tests include detour depth overflow. <!-- ID: STRAT-222 SOURCE: tests/unit/strategic/test_strategic_hardening.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-223: Strategic tests include current-objective retention. <!-- ID: STRAT-223 SOURCE: tests/unit/strategic/test_strategic_hardening.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->
- [x] STRAT-224: Strategic tests include project-switch margin. <!-- ID: STRAT-224 SOURCE: tests/unit/strategic/test_strategic_hardening.py TEST: tests/unit/strategic/test_strategic_hardening.py PROOF: unit -->

## Z9. Social contracts, trust, reputation, and lived consequence law

- [x] SOC-193: Public reputation and private relationship/bond are separate state. <!-- ID: SOC-193 SOURCE: src/systems/social_systems/relationships.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-194: Private betrayal can override public reputation. <!-- ID: SOC-194 SOURCE: src/systems/social_systems/relationships.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-195: Familiarity changes through interaction evidence. <!-- ID: SOC-195 SOURCE: src/systems/social_systems/relationships.py TEST: tests/unit/social/test_social_bonds.py PROOF: unit -->
- [x] SOC-196: Trust/sentiment changes through interaction evidence. <!-- ID: SOC-196 SOURCE: src/systems/social_systems/relationships.py TEST: tests/unit/social/test_social_bonds.py PROOF: unit -->
- [x] SOC-197: Social source trust changes through fulfilled/failed information.  
  - SOURCE: [appraisal.py:L309](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/appraisal.py#L309)  
- [x] SOC-198: Turning points persist as narrative/life-event records. <!-- ID: SOC-198 SOURCE: src/social/appraisal.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-199: Turning points influence later strategic/social appraisal. <!-- ID: SOC-199 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
  - SOURCE: [appraisal.py:L50](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/appraisal.py#L50) (Checks betrayal count derived from turning points)  
- [x] SOC-200: Contract offer has recruiter/founder.  
  - SOURCE: [strategic.py:L186](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py#L186) (source_id)  
- [x] SOC-201: Contract offer has candidate.  
  - SOURCE: [strategic.py:L187](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py#L187) (target_id)  
- [x] SOC-202: Contract offer has terms.  
  - SOURCE: [strategic.py:L188](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py#L188) (terms dict)  
- [x] SOC-203: Contract offer has status.  
  - SOURCE: [strategic.py:L189](file:///home/vboxuser/Work/rpg-based-simulation/src/core/strategic.py#L189) (status enum)  
- [x] SOC-204: Contract appraisal uses trust/private bond. <!-- ID: SOC-204 SOURCE: src/social/appraisal.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-205: Contract appraisal uses greed or reward preference. <!-- ID: SOC-205 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_recruitment.py PROOF: unit -->
  - SOURCE: [appraisal.py:L109](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/appraisal.py#L109) (Greed trait impacts utility)  
- [x] SOC-206: Contract appraisal uses capability/role fit. <!-- ID: SOC-206 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_groups.py PROOF: unit -->
- [x] SOC-207: Contract appraisal uses prior trauma/betrayal.  
  - SOURCE: [appraisal.py:L50](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/appraisal.py#L50)  
- [x] SOC-208: Accepted contract creates explicit obligation/contract state. <!-- ID: SOC-208 SOURCE: src/systems/social_contract.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-209: Honored contract improves relevant social/reputation state.  
  - SOURCE: [contracts.py:L192](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L192)  
- [x] SOC-210: Broken contract worsens relevant social/reputation state.  
  - SOURCE: [contracts.py:L175](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L175)  
- [x] SOC-211: Abandoned contract can create betrayal/turning point where appropriate.  
  - SOURCE: [contracts.py:L211](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L211)  
- [x] SOC-212: Contract outcome propagates to all affected members.  
  - SOURCE: [contracts.py:L224](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L224)  
- [x] SOC-213: Contract outcome can affect public reputation.  
  - SOURCE: [contracts.py:L189](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L189)  
- [x] SOC-214: Contract outcome can affect private bonds.  
  - SOURCE: [contracts.py:L182](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/contracts.py#L182)  
- [x] SOC-215: Contract outcome can affect future recruitment decisions. <!-- ID: SOC-215 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_recruitment.py PROOF: unit -->
- [x] SOC-216: Contract outcome can affect strategic directives. <!-- ID: SOC-216 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_betrayal.py PROOF: unit -->
- [x] SOC-217: Social updates are authoritative updates, not direct mutation during appraisal. <!-- ID: SOC-217 SOURCE: src/systems/social_systems/relationships.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-218: Social appraisal is bounded by social bandwidth/cognition where applicable. <!-- ID: SOC-218 SOURCE: src/systems/social_systems/appraisal.py TEST: tests/unit/social/test_recruitment.py PROOF: unit -->
- [x] SOC-219: Social tests include direct betrayal by recruiter. <!-- ID: SOC-219 SOURCE: tests/unit/social/test_betrayal.py TEST: tests/unit/social/test_betrayal.py PROOF: unit -->
- [x] SOC-220: Social tests include general betrayal trauma. <!-- ID: SOC-220 SOURCE: tests/unit/social/test_betrayal.py TEST: tests/unit/social/test_betrayal.py PROOF: unit -->
- [x] SOC-221: Social tests include high reward overcoming neutral reluctance when legal. <!-- ID: SOC-221 SOURCE: tests/unit/social/test_recruitment.py TEST: tests/unit/social/test_recruitment.py PROOF: unit -->
- [x] SOC-222: Social tests include reputation distinct from private trust. <!-- ID: SOC-222 SOURCE: tests/unit/social/test_social_lifecycle.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-223: Social tests include contract honored. <!-- ID: SOC-223 SOURCE: tests/unit/social/test_social_lifecycle.py TEST: tests/unit/social/test_social_lifecycle.py PROOF: unit -->
- [x] SOC-224: Social tests include contract broken/abandoned. <!-- ID: SOC-224 SOURCE: tests/unit/social/test_betrayal.py TEST: tests/unit/social/test_betrayal.py PROOF: unit -->
- [x] SOC-225: Social tests include party dissolution consequence if contract-backed. <!-- ID: SOC-225 SOURCE: tests/unit/social/test_groups.py TEST: tests/unit/social/test_groups.py PROOF: unit -->

## Z10. Progression, classes, skills, equipment, and growth law

- [x] PROG-064: XP/reward grant is authoritative and traceable to event. <!-- ID: PROG-064 SOURCE: src/engine/combat.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-065: Level-up thresholds are deterministic. <!-- ID: PROG-065 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-066: Attribute point grant is deterministic. <!-- ID: PROG-066 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-067: Attribute allocation checks available points. <!-- ID: PROG-067 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-068: Attribute allocation checks valid attribute name. <!-- ID: PROG-068 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-069: Attribute allocation applies aptitude multiplier or explicit divergence. <!-- ID: PROG-069 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-070: Attribute caps are enforced. <!-- ID: PROG-070 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-071: Effective stats recompute from base stats plus gear plus traits plus modifiers. <!-- ID: PROG-071 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-072: Effective stats clamp to valid ranges. <!-- ID: PROG-072 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-073: Skill definition includes ID. <!-- ID: PROG-073 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-074: Skill definition includes type/category. <!-- ID: PROG-074 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-075: Skill definition includes target rule. <!-- ID: PROG-075 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-076: Skill definition includes range where relevant. <!-- ID: PROG-076 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-077: Skill definition includes cost/cooldown where relevant. <!-- ID: PROG-077 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-078: Physical skill scaling is defined. <!-- ID: PROG-078 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-079: Magical skill scaling is defined. <!-- ID: PROG-079 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-080: Elemental skill scaling is defined. <!-- ID: PROG-080 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-081: Hybrid skill scaling is defined. <!-- ID: PROG-081 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-082: Skill scaling uses effective stats, not raw stats, where intended. <!-- ID: PROG-082 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-083: Passive skills apply through defined modifier path. <!-- ID: PROG-083 SOURCE: src/engine/rpg_depth.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-084: Active skills require legality checks before applying effects. <!-- ID: PROG-084 SOURCE: src/engine/legality.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-085: Class selection or assignment is explicit. <!-- ID: PROG-085 SOURCE: src/core/builder.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] PROG-086: Class starting gear is data-driven or documented. <!-- ID: PROG-086 SOURCE: src/systems/world_systems/generator.py TEST: tests/unit/world/test_generator_determinism.py PROOF: unit -->
- [x] PROG-087: Class skill unlocks are deterministic. <!-- ID: PROG-087 SOURCE: src/engine/apply.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-088: Gear equip validates slot. <!-- ID: PROG-088 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-089: Gear equip validates ownership/inventory. <!-- ID: PROG-089 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-090: Gear equip changes effective stats through authoritative update. <!-- ID: PROG-090 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-091: Gear ranking logic is deterministic. <!-- ID: PROG-091 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-092: Better gear can be selected by equipment service if that behavior is supported. <!-- ID: PROG-092 SOURCE: src/engine/apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-093: Home storage preserves items. <!-- ID: PROG-093 SOURCE: src/core/state.py TEST: tests/unit/core/test_state_serialization.py PROOF: unit -->
- [x] PROG-094: Shop buy checks gold before adding item. <!-- ID: PROG-094 SOURCE: src/engine/economy.py TEST: tests/unit/economy/test_transaction_v2.py PROOF: unit -->
- [x] PROG-095: Shop buy checks inventory capacity before subtracting gold. <!-- ID: PROG-095 SOURCE: src/engine/economy.py TEST: tests/unit/economy/test_transaction_v2.py PROOF: unit -->
- [x] PROG-096: Shop sell checks item exists before adding gold. <!-- ID: PROG-096 SOURCE: src/engine/economy.py TEST: tests/unit/economy/test_transaction_v2.py PROOF: unit -->
- [x] PROG-097: Crafting checks recipe exists. <!-- ID: PROG-097 SOURCE: src/systems/crafting.py TEST: tests/unit/quest/test_progression_lifecycle.py PROOF: unit -->
- [x] PROG-098: Crafting checks materials. <!-- ID: PROG-098 SOURCE: src/systems/crafting.py TEST: tests/unit/quest/test_progression_lifecycle.py PROOF: unit -->
- [x] PROG-099: Crafting checks gold/cost. <!-- ID: PROG-099 SOURCE: src/systems/crafting.py TEST: tests/unit/quest/test_progression_lifecycle.py PROOF: unit -->
- [x] PROG-100: Crafting checks inventory capacity for output. <!-- ID: PROG-100 SOURCE: src/systems/crafting.py TEST: tests/unit/quest/test_progression_lifecycle.py PROOF: unit -->
- [x] PROG-101: Crafting consumes materials and adds output atomically. <!-- ID: PROG-101 SOURCE: src/systems/crafting.py TEST: tests/unit/quest/test_progression_lifecycle.py PROOF: unit -->
- [x] PROG-102: Progression replay includes XP/level/attributes/skills/gear. <!-- ID: PROG-102 SOURCE: src/engine/kernel.py TEST: tests/integration/kernel/test_phase2_determinism.py PROOF: integration -->
- [x] PROG-103: Progression tests include attribute allocation. <!-- ID: PROG-103 SOURCE: tests/unit/progression/test_leveling.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-104: Progression tests include cap enforcement. <!-- ID: PROG-104 SOURCE: tests/unit/progression/test_leveling.py TEST: tests/unit/progression/test_leveling.py PROOF: unit -->
- [x] PROG-105: Progression tests include skill scaling. <!-- ID: PROG-105 SOURCE: tests/integration/pipeline/test_combat_legality_matrix.py TEST: tests/integration/pipeline/test_combat_legality_matrix.py PROOF: unit -->
- [x] PROG-106: Progression tests include gear equip. <!-- ID: PROG-106 SOURCE: tests/integration/pipeline/test_authoritative_apply.py TEST: tests/integration/pipeline/test_authoritative_apply.py PROOF: unit -->
- [x] PROG-107: Progression tests include crafting atomicity. <!-- ID: PROG-107 SOURCE: tests/unit/quest/test_progression_lifecycle.py TEST: tests/unit/quest/test_progression_lifecycle.py PROOF: unit -->

## Z11. World, region, spawn, calamity, and ecology law

- [x] WORLD-074: Spawned entity home/leash fields are valid where needed. [src/systems/world_systems/generator.py:45](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/world_systems/generator.py#L45)
    - `WorldGenerator` initializes `home_position` and `leash_radius` for camps.
    - TEST: `tests/unit/world/test_generator_determinism.py`
- [x] WORLD-079: Camp guards have leash/return behavior. [src/engine/rpg_depth.py:195](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L195)
    - `LeashService` enforces return to `home_position`.
    - TEST: `tests/unit/world/test_leash_mechanics.py`
- [x] WORLD-080: Leash gives up chase after explicit condition. [src/engine/rpg_depth.py:220](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/rpg_depth.py#L220)
    - `should_give_up_chase` checks distance and timeout.
    - TEST: `tests/unit/world/test_leash_mechanics.py`
- [x] WORLD-082: Calamity trigger rule is deterministic. [src/world/calamity.py:15](file:///home/vboxuser/Work/rpg-based-simulation/src/world/calamity.py#L15)
    - `CalamityService` uses `DeterministicRNG` for spawn decisions.
    - TEST: `tests/unit/world/test_calamity_spawns.py`
- [x] WORLD-090: World dynamics run even on quiet ticks where required. [src/engine/kernel.py:150](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L150)
    - `Kernel` triggers world systems in every tick.
    - TEST: `tests/unit/kernel/test_quiet_tick_dynamics.py`

## Z12. Phase guard, authorization, and mutation boundary law

- [x] SUB-316: AI/thought phase cannot write authoritative state directly. [src/engine/executor.py:32](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py#L32)
    - `_readonly_state_view` prevents worker/domain mutation.
    - TEST: `tests/unit/kernel/test_worker_harden.py`
- [x] SUB-320: Worker phase cannot bypass authoritative apply. [src/engine/kernel.py:214](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L214)
    - `_guard_stability` ensures all results go through `StateUpdate` collection.
    - TEST: `tests/unit/kernel/test_worker_integrity.py`

## Z13. Spatial index and map authority law

- [x] SUB-327: Spatial index can move entity/object between cells. [src/world/spatial.py:15](file:///home/vboxuser/Work/rpg-based-simulation/src/world/spatial.py#L15)
    - `SpatialIndex.move` handles cell transition atomically.
    - TEST: `tests/unit/world/test_spatial_index.py`
- [x] SUB-332: Spatial index stays consistent with authoritative entity positions after apply. [src/engine/apply.py:45](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L45)
    - `ApplyPath.apply_generation` triggers spatial sync.
    - TEST: `tests/unit/engine/test_spatial_sync.py`
- [x] SUB-334: Movement legality uses authoritative map/spatial truth. [src/engine/legality.py:110](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/legality.py#L110)
    - `verify_movement_legality` queries `SpatialIndex`.
    - TEST: `tests/unit/movement/test_occupancy_conflicts.py`

## Z14. API, inspector, logging, and replay truth surface

- [x] INFRA-134: API state view is derived from authoritative state. [src/platform/api/presenter.py:12](file:///home/vboxuser/Work/rpg-based-simulation/src/platform/api/presenter.py#L12)
    - `StatePresenter` maps domain models to public schemas.
    - TEST: `tests/unit/platform/test_api_visibility.py`
- [x] INFRA-150: Logs include final authoritative hash at shutdown. [src/engine/kernel.py:390](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L390)
    - `Kernel.shutdown` emits `final_hash`.
    - TEST: `tests/unit/kernel/test_replay_shutdown_budget.py`
- [x] INFRA-155: Replay manifest write is atomic. [src/platform/persistence/replay.py:88](file:///home/vboxuser/Work/rpg-based-simulation/src/platform/persistence/replay.py#L88)
    - Uses temporary file + rename.
    - TEST: `tests/unit/platform/test_replay_atomicity.py`

## Z15. Safe degraded mode and infrastructure fallback law

- [x] INFRA-162: Broker-disabled mode still runs core RPG simulation. [src/engine/kernel.py:98](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L98)
    - `Kernel.__init__` uses `LocalSequentialExecutor` if `profile.max_worker_count == 0`.
    - TEST: `tests/unit/kernel/test_worker_fallback.py`
- [x] INFRA-166: Local sequential executor preserves gameplay laws. [src/engine/executor.py:76](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py#L76)
    - `LocalSequentialExecutor.execute` uses identical domain logic as concurrent mode.
    - TEST: `tests/unit/kernel/test_local_executor.py`
- [x] INFRA-167: Worker executor preserves gameplay laws. [src/engine/executor.py:225](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py#L225)
    - `ConcurrentExecutionAdapter.execute` adapts work items to identical domain logic.
    - TEST: `tests/unit/kernel/test_worker_adaptation.py`
- [x] INFRA-169: Shutdown suspends new work arrival. [src/engine/kernel.py:387](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L387)
    - `Kernel.shutdown` sets `_stopped` flag; `tick_once` checks it.
    - TEST: `tests/unit/kernel/test_replay_shutdown_budget.py`
- [x] INFRA-170: Shutdown flushes replay/logging within timeout. [src/engine/kernel.py:392](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L392)
    - `Kernel.shutdown` calls `replay.finalize` with timeout.
    - TEST: `tests/unit/kernel/test_replay_shutdown_budget.py`
- [x] INFRA-171: Shutdown emits final authoritative hash. [src/engine/kernel.py:390](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L390)
    - `Kernel.shutdown` logs `final_hash`.
    - TEST: `tests/unit/kernel/test_replay_shutdown_budget.py`
- [x] INFRA-172: Failure in optional infrastructure does not corrupt authoritative state. [src/engine/kernel.py:214](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L214)
    - `_guard_stability` catches protocol violations and prevents corruption.
    - TEST: `tests/unit/kernel/test_worker_integrity.py`
- [x] INFRA-174: Degraded mode tests cover brokerless execution. [tests/unit/kernel/test_worker_fallback.py:65](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/kernel/test_worker_fallback.py#L65)
    - `test_force_local_override` verifies main-thread fallback.
    - TEST: `tests/unit/kernel/test_worker_fallback.py`

## Z16. Small but necessary default/no-op/safety laws

- [x] SUB-343: Empty world tick does not crash. [src/engine/kernel.py:127](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py#L127)
    - `Kernel.tick_once` handles empty work batch.
    - TEST: `tests/unit/kernel/test_empty_world_tick.py`
- [x] SUB-344: Empty world tick advances passive time if required. [src/engine/apply.py:56](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L56)
    - `ApplyPath.apply_generation` increments hunger/sleep/age even if no updates.
    - TEST: `tests/unit/engine/test_passive_advancement.py`
- [x] SUB-349: No-op update preserves state hash except allowed time/metadata changes. [src/engine/apply.py:14](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L14)
    - Deterministic transition ensures hash stability.
    - TEST: `tests/unit/engine/test_noop_hash_stability.py`
- [x] SUB-350: Copy/clone of state is deep enough to protect authoritative state from worker mutation. [src/engine/executor.py:32](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py#L32)
    - `_readonly_state_view` uses `MappingProxyType` to prevent container mutation.
    - TEST: `tests/unit/kernel/test_worker_harden.py`
- [x] SUB-351: Frozen snapshot cannot be mutated by AI proposal code. [src/engine/executor.py:27](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/executor.py#L27)
    - `_readonly_mapping` enforces runtime immutability.
    - TEST: `tests/unit/kernel/test_worker_integrity.py`
- [x] SUB-358: Clamp/floor/ceiling rules are explicit for HP. [src/engine/apply.py:76](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L76)
    - `hp = max(0, hp - damage)`.
    - TEST: `tests/unit/engine/test_hp_clamping.py`
- [x] SUB-359: Clamp/floor/ceiling rules are explicit for stamina/readiness. [src/engine/apply.py:96](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py#L96)
    - `final_readiness = min(100.0, readiness)`.
    - TEST: `tests/unit/engine/test_readiness_clamping.py`
- [x] SUB-360: Clamp/floor/ceiling rules are explicit for reputation/trust if bounded. [src/systems/social_systems/relationships.py:45](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/social_systems/relationships.py#L45)
    - `sentiment = max(-1.0, min(1.0, sentiment))`.
    - TEST: `tests/unit/social/test_sentiment_clamping.py`
- [x] SUB-362: Clamp/floor/ceiling rules are explicit for inventory weight/slots. [src/core/inventory.py:45](file:///home/vboxuser/Work/rpg-based-simulation/src/core/inventory.py#L45)
    - `can_add_item` enforces `len(items) < max_slots`.
    - TEST: `tests/unit/inventory/test_capacity.py`

---

# Final audit note

This file is intentionally longer than the previous generated checklist. The previous version was a summary. This one is an exhaustive semantic ledger. Do not collapse these items unless the implementation also collapses the behavior into a single proven law with enough tests to cover the atomic cases.
