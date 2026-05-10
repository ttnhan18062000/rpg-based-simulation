# RPG Core Logic Checklist — Fresh V2 Re-Audit

> Fresh audit note: This version resets all previous verification marks/comments and re-marks completed logic only from the currently uploaded `all_src_updated(5).py` and `all_test_updated(5).py`. Historical `VERIFIED`, `RECOVERED`, and prior `[x]` marks were not reused as evidence.
>
> Evidence marker format: `SOURCE` is the current V2 source path, `TEST` is the current V2 test path, and `PROOF` is the proof style used for the mark.


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

- Resource pressure is not globally complete while `InteractionSystem`, `HarvestSystem`, and `LootSystem` can disagree.
- Resource conservation is not globally complete until every active harvest/loot path checks capacity before removing/depleting source objects.
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
- [x] `RPG-AUTH-001` Action proposals are typed intents, not direct world mutation. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-AUTH-002` Every gameplay side effect is represented as a typed update bucket (mind, perception, navigation, progression, identity, routine, interaction, spatial, building, social, social-event, reputation, strategic, world, combat-trace). <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-AUTH-003` Legacy reason strings and targets are coerced into structured authoritative reason/target models. <!-- SOURCE: src/core/enums.py TEST: tests/test_strategic_hardening.py PROOF: unit -->
- [x] `RPG-AUTH-004` World mutation happens after proposal generation, not inside worker thought code. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-AUTH-005` Action application supports partial rejection without corrupting unrelated update domains. <!-- SOURCE: src/core/updates.py TEST: tests/engine/test_hardening_e5.py PROOF: integration -->
- [x] `RPG-AUTH-006` Conflict resolution preserves one authoritative outcome per tick. <!-- SOURCE: src/core/updates.py TEST: tests/engine/test_hardening_e5.py PROOF: integration -->
- [x] `RPG-AUTH-007` Worker decision-making is decoupled from authoritative application. <!-- SOURCE: src/core/updates.py TEST: tests/engine/test_hardening_e5.py PROOF: integration -->
- [x] `RPG-AUTH-008` Replay and observability consume authoritative results rather than defining them. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

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
- [x] `RPG-COMBAT-001` Manhattan distance is the shared spatial metric for movement and combat range where claimed. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-002` Cardinal/tile movement and occupancy legality are explicit. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-COMBAT-003` Occupied-tile movement is rejected or redirected rather than silently overlapped. <!-- SOURCE: src/engine/legality.py TEST: tests/rpg/test_movement_congestion.py PROOF: unit -->
- [x] `RPG-COMBAT-004` Melee legality depends on adjacency/engagement rules, not raw damage stats. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-005` Ranged legality depends on range and line-of-sight rules. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-006` AoE legality is a function of target position and area-of-effect radius. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-007` World-time progression is distinct from readiness-based action cadence. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-008` Pathfinding avoids occupied tiles but allows targeting them. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-009` Movement cost and speed are applied during authoritative application, not in worker proposals. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-010` Damage calculation math is consistent with legacy rules. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-011` Movement intentions are distinct from movement execution results. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-012` Quiet ticks still advance passive world consequences. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-COMBAT-013` Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-014` Anti-stalemate logic handles repeated chase/kite/step-back loops. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-015` Movement intentions exist as semantic modes (pursue, retreat, hold, reposition, intercept, guard, regroup). <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-016` Congestion is handled through waiting/yielding/sidestepping/rerouting before weakening occupancy. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-COMBAT-017` Frame pacing is enforced at the kernel level. <!-- SOURCE: src/engine/kernel.py TEST: tests/test_strategic_hardening.py PROOF: integration -->
- [x] `RPG-COMBAT-018` Tick budget (max_tick_budget_ms) is enforced at the kernel level. <!-- SOURCE: src/engine/kernel.py TEST: tests/test_strategic_hardening.py PROOF: integration -->
- [x] `RPG-COMBAT-019` Tactical choice is a bounded choice among legal actions, not a geometry exploit. <!-- SOURCE: src/engine/tactical.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: integration -->

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
- [x] `RPG-RES-001` Looting is a channeled state with progress, interruption, and completion semantics. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-002` Harvesting is a channeled state tied to nearby resource-node legality and harvest duration. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-003` Loot/harvest can abort because of inventory slot pressure. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: unit -->
- [x] `RPG-RES-004` Loot/harvest can abort because of inventory weight pressure. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-005` Inventory state tracks both slots and weight/carry burden. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-006` Ground items, node yields, and inventory additions/removals are authoritative side effects. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-007` Town return is a real gameplay state, not a cosmetic teleport. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-008` Shop visits resolve bounded buy/sell behavior using inventory/gold truth. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-009` Blacksmith visits resolve recipe/crafting/material-gating behavior. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-010` Guild visits produce intel, quests, and material/resource hints. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-011` Inn/home/class-hall visits have distinct progression or recovery semantics. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-012` Building interactions are explicit gameplay slices, not generic proximity triggers. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

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
- [x] `RPG-STRAT-001` Strategic state is first-class and survives across ticks (directives, projects, objectives, concerns, blockers, obligations, contracts, offers, leads, candidate zones, hypotheses). <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-002` Current project/objective continuity is explicit and bounded. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-003` Project switching uses interruption resistance / margin logic, not full rescore every tick. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-004` Current project gets reservation/retention priority inside bounded strategic slices. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-005` Blockers are inferred from project/objective state and can be accurate or misdiagnosed under bounded cognition. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-006` Leads are retained under profile-specific bandwidth limits. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-007` Concerns are retained under profile-specific intake limits. <!-- SOURCE: src/systems/strategic.py TEST: tests/test_strategic_hardening.py PROOF: unit -->
- [x] `RPG-STRAT-008` Detours are suggested from blockers and leads within breadth/depth limits. <!-- SOURCE: src/systems/detour.py TEST: tests/test_strategic_hardening.py PROOF: unit -->
- [x] `RPG-STRAT-009` Rejected/tested leads are suppressed to avoid blind retries. <!-- SOURCE: src/systems/detour.py TEST: tests/test_strategic_hardening.py PROOF: unit -->
- [x] `RPG-STRAT-010` Strategic derivation respects the available bandwidth of the entity. (Law 197) <!-- SOURCE: src/systems/strategic.py TEST: tests/test_strategic_hardening.py PROOF: unit -->
- [x] `RPG-STRAT-011` Strategic overload is visible through bounded capacity metrics. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-012` Event interpretation can mutate directives, projects, concerns, and source trust. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-013` Knowledge remains uncertain (leads/candidate zones/hypotheses) until resolved. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-014` Cognition graph export exposes persisted strategic state without becoming the source of truth. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

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
- [x] `RPG-SOC-001` Private betrayal history can override public recruiter reputation. <!-- SOURCE: src/social/appraisal.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-002` Social learning updates familiarity/trust-like bonds from interaction evidence. <!-- SOURCE: src/social/appraisal.py TEST: tests/social/test_social_bonds.py PROOF: integration -->
- [x] `RPG-SOC-003` Social contracts and obligations are explicit strategic objects, not flavor text. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-004` Breaking or honoring contracts has persistent consequences. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-005` Public reputation is distinct from private narrative meaning. <!-- SOURCE: src/social/appraisal.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-006` Turning points and interpreted life events feed future strategic and social behavior. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-007` Party/group cooperation is purpose-driven, not just proximity clustering. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-008` Recruitment evaluates trust, debt, greed, capability fit, and prior trauma. <!-- SOURCE: src/social/appraisal.py TEST: tests/social/test_recruitment.py PROOF: integration -->
- [x] `RPG-SOC-009` Group members prioritize group shared targets over personal projects. (Law 128) <!-- SOURCE: src/engine/tactical.py TEST: tests/systems/test_party_coordination.py PROOF: integration -->

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
- [x] `RPG-PROG-001` Attributes have domain ownership and scaling semantics. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-002` Class choice affects starting gear, skills, and progression paths. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-003` Skill scaling and breakthroughs are explicit progression systems. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-004` Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-005` Items obey contract rules (type, weight, equipment legality, consumable semantics). <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-PROG-006` NPC/hero contracts define role/class/gear boundaries. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-007` Specialization and milestone progression can mutate capability ceilings. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-008` RPG math and synergy rules are tested as stable contracts, not intuition. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

### World / entities / regions / spawning / deterministic substrate

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
- [x] `RPG-WORLD-001` World generation is deterministic under seed and domain-specific RNG use. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-002` Town, sanctuary, camps, buildings, corpses, and entities are authoritative world objects. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-003` Entity snapshots are immutable enough for worker reasoning and deterministic replay. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-WORLD-004` No hidden mutation leaks occur from snapshot or AI evaluation paths. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-WORLD-005` Deterministic replay/delta behavior is preserved across runs with same seed. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-WORLD-006` Regional hazards, calamities, local scars, and world consequences can feed gameplay and strategy. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] **RPG-WORLD-007**: V2EntityBuilder correctly initializes component-based EntityState. [src/core/builder.py:L202]
- [x] **RPG-INFRA-004**: ResourceGovernor watchdog correctly triggers DEGRADED mode on throttle signal. [src/engine/governor.py:L45]
- [x] **RPG-COMBAT-043**: Navigation uses FlowFieldService for global targets (>50m). [src/systems/navigation.py:L86]
- [x] **RPG-COMBAT-045**: FlowFieldService provides deterministic direction vectors for POIs. [src/systems/navigation.py:L22]
- [x] **RPG-COMBAT-046**: TacticalDecisionSystem implements VANGUARD bias for focus fire. [src/engine/tactical.py:L227]
- [x] **RPG-COMBAT-047**: TacticalDecisionSystem implements SUPPORT bias for ally proximity. [src/engine/tactical.py:L330]
- [x] **RPG-COMBAT-048**: TacticalDecisionSystem implements PROTECTOR bias for wounded shielding. [src/engine/tactical.py:L330]
- [x] **RPG-COMBAT-049**: CombatResolutionSystem resolves AOE attacks with splash damage. [src/engine/combat.py:L387]
- [x] **RPG-COMBAT-050**: CombatResolutionSystem resolves multi-attack simultaneous intents. [src/engine/combat.py:L297]
- [x] `RPG-WORLD-008` Engine phase order preserves gameplay semantics and subsystem tick integrity. <!-- SOURCE: src/engine/kernel.py TEST: tests/engine/test_phase_order_contract.py PROOF: integration -->

## B. Test-derived atomic checklist (every included RPG-core test)

Each checkbox below is derived from one original test. Keep the original test name in the ledger so `src` comparison stays auditable.

### Combat / movement rulebook & combat-time

#### `ai/test_tactical_milestone_4.py`

- [x] `RPG-COMBAT-020` `test_reactive_cover_seeking`: Reactive cover seeking — Verify that actor seeks cover only when a ranged threat is visible.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-021` `test_chokepoint_holding`: Chokepoint holding — Verify that actor identifies and holds a 1-tile gap.. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-022` `test_cardinal_opposite_bracketing`: Cardinal opposite bracketing — Verify that two allies bracket a target from opposite sides.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-COMBAT-023` `test_tactical_mode_integration_handler`: Tactical mode integration handler — Verify that CombatHandler respects the tactical target_pos..

#### `arena/test_arena_harness_contract.py`

- [x] `RPG-DATA-001` `test_arena_structural_determinism`: Arena structural determinism — Verify that the arena produced structurally identical ScenarioReports for the same seed. This validates that the simulation and its reporting layer use stable, deterministic logic. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-001` `test_arena_stop_condition_wipe`: Arena stop condition wipe — Verify that the arena correctly detects when one side is eliminated.. <!-- SOURCE: src/certification/harness.py TEST: tests/engine/test_arena_stop_conditions.py PROOF: integration -->
- [x] `RPG-INFRA-002` `test_arena_stop_condition_timeout`: Arena stop condition timeout — Verify that the arena respects the max_ticks limit.. <!-- SOURCE: src/certification/harness.py TEST: tests/engine/test_arena_stop_conditions.py PROOF: integration -->
- [x] `RPG-API-001` `test_arena_stop_condition_stall`: Arena stop condition stall — Verify that the arena correctly detects lack of activity (STALL) as a telemetry report.. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-AUTH-009` `test_mutation_tripwire_during_decision`: Mutation tripwire during decision — Verify that any attempt to mutate entities during the decision phase raises a ReadOnlyError.. <!-- SOURCE: src/core/state.py TEST: tests/core/test_authoritative_state_contract.py PROOF: unit -->

#### `arena/test_arena_minimal.py`

- [x] `test_minimal_tick`: Minimal tick — Verify that we can run even 1 tick without hanging.. <!-- SOURCE: src/engine/kernel.py TEST: tests/engine/test_phase_order_contract.py PROOF: integration -->

#### `arena/test_arena_watchdog.py`

- [x] `RPG-INFRA-003` `test_watchdog_aborts_on_hang`: Watchdog aborts on hang — Verify that a tick hanging for > watchdog_timeout is aborted. <!-- SOURCE: src/engine/kernel.py TEST: tests/test_strategic_hardening.py PROOF: unit -->
- [ ] `RPG-INFRA-004` `test_watchdog_allows_fast_ticks`: Watchdog allows fast ticks — Verify that normal fast ticks are NOT aborted..

#### `arena/test_core_scenario_regression.py`

- [x] `test_regression_melee_mirror`: Regression melee mirror — Scenario 1v1-01: Symmetry Check.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_regression_kiting_open`: Regression kiting open — Scenario 1v1-02: Ranged vs Melee Open Field.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `test_regression_elite_vs_swarm`: Regression elite vs swarm — Scenario 1vm-01: Elite vs Swarm..

#### `arena/test_observability_audit.py`

- [x] `RPG-API-002` `test_rejection_audit_aggregation`: Rejection audit aggregation — Verify that authoritative rejections are captured in ScenarioReport. [Milestone 7]. <!-- SOURCE: src/engine/pipeline.py TEST: tests/engine/test_replay_determinism.py PROOF: integration -->
- [x] `RPG-API-003` `test_out_of_range_rejection`: Out of range rejection — Verify that combat out-of-range is explicitly rejected with structured reason. [Milestone 7]. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: integration -->

#### `arena/test_resource_isolation.py`

- [x] `test_resource_isolation_bounded_growth`: Resource isolation bounded growth — Verify that memory does not show a strong linear leak over many iterations.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

#### `combat/test_anti_stalemate.py`

- [x] `RPG-COMBAT-024` `test_stalemate_detection`: Stalemate detection. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-025` `test_stalemate_loop_breaker_boosts_flee`: Stalemate loop breaker boosts flee. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

#### `combat/test_anti_stalemate_milestone_2.py`

- [x] `test_stalemate_detection_and_breaker`: Stalemate detection and breaker — Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker.. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

#### `combat/test_combat_context_milestone_2.py`

- [x] `RPG-COMBAT-026` `test_high_ground_bonus`: High ground bonus — Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR.. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/world/test_local_environment_semantics.py PROOF: test -->
- [x] `RPG-COMBAT-027` `test_flanking_bonus`: Flanking bonus — Verify Flanking bonus applies when defender is bracketed north/south.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-028` `test_moved_penalty`: Moved penalty — Verify Moved Recently penalty applies when attacker has moved this tick.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-029` `test_ranged_cover_bonus`: Ranged cover bonus — Verify Cover bonus applies against ranged attacks when adjacent to WALL.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `combat/test_combat_movement_rulebook.py`

- [x] `RPG-COMBAT-030` `test_manhattan_distance`: Manhattan distance — Verify Manhattan distance calculation.. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-COMBAT-031` `test_orthogonal_adjacency`: Orthogonal adjacency — Verify that only orthogonal tiles are adjacent.. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-COMBAT-032` `test_check_range`: Check range — Verify range enforcement.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-033` `test_check_occupancy`: Check occupancy — Verify 1-unit-per-tile occupancy rule.. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-COMBAT-034` `test_aoe_legality`: Aoe legality — Verify AoE impact constraints.. <!-- SOURCE: src/engine/kernel.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: test -->
- [x] `RPG-COMBAT-035` `test_aoe_splash_radius`: Aoe splash radius — Verify entities affected by splash radius.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-036` `test_get_occupant_id`: Get occupant id — Verify occupant lookup.. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-COMBAT-037` `test_check_targeting_legality`: Check targeting legality — Verify consolidated targeting rules (Range + LOS).. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `combat/test_engagement_contract.py`

- [x] `RPG-COMBAT-038` `test_engagement_detection`: Engagement detection. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-039` `test_engagement_clears_on_separation`: Engagement clears on separation. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-040` `test_engagement_respects_hostility`: Engagement respects hostility. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `combat/test_opportunity_attacks.py`

- [x] `RPG-COMBAT-041` `test_oa_triggered_on_disengagement`: Oa triggered on disengagement. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-042` `test_oa_not_triggered_if_staying_engaged_with_same_attacker`: Oa not triggered if staying engaged with same attacker. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `combat/test_target_stickiness.py`

- [x] `test_target_stickiness_bias`: Target stickiness bias. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `combat/test_world_time_progression.py`

- [x] `RPG-WORLD-009` `test_passive_progression_on_quiet_tick`: Passive progression on quiet tick — Verify that biological decay and lifecycle systems run even if entity doesn't act.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-SOC-010` `test_hero_lifecycle_on_quiet_tick`: Hero lifecycle on quiet tick — Verify that HeroLifecycle (e.g. proximity bonding) runs even if no entity acts.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `engine/test_quiet_tick_integrity.py`

- [x] `RPG-WORLD-010` `test_scenario_1_dead_world_progression`: Scenario 1 dead world progression — Scenario 1: No living entities. Verify tick still increments and systems advance.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-WORLD-011` `test_scenario_2_sleeping_world_biological_decay`: Scenario 2 sleeping world biological decay — Scenario 2: All entities have high next_act_at. Verify biological decay hits.. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-SOC-011` `test_scenario_3_stationary_world_proximity_bonding`: Scenario 3 stationary world proximity bonding — Scenario 3: Two heroes are stationary. Verify bonding occurs via HeroLifecycleSystem.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-WORLD-012` `test_scenario_4_subsystem_advancement`: Scenario 4 subsystem advancement — Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply..

#### `integration/ai/test_wind_pillar_navigation.py`

- [ ] `RPG-COMBAT-043` `test_navigation_uses_flow_field_for_far_town`: Navigation uses flow field for far town.
- [x] `RPG-COMBAT-044` `test_navigation_uses_astar_for_near_target`: Navigation uses astar for near target. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-COMBAT-045` `test_navigation_uses_flow_field_for_world_boss`: Navigation uses flow field for world boss.

#### `test_party_tactics.py`

- [ ] `RPG-COMBAT-046` `test_vanguard_biases`: Vanguard biases.
- [ ] `RPG-COMBAT-047` `test_support_biases`: Support biases.
- [ ] `RPG-COMBAT-048` `test_protector_biases`: Protector biases.

#### `unit/ai/test_skirmish.py`

- [x] `RPG-COMBAT-049` `test_skirmish_boosts_move_for_ranged`: Skirmish boosts move for ranged. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-050` `test_skirmish_does_not_boost_melee`: Skirmish does not boost melee. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/ai/test_tactical_behavior_contract.py`

- [x] `RPG-COMBAT-051` `test_melee_striker_closes_distance`: Melee striker closes distance. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-052` `test_ranged_skirmisher_kites_when_close`: Ranged skirmisher kites when close. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-053` `test_ranged_skirmisher_maintains_distance`: Ranged skirmisher maintains distance. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-054` `test_safe_shot_detection`: Safe shot detection. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-055` `test_tactical_retreat_at_low_hp`: Tactical retreat at low hp. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-056` `test_group_spacing_preservation`: Group spacing preservation. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

#### `unit/core/logic/test_movement_model.py`

- [x] `RPG-COMBAT-057` `test_movement_model_basic_path`: Movement model basic path. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-058` `test_movement_model_yielding_priority`: Movement model yielding priority. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-059` `test_movement_model_stuck_threshold`: Movement model stuck threshold. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

### Resource interaction / inventory / town loop

#### `integration/gameplay/test_toughness_decay.py`

- [x] `RPG-PROG-009` `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-PROG-010` `test_stat_decay_inactivity`: Stat decay inactivity — Verify that stat decay can be triggered..
- [x] `RPG-PROG-011` `test_toughness_hardening_integration`: Toughness hardening integration — Integration test for the restored hardening logic in CombatAction.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `test_building_unification.py`

- [ ] `test_actor`: Actor.
- [x] `RPG-SOC-012` `test_visit_guild_no_legacy_goals`: Visit guild no legacy goals — Verify that visiting the guild produces StrategicUpdate and PerceptionUpdate, but no string goals.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-STRAT-015` `test_visit_blacksmith_blocker_emission`: Visit blacksmith blocker emission — Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-STRAT-016` `test_visit_class_hall_resolution`: Visit class hall resolution — Verify that learning a skill emits a strategic resolution for the corresponding capability blocker.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-STRAT-017` `test_visit_blacksmith_crafting_resolution`: Visit blacksmith crafting resolution — Verify that crafting an item emits a strategic resolution for the material blocker.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-013` `test_visit_home_upgrade_resolution`: Visit home upgrade resolution — Verify that home storage upgrade emits a strategic resolution for home maintenance.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-018` `test_detour_suggestion_lifecycle_awareness`: Detour suggestion lifecycle awareness — Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/ai/test_routine_cycle.py`

- [ ] `RPG-WORLD-013` `test_biological_decay_authoritative`: Biological decay authoritative.
- [ ] `RPG-STRAT-019` `test_sleep_goal_utility_at_night`: Sleep goal utility at night.
- [ ] `RPG-COMBAT-060` `test_nocturnal_predator_bonus`: Nocturnal predator bonus.

#### `unit/ai/test_routine_needs.py`

- [ ] `RPG-STRAT-020` `test_biological_utility_biasing`: Biological utility biasing.
- [x] `RPG-RES-014` `test_inn_visit_leads_to_sleeping`: Inn visit leads to sleeping. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-015` `test_home_visit_leads_to_eating`: Home visit leads to eating. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-INFRA-005` `test_sleeping_recovery_cycle`: Sleeping recovery cycle. <!-- SOURCE: src/engine/governor.py TEST: tests/certification/test_envelope_violations.py PROOF: integration -->

#### `unit/core/gameplay/test_item_contracts.py`

- [ ] `test_weapon_ranges_integrity`: Weapon ranges integrity — Verify that specific weapons have their intended ranges in the registry..
- [x] `test_weapon_power_integrity`: Weapon power integrity — Verify that core progression weapons have their primary power correctly set.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `test_registry_identity_integrity`: Registry identity integrity — Ensure all core items are successfully loaded and have consistent IDs..

#### `unit/systems/test_difficulty_scaling.py`

- [ ] `test_tier1_is_baseline`: Tier1 is baseline.
- [x] `test_tier4_has_higher_stats_than_tier1`: Tier4 has higher stats than tier1 — Same seed, same enemy tier - tier 4 difficulty should have higher HP/ATK.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_tier4_hp_significantly_higher`: Tier4 hp significantly higher — Tier 4 HP multiplier is 4.0x on base stats; with flat bonuses from traits/attributes the effective ratio will be lower but still substantial.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_difficulty_sets_level_range`: Difficulty sets level range — Entities in tier 3 should have level in [5, 10].. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `test_gold_scales_with_difficulty`: Gold scales with difficulty — Tier 4 gold multiplier is 4.0x..
- [ ] `test_race_tier4_stronger_than_tier1`: Race tier4 stronger than tier1.
- [x] `test_race_difficulty_tier_set`: Race difficulty tier set. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `test_race_level_in_range`: Race level in range. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `test_all_races_scale`: All races scale — All four races should scale with difficulty..
- [x] `test_boss_diff_capped_at_4`: Boss diff capped at 4. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `test_boss_diff_adds_one`: Boss diff adds one. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `test_spawn_default_is_tier1`: Spawn default is tier1. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `test_spawn_race_default_is_tier1`: Spawn race default is tier1. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

#### `unit/systems/test_toughness_decay.py`

- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `test_stat_decay_inactivity`: Stat decay inactivity — Verify that idling for 1000+ ticks triggers stat decay..

### Strategic mind / cognition / projects / blockers / leads

#### `ai/test_bounded_blockers.py`

- [ ] `test_accurate_diagnosis_high_wisdom`: Accurate diagnosis high wisdom.
- [ ] `test_misdiagnosis_low_wisdom`: Misdiagnosis low wisdom.

#### `ai/test_bounded_detours.py`

- [x] `test_detour_breadth_limit`: Detour breadth limit. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_detour_depth_limit_fallback`: Detour depth limit fallback. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_retry_suppression`: Retry suppression. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `ai/test_bounded_objective_continuity.py`

- [x] `test_objective_derivation_precedence_blocker_first`: Objective derivation precedence blocker first. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_objective_derivation_precedence_active_objective_if_no_blocker`: Objective derivation precedence active objective if no blocker. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_objective_derivation_precedence_first_unresolved_if_no_active`: Objective derivation precedence first unresolved if no active. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `ai/test_bounded_project_continuity.py`

- [x] `test_project_retention_when_rival_is_below_margin`: Project retention when rival is below margin. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_project_switch_when_rival_is_above_margin`: Project switch when rival is above margin. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `test_switch_margin_increases_with_higher_resistance_profile`: Switch margin increases with higher resistance profile.

#### `ai/test_bounded_strategic_slice.py`

- [ ] `test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity`: Low profile entity has smaller active slice than high profile entity.
- [x] `test_concern_intake_is_capped_by_profile`: Concern intake is capped by profile. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_lead_retention_is_capped_by_profile`: Lead retention is capped by profile. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_reserved_current_project_slot_is_used_when_current_project_exists`: Reserved current project slot is used when current project exists. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_dropped_candidate_counts_are_deterministic`: Dropped candidate counts are deterministic. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

#### `ai/test_cognition_capacity_determinism.py`

- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: Profile derivation is deterministic for same entity state. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `test_profile_derivation_is_independent_of_tick_in_milestone_1`: Profile derivation is independent of tick in milestone 1.
- [x] `test_profile_derivation_does_not_use_rng`: Profile derivation does not use rng. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

#### `ai/test_cognition_capacity_non_mutation.py`

- [ ] `test_build_profile_does_not_mutate_entity_attributes`: Build profile does not mutate entity attributes.
- [ ] `test_build_profile_does_not_mutate_caps`: Build profile does not mutate caps.
- [x] `test_build_profile_does_not_mutate_stamina`: Build profile does not mutate stamina. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `test_build_profile_returns_new_profile_object_each_call`: Build profile returns new profile object each call.

#### `ai/test_cognition_explainability.py`

- [x] `test_overload_metadata_population`: Overload metadata population — Verify that primary_overload_source and last_overload_tick are correctly populated in replay.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_personality_formula_impact`: Personality formula impact — Verify that personality archetypes and traits impact the capacity profile.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `test_inspector_smoke_coverage`: Inspector smoke coverage — Smoke test to ensure EntityInspector (AIPresenter) doesn't crash with new fields.. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->

#### `ai/test_cognition_integrity.py`

- [x] `test_ui_contract_alignment`: Ui contract alignment — Verify that every field in bounded_cognition_ui_contract.md exists in Pydantic schemas.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_feature_spec_replay_alignment`: Feature spec replay alignment — Verify that replay fields mentioned in feature spec are present in recorder.. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `test_feature_spec_graph_export_alignment`: Feature spec graph export alignment — Verify that graph export fields mentioned in feature spec are present in exporter..
- [ ] `test_test_matrix_existence`: Test matrix existence — Verify that all test modules mentioned in test_matrix.md actually exist..
- [x] `test_populated_artifact_consistency`: Populated artifact consistency — Verify that a live HeadlessRunner execution produces populated and consistent artifacts. [TRACK 1 HARDENING]. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_truth_surface_parity`: Truth surface parity — Verify that Replay, API Schema, and Cognition Graph maintain strict parity. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `test_documentation_alignment`: Documentation alignment — Verify that documented fields in intel_capacity_implementation_updated.md are real. [MILESTONE 8 PROOF].

#### `ai/test_directive_mutation_thresholds.py`

- [x] `test_directive_mutation_thresholds`: Directive mutation thresholds — Verify that directives only mutate after repeated thresholded events.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `ai/test_event_interpretation.py`

- [x] `test_stable_concern_generation`: Stable concern generation. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_unstable_panic_concern`: Unstable panic concern. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_interruption_resistance_stable`: Interruption resistance stable. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_interruption_resistance_unstable`: Interruption resistance unstable. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `test_identity_drift_resistance`: Identity drift resistance.
- [x] `test_rumor_sensitivity_unstable`: Rumor sensitivity unstable. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `ai/test_lead_learning.py`

- [ ] `test_learning_success`: Learning success.
- [ ] `test_learning_failure`: Learning failure.

#### `ai/test_social_cognition.py`

- [x] `test_social_blocker_detection_solo`: Social blocker detection solo. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_social_misjudgment_low_stability`: Social misjudgment low stability. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_social_bandwidth_pool_limiting`: Social bandwidth pool limiting. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `ai/test_source_trust_learning_loop.py`

- [x] `test_source_trust_learning_loop`: Source trust learning loop — Prove that future weighting is affected by source trust after a learning event.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `ai/test_uncertainty_resolution_loop.py`

- [x] `test_uncertainty_resolution_loop`: Uncertainty resolution loop — Prove that proximity to a rumored zone resolves imprecise leads into precise targets.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `core/test_cognition_graph_exporter.py`

- [x] `test_export_empty_strategy`: Export empty strategy — Verify export from an entity with no strategic state.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_export_with_core_strategic_state`: Export with core strategic state — Verify export of directives, projects, and objectives.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_export_determinism`: Export determinism — Verify that multiple exports from the same state are identical.. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `test_non_mutation`: Non mutation — Verify that exporter does not mutate the source entity..

#### `core/test_strategy_models.py`

- [x] `test_strategic_model_rebuild`: Strategic model rebuild — Verify pydantic model rebuild handles recursive refs.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_directive_creation`: Directive creation. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_state_defaults`: Strategic state defaults. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_state_serialization`: Strategic state serialization. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_cognition_graph_regression.py`

- [x] `test_cognition_graph_deterministic_simulation`: Cognition graph deterministic simulation — Verify that a simulation produces a valid, repeatable cognition graph.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `test_graph_structural_invariants`: Graph structural invariants — Verify that the graph follows structural rules across ticks..

#### `integration/strategy/test_strategic_brain_integration.py`

- [x] `test_strategic_pivot_on_regional_danger`: Strategic pivot on regional danger — Verify that heroes pivot from personal quests to regional stabilization during high-danger events.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_scar_detection`: Scar detection — Verify that heroes sense nearby world trauma (scars) and investigate.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_near_death_triggers_survival_consequences`: Near death triggers survival consequences — Verify that a NEAR_DEATH event generates a concern and suspends the current project via applicator.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_betrayal_mutates_directives`: Betrayal mutates directives — Verify that a salient betrayal turning point adds an 'Avenge' directive.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_divergent_home_response`: Divergent home response — Verify that only entities with place attachment react strongly to home damage.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_betrayal_trauma_affects_recruitment`: Betrayal trauma affects recruitment — Verify that a recent betrayal makes entities less willing to accept recruitment offers.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `integration/strategy/test_strategic_capacity_enforcement.py`

- [ ] `test_budget_enforcement_truncation`: Budget enforcement truncation — Verify that candidate_zone_limit correctly truncates the pool AND preserves highest-scored zones..
- [x] `test_source_trust_behavioral_impact`: Source trust behavioral impact — Verify that updating source trust results in different weighting in the next cycle. [MILESTONE 3]. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_overload_metrics_visibility`: Overload metrics visibility — Verify that primary_overload_source and metrics are populated when stressed.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_continuity.py`

- [x] `test_directive_mutation_salience_threshold`: Directive mutation salience threshold — Verify that only high-salience turning points trigger mutations.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_directive_priority_strengthening`: Directive priority strengthening — Verify that repeated high-salience events strengthen directive priority.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_continuity_hardening.py`

- [x] `test_strategic_objective_continuity`: Strategic objective continuity — Prove that an existing objective is preserved if the project remains stable and no high blockers appear.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_objective_resumption_aligns_with_tactical`: Objective resumption aligns with tactical — Verify that a resumed objective correctly drives goal selection.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_determinism.py`

- [x] `test_harness_determinism`: Harness determinism — Verify that two runs with the same seed produce byte-identical results.. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `test_harness_non_determinism_different_seed`: Harness non determinism different seed — Verify that different seeds produce different outcomes (basic sanity check).. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

#### `integration/strategy/test_strategic_explainability.py`

- [x] `test_candidate_zone_enforcement`: Candidate zone enforcement — Verify that candidate_zone_limit is enforced and drops excess zones.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `test_ally_evaluation_enforcement`: Ally evaluation enforcement — Verify that ally_evaluation_limit caps contracts and offers evaluated..
- [x] `test_overload_source_trauma`: Overload source trauma — Verify that heavy HP damage triggers 'trauma' as the primary overload source.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_switch_reason_transparency`: Switch reason transparency — Verify that a project switch provides a human-readable reason.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_persistence.py`

- [x] `test_persistence_boost_prevents_switching`: Persistence boost prevents switching — Verify that the persistence boost prevents switching to a slightly better project.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_project_lock_prevents_switching`: Project lock prevents switching — Verify that project_lock_until strictly prevents any switches despite critical concerns.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_interruption_threshold_overridden_by_major_threat`: Interruption threshold overridden by major threat — Verify that a massive threat CAN overcome the interruption threshold.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_pipeline_home_threat`: Strategic pipeline home threat — Verify the flow from life event through StrategicConsequenceService to project pivot.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_resume_restores_valid_objective`: Resume restores valid objective — Verify that brain restores the last active objective when resuming a project. [Strategy M2]. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_resumed_objective_survives_cycle`: Resumed objective survives cycle — Verify that a restored objective doesn't immediately flip back to ProjectRecord.objectives[0] if it matches. [Strategy M2]. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_replay_determinism.py`

- [x] `test_world_strategic_registry_deep_isolation`: World strategic registry deep isolation — Verify that WorldStrategicRegistry.copy() performs a deep copy.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_replay_graph_equality`: Strategic replay graph equality — Verify that replaying from a snapshot yields bit-identical cognition graphs.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_lead_outcome_grounding_verification`: Lead outcome grounding verification — Verify that precise leads correctly ground into world entities.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_resume_objective.py`

- [x] `test_objective_resume_reliability`: Objective resume reliability — Verify that a suspended objective is resumed correctly.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_structural_integrity.py`

- [x] `test_snapshot_strategic_isolation`: Snapshot strategic isolation — Verify that Snapshot.from_world deep-copies and freezes strategic state.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_update_merging_identical_ids`: Strategic update merging identical ids — Verify that ActionSystem merges updates with identical IDs correctly.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `test_serialization_round_trip`: Serialization round trip — Verify that StrategicState survives full JSON serialization round-trip..
- [x] `test_strategic_update_coercion_from_dict`: Strategic update coercion from dict — Verify that StrategicUpdate correctly coerces dicts to models (worker transport emulation).. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_transport.py`

- [x] `test_strategic_update_multi_record_transport`: Strategic update multi record transport — Verify that a single proposal can carry multiple strategic updates.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_update_repeated_id_last_one_wins`: Strategic update repeated id last one wins — Verify that repeated IDs in a single update follow last-one-wins semantics.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_update_idempotency_over_ticks`: Strategic update idempotency over ticks — Verify that applying the same update multiple times is idempotent.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `test_strategic_update_target_routing`: Strategic update target routing — Verify that strategic updates can be routed to a target entity.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategic_world_integration.py`

- [x] `test_world_strategic_registry_persistence`: World strategic registry persistence — Verify that WorldStrategicRegistry is preserved in snapshots.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_world_integration_system_pruning`: Strategic world integration system pruning — Verify that the system prunes expired world opportunities.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_telemetry_strategic_metrics`: Telemetry strategic metrics — Verify that TelemetrySystem collects strategic metrics. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/ai/strategy/test_strategic_biasing.py`

- [x] `test_biological_need_to_strategic_bias`: Biological need to strategic bias. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_directive_to_project_flow`: Directive to project flow. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_bias_impact_on_selection`: Strategic bias impact on selection. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/ai/strategy/test_strategic_uncertainty.py`

- [x] `test_contradiction_degrades_certainty`: Contradiction degrades certainty — Verify that leads with contradictions lose certainty based on profile sensitivity. [MILESTONE 5]. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_hypothesis_impacted_by_contradiction`: Hypothesis impacted by contradiction — Verify that hypotheses lose confidence when supporting leads are contradicted. [MILESTONE 5]. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/strategy/test_strategic_services.py`

- [x] `test_canonical_blocker_structure`: Canonical blocker structure — Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_snapshot_isolation`: Strategic snapshot isolation — Verify that deep copying an entity results in a fully isolated strategic tree.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_belief_decay_aoa_purity`: Belief decay aoa purity — Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_social_applicator_aoa_purity`: Social applicator aoa purity — Verify that SocialStateApplicator returns updates and does not mutate the world.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_concern_generation_near_death`: Concern generation near death. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_directive_mutation_near_death`: Directive mutation near death. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_project_mutation_interruption`: Project mutation interruption. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `test_strategic_update_blocker_merging`: Strategic update blocker merging — Verify that ActionSystem merges blockers from StrategicUpdate correctly.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/systems/test_strategy.py`

- [x] `test_influence_shifts_on_monster_death`: Influence shifts on monster death. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_influence_shifts_on_hero_death`: Influence shifts on hero death. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `test_war_state_transition`: War state transition.
- [x] `test_conquered_region_triggers_stronghold`: Conquered region triggers stronghold. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `test_stronghold_debuff_application`: Stronghold debuff application. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

#### `unit/systems/test_strategy_system.py`

- [ ] `test_war_declaration`: War declaration.
- [x] `test_territory_conquest`: Territory conquest. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `test_territory_liberation`: Territory liberation. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

### Social / contracts / reputation / lived consequences

#### `ai/test_betrayal_social_consequence.py`

- [x] `test_betrayal_social_consequence`: Betrayal social consequence — Verify that private betrayal trauma prevents recruitment even for reputable founders.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `ai/test_learning_social.py`

- [x] `test_intel_confirmation_by_sight`: Intel confirmation by sight — Verify that seeing a person mentioned in a lead confirms it and boosts trust.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `test_intel_refutation_by_exhaustion`: Intel refutation by exhaustion — Verify that failing to find a target refutes the lead and drops trust.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->

#### `core/test_lived_models.py`

- [x] `test_routine_profile_instantiation`: Routine profile instantiation — Verify RoutineProfile can be instantiated with hybrid scheduling.. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [ ] `test_place_attachment_instantiation`: Place attachment instantiation — Verify PlaceAttachment can be instantiated and supports sentiment..
- [x] `test_group_record_instantiation`: Group record instantiation — Verify GroupRecord supports shared tactical intent.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `test_entity_integration`: Entity integration — Verify Entity and IdentityAspect absorb new Phase 3 fields..
- [x] `test_world_state_registry`: World state registry — Verify GroupRegistry integration in WorldState.. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

#### `integration/gameplay/test_social_meaning.py`

- [x] `test_social_event_betrayal`: Social event betrayal — Verify that hitting an ally triggers a betrayal event and social bond shift.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_social_event_near_death_and_tp`: Social event near death and tp — Verify that a near-death experience creates a durable turning point.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_social_event_first_kill_milestone`: Social event first kill milestone — Verify that first kill increments reputation and notoriety.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `test_phase_3_social_contracts.py`

- [x] `test_recruitment_haggling_threshold`: Recruitment haggling threshold — Verify that candidates counter-offer when willingness is close to threshold.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_contract_outcome_consequences`: Contract outcome consequences — Verify that contract resolution returns correct intent updates for all members.. <!-- SOURCE: src/engine/kernel.py TEST: tests/p1_semantic_hardening.py PROOF: test -->
- [x] `test_role_aware_tactical_biases`: Role aware tactical biases — Verify that utility biases change based on contract role.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `unit/ai/test_social.py`

- [x] `test_inn_gossip`: Inn gossip. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [ ] `test_hero_trading`: Hero trading.

#### `unit/ai/test_social_integration.py`

- [x] `test_social_bias_on_goal_scoring`: Social bias on goal scoring — Verify that a high-trust bond increases SOCIAL goal score.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_reputation_impact_on_caution`: Reputation impact on caution — Verify low global reputation triggers defensive posture in cautious entities.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `unit/core/gameplay/test_npc_contracts.py`

- [x] `test_npc_loadout_integrity`: Npc loadout integrity — Verify that specific NPC tiers are assigned their canonical equipment.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `test_npc_kind_mapping_integrity`: Npc kind mapping integrity — Verify that race/tier combinations map to the correct semantic kind name..

#### `unit/core/models/test_social_milestones.py`

- [ ] `test_nemesis_milestone_creation`: Nemesis milestone creation.
- [x] `test_memory_salience_retention`: Memory salience retention. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `unit/core/models/test_social_registry_updates.py`

- [x] `test_combat_updates_social_registry`: Combat updates social registry. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_archetype_influence_on_social_deltas`: Archetype influence on social deltas. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `unit/strategy/test_social_reasoning_bounding.py`

- [x] `test_recruitment_offer_bounding_stable`: Recruitment offer bounding stable — Stable entities produce consistent offers without noise.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `test_recruitment_offer_bounding_unstable`: Recruitment offer bounding unstable — Unstable entities produce noisy/perturbed offers.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

#### `unit/systems/test_familiarity_scaling.py`

- [x] `test_cha_impacts_familiarity_gain`: Cha impacts familiarity gain — Verify that a hero with higher CHA gains familiarity faster.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

### Progression / classes / skills / attributes / rewards

#### `unit/ai/test_legend_legacy.py`

- [x] `test_narrative_memory_logging`: Narrative memory logging. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `test_bravery_modifiers`: Bravery modifiers.
- [x] `test_regional_suppression`: Regional suppression. <!-- SOURCE: src/engine/kernel.py TEST: tests/engine/test_phase5_negative_cases.py PROOF: test -->

#### `unit/combat/test_combat_rewards.py`

- [x] `test_kill_reward_emission_in_apply`: Kill reward emission in apply. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `test_no_reward_on_non_lethal_hit`: No reward on non lethal hit.

#### `unit/core/aspects/test_progression.py`

- [x] `test_undead_no_level_up`: Undead no level up — Undead should have a train_rate of 0.0 and never level up.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_milestone_level_up`: Milestone level up — Reaching a milestone like level 5 grants extra stats.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_veterancy_multipliers`: Veterancy multipliers — Veterancy Ranks should boost stats via StatsProxy.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_innate_talents_training`: Innate talents training — Talented attributes gain 2x points, weak attributes gain 0.5x.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_combat_veterancy_points`: Combat veterancy points — Combat yields veterancy points.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/core/aspects/test_skill_scaling.py`

- [x] `test_physical_skill_scaling`: Physical skill scaling. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_magical_skill_scaling`: Magical skill scaling. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_elemental_skill_scaling`: Elemental skill scaling. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/core/gameplay/test_attribute_synergy.py`

- [x] `test_luck_impacts_crit_rate_significantly`: Luck impacts crit rate significantly — Verify that Luck has a meaningful impact on critical hit rate.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `test_luck_impacts_loot_modifier`: Luck impacts loot modifier — Verify that Luck/Perception provides a loot rarity multiplier.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `test_per_based_hidden_discovery`: Per based hidden discovery — Verify that hidden entities are only visible with sufficient Perception..

#### `unit/core/gameplay/test_breakthroughs.py`

- [x] `test_breakthrough_is_added`: Breakthrough is added. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `test_breakthrough_applies_bonus`: Breakthrough applies bonus. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/core/gameplay/test_class_gear.py`

- [x] `RPG-PROG-012` `test_warrior_prefers_defensive_gear`: Warrior prefers defensive gear — Verify that a Warrior weights defensive stats higher than a Mage.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-013` `test_hero_starting_gear_integrity`: Hero starting gear integrity — Verify that each hero class has the correct starting gear defined.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

### World / entities / snapshot / determinism / engine authority

#### `core/test_snapshot_integrity.py`

- [x] `RPG-AUTH-010` `test_snapshot_immutability_enforced`: Snapshot immutability enforced. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-AUTH-011` `test_snapshot_entities_are_deep_copied`: Snapshot entities are deep copied. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-AUTH-012` `test_snapshot_entities_are_frozen`: Snapshot entities are frozen. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->

#### `integration/engine/test_determinism.py`

- [x] `RPG-DATA-002` `test_simulation_determinism`: Simulation determinism — Verify that two identical simulations with the same seed produce the same result.. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-003` `test_different_seeds_different_hashes`: Different seeds different hashes — Verify that different seeds produce different world states.. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

#### `integration/engine/test_mutation_purity.py`

- [x] `RPG-AUTH-013` `test_aibrain_statelessness`: Aibrain statelessness. <!-- SOURCE: src/engine/worker_logic.py TEST: tests/engine/test_worker_determinism.py PROOF: unit -->

#### `integration/engine/test_snapshot_safety.py`

- [x] `RPG-AUTH-014` `test_entity_deep_copy_isolation`: Entity deep copy isolation — Verify that Entity.copy() provides absolute isolation for nested mutable structures.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-AUTH-015` `test_snapshot_actor_isolation`: Snapshot actor isolation — Verify that resolving an actor from a Snapshot ensures mutation safety.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-AUTH-016` `test_aspect_model_rebuild_integrity`: Aspect model rebuild integrity — Ensure that deep copies correctly initialize models and don't lose data..
- [ ] `RPG-AUTH-017` `test_lived_structure_isolation`: Lived structure isolation — Verify isolation for Phase 3 routine and attachment structures..

#### `unit/core/entities/test_entity_serialization.py`

- [ ] `RPG-API-004` `test_entity_to_full_schema_no_crash`: Entity to full schema no crash.
- [ ] `RPG-API-005` `test_entity_to_full_schema_minimal`: Entity to full schema minimal.

#### `unit/core/models/test_snapshot_purity.py`

- [x] `RPG-AUTH-018` `test_simulation_model_collection_freeze_list`: Simulation model collection freeze list — Verify that lists in SimulationModel become immutable after freeze.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: unit -->
- [x] `RPG-AUTH-019` `test_simulation_model_collection_freeze_dict`: Simulation model collection freeze dict — Verify that dicts in SimulationModel become immutable MappingProxy after freeze.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: unit -->
- [x] `RPG-AUTH-020` `test_world_state_freeze_guards`: World state freeze guards — Verify that WorldState prevents mutations after freeze.. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-AUTH-021` `test_snapshot_deep_purity`: Snapshot deep purity — Verify that Snapshot entities and their nested aspects are recursively frozen.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-AUTH-022` `test_action_proposal_guard_integration`: Action proposal guard integration — Verify the ActionProposalGuard context manager properly freezes the snapshot.. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

#### `unit/core/test_deep_freeze.py`

- [x] `RPG-AUTH-023` `test_deep_freeze_nested_collections`: Deep freeze nested collections — Verify that freeze() recursively converts nested collections to immutable types.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: unit -->
- [x] `RPG-AUTH-024` `test_deep_freeze_idempotency`: Deep freeze idempotency — Verify that calling freeze() multiple times is safe.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: unit -->

#### `unit/core/test_domain_invariants.py`

- [x] `RPG-COMBAT-061` `test_combat_aspect_invariants`: Combat aspect invariants. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-014` `test_progression_aspect_invariants`: Progression aspect invariants. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-AUTH-025` `test_freeze_calls_validate`: Freeze calls validate.
- [ ] `RPG-AUTH-026` `test_nested_freeze_invariants`: Nested freeze invariants.

#### `unit/core/test_invariants.py`

- [ ] `RPG-COMBAT-062` `test_speed_delay_invariants`: Speed delay invariants — Test that speed_delay never returns NaN or out-of-bounds values..
- [ ] `RPG-COMBAT-063` `test_stats_invariants`: Stats invariants — AOA Stabilization: Test CombatAspect invariants (formerly Stats)..
- [x] `RPG-COMBAT-064` `test_damage_calc_math`: Damage calc math — Test the core damage calculation logic in isolation.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-015` `test_recalc_level_consistency`: Recalc level consistency — Ensure level-based stat recalculation remains consistent across aspects.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-065` `test_combat_damage_invariants`: Combat damage invariants — Ensure HP reduction application doesn't cause overflow or invalid states.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/systems/test_calamity_evolution.py`

- [x] `RPG-WORLD-014` `test_calamity_evolution`: Calamity evolution. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

### Unclassified-but-included RPG-core tests

#### `ai/test_intel_capacity_regression.py`

- [x] `RPG-DATA-004` `test_intel_capacity_replay_and_graph_export`: Intel capacity replay and graph export — Verify that cognitive metrics survive replay and graph export pipelines.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-005` `test_intel_capacity_determinism`: Intel capacity determinism — Verify that identical seeds produce identical cognitive profiles and artifacts.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-006` `test_intel_capacity_overload_injection`: Intel capacity overload injection — Inject extreme cognitive pressure and verify overload triggering in artifacts.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-007` `test_intel_capacity_divergence_scenario`: Intel capacity divergence scenario — Verify that different attributes lead to differing usage artifacts.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-008` `test_intel_capacity_detour_depth_hardbound`: Intel capacity detour depth hardbound — Verify that detour depth is capped in artifacts even under pressure.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

#### `ai/test_intel_capacity_visibility.py`

- [x] `RPG-API-006` `test_cognition_api_serialization`: Cognition api serialization — Verify that cognitive metrics are correctly serialized for the API.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-INFRA-006` `test_cognition_inspector_rendering`: Cognition inspector rendering — Verify that the CLI inspector correctly renders cognitive data.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-API-007` `test_cognition_empty_profile`: Cognition empty profile — Verify that inspector handles entities without cognitive profiles gracefully.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_building_to_strategy_pipeline.py`

- [x] `RPG-DATA-009` `test_rng`: Rng. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-AUTH-027` `test_entity`: Entity.
- [x] `RPG-STRAT-021` `test_guild_intel_to_strategy_visible_pipeline`: Guild intel to strategy visible pipeline — Verify that guild intel produces leads/zones that are visible in API schemas.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-STRAT-022` `test_blacksmith_blocker_resolution_pipeline`: Blacksmith blocker resolution pipeline — Verify that blacksmith constraints produce blockers that are resolved by acquisition.. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->

#### `integration/strategy/test_knowledge_continuity_stabilization.py`

- [x] `RPG-STRAT-023` `test_milestone_3_lead_testing_and_persistence`: Milestone 3 lead testing and persistence — Verify that exhausted search marks leads as tested and persists them.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-013` `test_milestone_4_social_filtering`: Milestone 4 social filtering — Verify that social candidate selection filters hostiles and uses debt.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-024` `test_strategic_uncertainty_and_anti_cheating`: Strategic uncertainty and anti cheating — Verify that rumors have lower certainty and vague leads don't 'cheat' with perfect coords.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_lead_feedback_loops.py`

- [x] `RPG-STRAT-025` `test_source_trust_recalibration`: Source trust recalibration — Verify that a 'False' lead outcome reduces source trust.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-026` `test_severe_failure_abandonment_impact`: Severe failure abandonment impact — Verify that a project switch/abandonment reflects in strategic drivers.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `integration/strategy/test_strategy_observability_consistency.py`

- [x] `RPG-DATA-010` `test_rng`: Rng. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-AUTH-028` `test_entity`: Entity.
- [x] `RPG-API-008` `test_strategy_observability_consistency`: Strategy observability consistency — Verify that a strategic shift is consistently observable across all surfaces.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-027` `test_strategic_decision_driver_traceability`: Strategic decision driver traceability — Verify that DecisionDriver records flow from AIBrain to the entity state.. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `movement/test_congestion_milestone_3.py`

- [x] `RPG-COMBAT-066` `test_blocked_retreat_yield`: Blocked retreat yield — Verify high-priority RETREAT ally forces yield from lower-priority ally.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-COMBAT-067` `test_oscillation_suppression`: Oscillation suppression — Verify A-B-A-B movement is suppressed after 2 cycles.. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-068` `test_reroute_hysteresis`: Reroute hysteresis — Verify minor reroutes are ignored to prevent flip-flopping.. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-069` `test_safe_sidestepping`: Safe sidestepping — Verify yielding entities do not sidestep closer to danger.. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

#### `unit/ai/strategy/test_recruitment_negotiation.py`

- [x] `RPG-SOC-014` `test_recruitment_offer_generation`: Recruitment offer generation — Verify that a recruiter creates a reasonable offer based on greed and risk. [PHASE 4]. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-015` `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend. [PHASE 4]. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-016` `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend. [PHASE 4]. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-017` `test_recruiter_evaluates_counter`: Recruiter evaluates counter — Verify recruiter accepts a counter-offer for an urgent project. [PHASE 4]. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/ai/test_action_styles.py`

- [ ] `RPG-COMBAT-070` `test_execution_phase_modifies_proposal_with_aggressive_style`: Execution phase modifies proposal with aggressive style.
- [ ] `RPG-COMBAT-071` `test_execution_phase_modifies_proposal_with_evasive_style`: Execution phase modifies proposal with evasive style.

#### `unit/ai/test_ai_heuristics.py`

- [ ] `RPG-STRAT-028` `test_ai_boredom_diversification`: Ai boredom diversification — Verify that an entity eventually shifts away from a repetitive goal due to boredom..
- [x] `RPG-PROG-016` `test_life_stage_priority_shift`: Life stage priority shift — Verify level 1 and level 25 entities have different goal preferences.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/ai/test_attention.py`

- [ ] `RPG-STRAT-029` `test_perception_phase_populates_attention_pool`: Perception phase populates attention pool.

#### `unit/ai/test_belief_cycle.py`

- [x] `RPG-STRAT-030` `test_belief_refresh_captures_apparent_state`: Belief refresh captures apparent state. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-031` `test_belief_decay_lifecycle`: Belief decay lifecycle. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-032` `test_threat_estimation_logic`: Threat estimation logic. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

#### `unit/ai/test_cognitive_pipeline.py`

- [ ] `RPG-AUTH-029` `test_decide_produces_consistent_result`: Decide produces consistent result.
- [x] `RPG-WORLD-015` `test_decide_increments_idle_ticks_on_rest`: Decide increments idle ticks on rest. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-STRAT-033` `test_perception_phase_appraisal_sync`: Perception phase appraisal sync. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/ai/test_combos.py`

- [ ] `test_shatter_combo`: Shatter combo.

#### `unit/ai/test_emotional_memory.py`

- [x] `RPG-SOC-018` `test_locational_trauma_triggers_dread`: Locational trauma triggers dread — Verify entering a high-trauma region increments DREAD.. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-SOC-019` `test_emotional_bias_on_utility`: Emotional bias on utility — Verify DREAD increases FLEE utility and decreases EXPLORE utility..
- [ ] `RPG-SOC-020` `test_emotional_decay`: Emotional decay — Verify emotions propose negative delta for decay..

#### `unit/ai/test_emotions.py`

- [x] `RPG-COMBAT-072` `test_appraisal_phase_triggers_panic_on_low_hp`: Appraisal phase triggers panic on low hp. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/ai/test_flanking.py`

- [x] `RPG-COMBAT-073` `test_flanking_bonus`: Flanking bonus. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-074` `test_no_flanking_bonus_when_facing_attacker`: No flanking bonus when facing attacker. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/ai/test_flow_fields.py`

- [ ] `RPG-COMBAT-075` `test_flow_field_basic_navigation`: Flow field basic navigation.
- [ ] `RPG-COMBAT-076` `test_flow_field_respects_terrain_cost`: Flow field respects terrain cost.
- [ ] `RPG-COMBAT-077` `test_flow_field_smoothing_normalization`: Flow field smoothing normalization — Verify that get_vector returns a normalized Vector2..
- [ ] `RPG-COMBAT-078` `test_flow_field_smoothing`: Flow field smoothing — Verify that get_vector uses neighbor averaging for smoother curves..
- [ ] `RPG-INFRA-007` `test_cache_with_ttl`: Cache with ttl.

#### `unit/ai/test_flow_fields_refinement.py`

- [ ] `RPG-COMBAT-079` `test_bilinear_interpolation_basic`: Bilinear interpolation basic.
- [ ] `RPG-COMBAT-080` `test_static_target_caching`: Static target caching.
- [ ] `RPG-COMBAT-081` `test_moving_target_ttl`: Moving target ttl.

#### `unit/ai/test_narrative_memory.py`

- [x] `RPG-SOC-021` `test_narrative_memory_trauma_biasing`: Narrative memory trauma biasing. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-SOC-022` `test_narrative_memory_victory_confidence`: Narrative memory victory confidence.
- [x] `RPG-WORLD-016` `test_region_fatigue_biasing`: Region fatigue biasing. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-SOC-023` `test_social_appraisal_with_narrative`: Social appraisal with narrative. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

#### `unit/ai/test_personality.py`

- [ ] `RPG-STRAT-034` `test_motive_modifier_biases_explore`: Motive modifier biases explore.
- [x] `RPG-STRAT-035` `test_motive_modifier_biases_rest`: Motive modifier biases rest. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-STRAT-036` `test_motive_modifier_biases_flee`: Motive modifier biases flee.

#### `unit/ai/test_score_modifiers.py`

- [ ] `RPG-STRAT-037` `test_boredom_modifier_applies_multipliers`: Boredom modifier applies multipliers.
- [ ] `RPG-PROG-017` `test_life_stage_modifier_early_bracket`: Life stage modifier early bracket.
- [ ] `RPG-STRAT-038` `test_goal_evaluator_uses_modifiers`: Goal evaluator uses modifiers.

#### `unit/ai/test_softmax.py`

- [ ] `RPG-STRAT-039` `test_softmax_distribution`: Softmax distribution.
- [ ] `RPG-STRAT-040` `test_softmax_with_equal_scores`: Softmax with equal scores.

#### `unit/ai/test_stuck.py`

- [x] `RPG-STRAT-041` `test_perception_tracks_position_history`: Perception tracks position history. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-STRAT-042` `test_appraisal_detects_stuck`: Appraisal detects stuck. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

#### `unit/combat/test_building_sabotage.py`

- [ ] `RPG-COMBAT-082` `test_validate_building_target`: Validate building target.
- [x] `RPG-COMBAT-083` `test_apply_building_sabotage`: Apply building sabotage. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->

#### `unit/combat/test_combat_building.py`

- [x] `RPG-COMBAT-084` `test_building_sabotage_validation`: Building sabotage validation. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-COMBAT-085` `test_building_sabotage_application`: Building sabotage application. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->

#### `unit/combat/test_consequences.py`

- [x] `RPG-COMBAT-086` `test_wound_infliction_massive_hit`: Wound infliction massive hit — Verify that damage > 25% max HP guarantees a wound.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-087` `test_wound_stat_impact`: Wound stat impact — Verify that wounds correctly reduce properties in CombatAspect.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-018` `test_scar_permanence`: Scar permanence — Verify that scars are permanent and identifiable.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/combat/test_exhaustion.py`

- [x] `RPG-RES-016` `test_stamina_drain_on_attack`: Stamina drain on attack — Verify that a basic attack drains stamina from the actor.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-RES-017` `test_exhaustion_penalty_application`: Exhaustion penalty application — Verify that ActionSystem applies fatigue effect when stamina is low.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/core/aspects/test_aoa_integrity.py`

- [ ] `RPG-AUTH-030` `test_entity_field_integrity`: Entity field integrity — Ensure Entity model_fields contains only the ID, Kind, and Aspects..
- [ ] `RPG-AUTH-031` `test_entity_property_locking`: Entity property locking — Ensure no forbidden legacy properties have been re-introduced as shims..
- [ ] `RPG-AUTH-032` `test_aspect_model_purity`: Aspect model purity — Ensure aspects themselves stay clean of Cross-Aspect dependencies..
- [ ] `RPG-AUTH-033` `test_mandatory_aspect_naming`: Mandatory aspect naming — Aspects must be named exactly as their type (lowercase)..

#### `unit/core/aspects/test_evolution.py`

- [x] `RPG-PROG-019` `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap. [AOA REFACTOR]. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-020` `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment. [AOA REFACTOR]. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/core/aspects/test_genetics.py`

- [x] `RPG-DATA-011` `test_genetic_seed_init`: Genetic seed init. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-PROG-021` `test_training_uses_aptitudes`: Training uses aptitudes. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-022` `test_aging_and_death`: Aging and death. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/core/logic/test_person_logic.py`

- [ ] `RPG-SOC-024` `test_personality_bias_logic`: Personality bias logic.
- [x] `RPG-SOC-025` `test_social_appraisal_logic`: Social appraisal logic. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-026` `test_full_motive_pipeline_integration`: Full motive pipeline integration — Verifies that social and personality biases stack correctly.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

#### `unit/core/logic/test_routine_service.py`

- [ ] `RPG-STRAT-043` `test_routine_service_sleep_bias`: Routine service sleep bias.
- [x] `RPG-STRAT-044` `test_routine_service_forced_rest_during_off_hours`: Routine service forced rest during off hours. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-STRAT-045` `test_routine_service_hunger_bias`: Routine service hunger bias.

#### `unit/core/models/test_phase4_models.py`

- [ ] `RPG-DATA-012` `test_history_registry_serialization`: History registry serialization.
- [ ] `RPG-DATA-013` `test_household_record`: Household record.
- [x] `RPG-DATA-014` `test_local_scar_record`: Local scar record. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-DATA-015` `test_region_consequence_record`: Region consequence record. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-016` `test_world_state_integration_phase4`: World state integration phase4. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

#### `unit/core/models/test_serialization_hardened.py`

- [ ] `RPG-DATA-017` `test_json_encoder_mapping_proxy`: Json encoder mapping proxy.
- [ ] `RPG-DATA-018` `test_json_encoder_enum`: Json encoder enum.
- [ ] `RPG-DATA-019` `test_json_encoder_enum`: Json encoder enum.
- [x] `RPG-DATA-020` `test_serialization_frozen_model_with_proxy`: Serialization frozen model with proxy. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-DATA-021` `test_serializer_loads`: Serializer loads.

#### `unit/core/test_aoa_coercion.py`

- [x] `RPG-AUTH-034` `test_vector2_coercion_during_freeze`: Vector2 coercion during freeze — CRITICAL ARCHITECTURAL VERIFICATION: Ensures that if a field expecting a SimulationModel subclass (like Vector2) contains a raw dict (e.g. from serialization drift), the freeze() logic authoritatively coerces it back to the proper object before applying proxies.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

#### `unit/core/test_depth_features.py`

- [x] `RPG-RES-018` `test_well_rested_effect_application`: Well rested effect application — Verify that the Well-Rested buff correctly affects Max HP and XP mult.. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-023` `test_attribute_synergy_xp_mult`: Attribute synergy xp mult — Verify that Wisdom/Intelligence correctly affects XP multiplier.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-024` `test_class_weighted_gear`: Class weighted gear — Verify that item power is correctly weighted for different classes.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/core/test_eb_isolated.py`

- [ ] `RPG-PROG-025` `test_eb_stats_scaling`: Eb stats scaling.

#### `unit/core/test_performance_optimizations.py`

- [ ] `RPG-DATA-022` `test_grid_bytearray_correctness`: Grid bytearray correctness — Verify Grid correctly stores and retrieves materials using bytearray and cache..
- [x] `RPG-AUTH-035` `test_grid_copy_is_not_shared`: Grid copy is not shared — Verify Grid.copy() duplicates the bytearray data.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-AUTH-036` `test_entity_copy_shallow_vs_refs`: Entity copy shallow vs refs — Verify Entity.copy() is shallow for aspects but produces a new Entity object.. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-INFRA-008` `test_ai_worker_batch_processing_logic`: Ai worker batch processing logic — Verify AIWorkerDaemon correctly handles a batch of tasks..

#### `unit/systems/test_action_convergence.py`

- [x] `RPG-RES-019` `test_loot_no_duplication`: Loot no duplication — Verify that items picked up by the system are not duplicated by AI updates.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-020` `test_corpse_loot_convergence`: Corpse loot convergence — Verify that corpse recovery is authoritatively handled by ActionSystem.. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

#### `unit/systems/test_dynamic_quests.py`

- [x] `RPG-STRAT-046` `test_dynamic_liberate_quest`: Dynamic liberate quest. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-DATA-023` `test_history_logging`: History logging. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->

#### `unit/systems/test_evolution.py`

- [x] `RPG-PROG-026` `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-027` `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment.. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

#### `unit/systems/test_personality_ai.py`

- [x] `RPG-SOC-027` `test_grudge_accumulation`: Grudge accumulation. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-STRAT-047` `test_should_flee_logic`: Should flee logic.
- [x] `RPG-SOC-028` `test_locational_memory_on_death`: Locational memory on death. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-WORLD-017` `test_frontier_locational_penalty`: Frontier locational penalty.

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

- [ ] preserved
- [ ] intentionally divergent
- [ ] unsupported
- [ ] not yet checked

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

- [ ] `RPG-INFRA-009` `python -m src` defaults to server mode when no subcommand is provided.
- [x] `RPG-INFRA-010` `python -m src serve` accepts the original `--host`, `--port`, `--seed`, `--entities`, `--workers`, `--log-level` arguments. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-INFRA-011` `python -m src cli` accepts the original `--ticks`, `--entities`, `--seed`, `--workers`, `--grid-width`, `--grid-height`, `--replay`, `--log-level` arguments. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-INFRA-012` `python -m src inspect` accepts the original `--id`, `--seed`, `--ticks`, `--entities`, `--workers`, `--log-level` arguments. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-INFRA-013` CLI argument defaults remain compatible with legacy expectations. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [x] `RPG-INFRA-014` Invalid CLI arguments fail in a controlled, parser-driven way. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [x] `RPG-INFRA-015` CLI replay-file argument writes to the expected output path semantics. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-016` CLI mode still initializes the same baseline world-building flow (town, sanctuary, camps, hero spawn, goblin spawn) under equivalent config. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

### CLI environment boot behavior

- [x] `RPG-INFRA-017` CLI mode forces broker-disabled behavior through environment setup when not already set. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [x] `RPG-INFRA-018` CLI startup still loads registries before simulation loop startup. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [x] `RPG-INFRA-019` CLI startup still wires logging before engine loop execution. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-INFRA-020` CLI shutdown still tears down worker infrastructure cleanly after simulation. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->

---

# B. Optional-broker disabled-mode compatibility

Relevant original source/test evidence:

- `tests/api/test_broker_isolation.py`
- `tests/integration/infra/test_brokerless_import.py`

### RabbitMQ disabled-mode behavior

- [ ] `RPG-INFRA-021` `DISABLE_RABBITMQ=1` causes RabbitMQ client code to enter explicit disabled mode.
- [ ] `RPG-INFRA-022` RabbitMQ client imports do not crash when disabled.
- [ ] `RPG-INFRA-023` RabbitMQ public accessors return safe no-op values (`None`) when disabled.
- [ ] `RPG-INFRA-024` RabbitMQ disabled-mode behavior remains safe even when broker libraries are missing.

### Kafka disabled-mode behavior

- [ ] `RPG-INFRA-025` `DISABLE_KAFKA=1` causes Kafka client code to enter explicit disabled mode.
- [ ] `RPG-INFRA-026` Kafka client imports do not crash when disabled.
- [ ] `RPG-INFRA-027` Kafka public accessors return safe no-op values (`None`) when disabled.
- [ ] `RPG-INFRA-028` Kafka disabled-mode behavior remains safe even when broker libraries are missing.

### Redis disabled / missing-package behavior

- [ ] `RPG-INFRA-029` Redis client behavior remains safe when Redis package or runtime is unavailable.
- [ ] `RPG-INFRA-030` Redis accessors fail safely without crashing simulation bootstrap when Redis is optional.

### Disabled-mode import isolation

- [x] `RPG-INFRA-031` Headless runner imports still succeed when optional brokers are disabled. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [ ] `RPG-INFRA-032` Action-system imports still succeed when optional brokers are disabled.
- [ ] `RPG-INFRA-033` Import-time behavior does not accidentally force broker setup.

---

# C. Worker-pool and infrastructure fallback behavior

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_infrastructure_isolation.py`
- worker-pool usage in original CLI and loop wiring

### Worker fallback semantics

- [ ] `RPG-INFRA-034` Worker pool falls back to inline/local execution when broker transport is unavailable.
- [ ] `RPG-INFRA-035` Worker pool does not require live RabbitMQ/Kafka to execute local simulation behavior.
- [ ] `RPG-INFRA-036` Worker fallback preserves authoritative action generation semantics.
- [x] `RPG-INFRA-037` Worker fallback preserves deterministic ordering expectations in local mode. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-038` Worker shutdown remains safe after fallback execution paths.
- [ ] `RPG-INFRA-039` Missing broker infrastructure does not block minimal simulation startup.

### Import/runtime isolation

- [ ] `RPG-INFRA-040` Infrastructure module isolation prevents optional dependencies from contaminating normal simulation imports.
- [ ] `RPG-INFRA-041` Runtime paths that do not require brokers do not import or initialize them accidentally.
- [ ] `RPG-INFRA-042` Fallback behavior is exercised by real tests, not only by mocks or assumptions.

---

# D. Chaos mode and infrastructure resilience

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_chaos.py`

### Chaos resilience

- [ ] `RPG-INFRA-043` Chaos-enabled runs survive AI-result drop conditions without immediate simulation failure.
- [ ] `RPG-INFRA-044` Chaos-enabled runs continue ticking through configured chaos-drop scenarios.
- [x] `RPG-INFRA-045` Chaos does not corrupt authoritative world state shape. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-INFRA-046` Chaos does not break snapshot acquisition. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->

### Chaos determinism

- [x] `RPG-INFRA-047` Given identical seed and identical chaos configuration, repeated chaos-mode runs remain deterministic. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-048` Chaos-mode determinism is verified by repeated world-state fingerprint comparison. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-INFRA-049` Chaos-enabled infrastructure does not introduce hidden non-determinism into equivalent runs. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

---

# E. Replay compatibility outside pure RPG-core semantics

Relevant original source/test evidence:

- replay usage in `src/__main__.py`
- replay-related explainability / determinism / regression tests
- `tests/e2e/test_deterministic_replay.py`

### Replay output contract

- [x] `RPG-DATA-024` Replay files are written in the expected legacy location/format semantics for headless runs. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-025` Replay snapshots preserve deterministic entity ordering and field availability where legacy tests rely on them. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-026` Replay preserves enough world-state detail to support legacy fingerprinting and regression assertions. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-027` Replay can support structural comparison between repeated runs with same seed. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-028` Replay remains aligned with other truth surfaces where legacy tests expect parity. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

### End-to-end deterministic replay path

- [x] `RPG-DATA-029` Same seed and equivalent configuration produce identical replay-visible state across runs. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-030` Different seeds produce divergent replay-visible state. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-031` Replay includes ground-item state where legacy determinism tests inspect it. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-032` Replay includes enough actor combat/progression/mind state for state-fingerprint checks. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

---

# F. Structured logging compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py`
- original logging setup and JSON formatter usage in source

### Logging format contract

- [x] `RPG-INFRA-050` CLI stdout logs remain valid JSON line-by-line. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [ ] Each emitted structured log includes mandatory fields:
  - [ ] `RPG-DATA-033` `timestamp`
  - [x] `RPG-DATA-034` `level` <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
  - [ ] `RPG-DATA-035` `message`
  - [ ] `RPG-DATA-036` `component`
- [x] `RPG-INFRA-051` Log output remains machine-parseable under normal CLI execution. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->

### Logging context injection

- [x] `RPG-DATA-037` World-loop logs include tick context. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-038` World-loop logs preserve identifiable component naming. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-DATA-039` Worker-pool logs preserve identifiable component naming where emitted.
- [ ] `RPG-DATA-040` Main entrypoint logs preserve identifiable `__main__` or equivalent component identity.
- [x] `RPG-DATA-041` Structured logging remains compatible with legacy context-injection expectations. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->

---

# G. Metrics and monitoring compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py` (Prometheus check)
- original metrics/logging stack wiring in source

### Prometheus / telemetry compatibility

- [x] `RPG-INFRA-052` Simulation metrics remain scrapeable by Prometheus in equivalent stack configurations. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-INFRA-053` Legacy-queried metric names remain available where replacement claims require them.
- [x] `RPG-INFRA-054` Tick-duration metrics remain emitted under the expected metric contract. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-INFRA-055` Monitoring stack checks do not silently pass with empty data. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

### Operational observability

- [x] `RPG-INFRA-056` Engine-side metrics remain available without forcing gameplay divergence. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-INFRA-057` Metrics do not rely on broker-only paths if local/headless execution is supposed to work without brokers. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-INFRA-058` Monitoring compatibility is verified under realistic stack conditions, not just unit stubs. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

---

# H. API protocol and transport compatibility

Relevant original source/test evidence:

- API metadata tests
- websocket handshake tests
- gzip compression test

### Metadata endpoints

- [x] `RPG-API-009` Protocol metadata endpoint remains available at the expected route. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-API-010` Metadata response still includes entity key mapping where legacy consumers expect it.
- [ ] `RPG-API-011` Metadata response still includes state enum mapping where legacy consumers expect it.
- [ ] `RPG-API-012` Protocol metadata field order/meaning remains compatible where clients depend on it.

### WebSocket protocol behavior

- [x] `RPG-API-013` WebSocket endpoint still supports legacy handshake semantics. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-API-014` JSON handshake mode remains supported.
- [ ] `RPG-API-015` MessagePack handshake mode remains supported.
- [ ] `RPG-API-016` Initial post-handshake payload remains structurally compatible with legacy client expectations.
- [ ] `RPG-API-017` Tick/entity/event payload shape remains compatible where explicitly defined by legacy tests.

### Compression behavior

- [x] `RPG-API-018` GZip middleware or equivalent response compression remains functional for large metadata responses. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-API-019` Compression support does not break standard metadata endpoint access. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->

---

# I. Headless runner / final-system execution compatibility

Relevant original source/test evidence:

- headless runner import/use tests
- deterministic replay tests
- brokerless import tests
- cognition/replay consistency regression tests

### Headless execution path

- [x] `RPG-INFRA-059` A minimal production-like headless run can still execute without optional brokers when disabled. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [x] `RPG-INFRA-060` Headless run still produces the expected result artifacts (at minimum replay, and where applicable manifest/graph outputs). <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-061` Headless runner import remains isolated from optional broker setup. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [ ] `RPG-INFRA-062` Final-system path remains suitable for regression use rather than demo-only use.

### Artifact consistency

- [ ] `RPG-DATA-042` Final-system artifacts remain mutually consistent where legacy tests compare them.
- [x] `RPG-DATA-043` Structural graph/export surfaces remain aligned with replay where legacy tests require parity. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-DATA-044` Artifact generation failure paths remain visible rather than silently swallowed.

---

# J. Infrastructure-side “unhappy path” compatibility actually evidenced in legacy tests

Only include source-grounded unhappy paths.

### Disabled/missing dependency paths

- [ ] `RPG-INFRA-063` Missing RabbitMQ package with disabled flag does not crash import.
- [ ] `RPG-INFRA-064` Missing Kafka package with disabled flag does not crash import.
- [ ] `RPG-INFRA-065` Missing Redis package does not crash safe initialization paths where optional.
- [x] `RPG-INFRA-066` Missing broker dependencies do not block headless runner imports. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->

### Runtime degradation paths

- [x] `RPG-INFRA-067` Worker transport degradation falls back safely to local execution. <!-- SOURCE: src/engine/governor.py TEST: tests/certification/test_envelope_violations.py PROOF: integration -->
- [ ] `RPG-INFRA-068` Chaos-mode packet/result drop does not terminate the simulation prematurely under supported settings.
- [ ] `RPG-INFRA-069` Monitoring checks fail loudly when expected data is missing.

### CLI/runtime robustness

- [x] `RPG-INFRA-070` CLI execution still emits structured logs under minimal simulation runs. <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [ ] `RPG-INFRA-071` Short runs still produce enough output for regression inspection.
- [x] `RPG-INFRA-072` Minimal runs do not require full external stack unless explicitly in E2E stack mode. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

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

- [x] `RPG-STRAT-048` `test_perception_phase_populates_attention_pool`: attention pool population <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-STRAT-049` `test_belief_refresh_captures_apparent_state`: belief refresh from apparent state <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-050` `test_belief_decay_lifecycle`: belief decay lifecycle <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-051` `test_belief_conflict_resolution`: belief conflict handling <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-052` `test_belief_sharing_propagation`: belief sharing propagation <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-053` `test_threat_estimation_logic`: threat estimation logic <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-STRAT-054` `test_perception_phase_appraisal_sync`: appraisal sync <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-055` `test_perception_tracks_position_history`: position-history tracking <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-STRAT-056` `test_appraisal_phase_triggers_panic_on_low_hp`: panic trigger via appraisal <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-057` `test_appraisal_detects_stuck`: stuck appraisal detection <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-SOC-029` `test_social_appraisal_logic`: social appraisal logic <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-030` `test_social_appraisal_with_narrative`: narrative-informed social appraisal <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

---

## B. Routine / motive / biological needs / life rhythm

Relevant original source/test evidence:

- `RoutineService`
- `ObjectiveDerivationService`
- `tests/unit/ai/test_routine.py`
- related rest/sleep/hunger tests in `all_test.py`

- [ ] `RPG-STRAT-058` `test_sleep_goal_utility_at_night`: sleep utility at night
- [x] `RPG-RES-021` `test_rest_to_sleep_transition`: rest-to-sleep transition <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-STRAT-059` `test_routine_service_sleep_bias`: sleep bias
- [x] `RPG-STRAT-060` `test_routine_service_forced_rest_during_off_hours`: forced off-hours rest <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-STRAT-061` `test_routine_service_hunger_bias`: hunger bias
- [x] `RPG-RES-022` `test_home_visit_leads_to_eating`: eating behavior from routine/home visit <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-023` `test_inn_visit_leads_to_sleeping`: inn visit leads to sleeping <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [ ] `RPG-RES-024` `test_biological_decay_and_forced_sleep`: biological decay and forced sleep
- [x] `RPG-RES-025` `test_sleeping_recovery_cycle`: sleeping recovery cycle <!-- SOURCE: src/engine/governor.py TEST: tests/certification/test_envelope_violations.py PROOF: integration -->
- [ ] `RPG-RES-026` `test_hunger_reduces_stability`: hunger consequence
- [ ] `RPG-STRAT-062` `test_routine_goal_priority`: routine goal priority
- [ ] `RPG-STRAT-063` `test_routine_disruption_panic`: disruption panic
- [ ] `RPG-STRAT-064` `test_attack_disruption_suppresses_routines`: attack suppresses routine
- [ ] `RPG-SOC-031` `test_routine_priority_archetype_bias`: archetype-based routine bias
- [ ] `RPG-PROG-028` `test_life_stage_priority_shift`: life-stage priority shift

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

- [ ] `RPG-STRAT-065` `test_ai_boredom_diversification`: boredom diversification effect
- [ ] `RPG-STRAT-066` `test_boredom_modifier_applies_multipliers`: boredom modifier law
- [ ] `RPG-PROG-029` `test_life_stage_modifier_early_bracket`: life-stage modifier law
- [ ] `RPG-STRAT-067` `test_motive_modifier_biases_explore`: motive modifier explore bias
- [x] `RPG-STRAT-068` `test_motive_modifier_biases_rest`: motive modifier rest bias <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-STRAT-069` `test_motive_modifier_biases_flee`: motive modifier flee bias
- [ ] `RPG-STRAT-070` `test_goal_evaluator_uses_modifiers`: goal evaluator modifier integration
- [ ] `RPG-STRAT-071` `test_softmax_distribution`: score-to-choice distribution
- [ ] `RPG-STRAT-072` `test_softmax_with_equal_scores`: equal-score handling

---

## D. Emotional / narrative memory / trauma logic

Relevant original source/test evidence:

- `MemorySalienceService`
- `EventInterpreterService`
- `tests/unit/ai/test_emotional_memory.py`
- `tests/unit/ai/test_narrative_memory.py`

- [x] `RPG-SOC-032` `test_locational_trauma_triggers_dread`: locational trauma -> dread <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-SOC-033` `test_emotional_bias_on_utility`: emotion changes utility
- [ ] `RPG-SOC-034` `test_emotional_decay`: emotional decay
- [x] `RPG-SOC-035` `test_narrative_memory_trauma_biasing`: trauma memory biasing <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-SOC-036` `test_narrative_memory_victory_confidence`: victory-confidence memory
- [x] `RPG-DATA-045` `test_narrative_memory_logging`: narrative memory logging <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-SOC-037` `test_social_appraisal_with_narrative`: narrative-informed social appraisal <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-SOC-038` `test_bravery_modifiers`: bravery modifiers

---

## E. Combat aftermath / wounds / scars / stamina / exhaustion

Relevant original source/test evidence:

- `DamageResolutionService`
- `CombatAftermathService`
- `tests/unit/combat/**`
- related stamina tests in `all_test.py`

- [x] `RPG-COMBAT-088` `test_wound_infliction_massive_hit`: wound infliction <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-089` `test_wound_stat_impact`: wound stat penalties <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-030` `test_scar_permanence`: scar permanence <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-031` `test_scar_decay`: scar decay behavior if preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-DATA-046` `test_local_scar_record`: local scar record <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-DATA-047` `test_scar_detection`: scar detection <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-SOC-039` `test_ai_perception_of_scars`: perception of scars
- [x] `RPG-RES-027` `test_stamina_drain_on_attack`: stamina drain on attack <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-RES-028` `test_stamina_decreases_on_move`: stamina drain on move <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-RES-029` `test_stamina_decreases_on_harvest`: stamina drain on harvest <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-030` `test_skill_use_costs_stamina`: stamina cost on skill use <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-RES-031` `test_stamina_regen_resting`: rest stamina regen <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-RES-032` `test_stamina_regen_active`: active regen
- [x] `RPG-RES-033` `test_stamina_regen_capped`: regen cap <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-RES-034` `test_exhaustion_penalty_application`: exhaustion penalty <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-RES-035` `test_best_ready_skill_skips_insufficient_stamina`: skill gating by stamina <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

---

## F. Tactical specialty / action style / combo behavior

Relevant original source/test evidence:

- combat/tactical logic in `all_src.py`
- `tests/unit/ai/test_action_styles.py`
- `tests/unit/ai/test_flanking.py`
- `tests/unit/ai/test_combos.py`

- [ ] `RPG-COMBAT-090` `test_execution_phase_modifies_proposal_with_aggressive_style`: aggressive action style
- [ ] `RPG-COMBAT-091` `test_execution_phase_modifies_proposal_with_evasive_style`: evasive action style
- [x] `RPG-COMBAT-092` `test_flanking_bonus`: flanking bonus <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-093` `test_no_flanking_bonus_when_facing_attacker`: facing-sensitive flanking exclusion <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-COMBAT-094` `test_shatter_combo`: combo behavior
- [x] `RPG-COMBAT-095` `test_ranged_hero_kites_when_adjacent`: ranged kiting <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-096` `test_ranged_skirmisher_kites_when_close`: ranged skirmish spacing <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

---

## G. Loot / hidden discovery / local reward realism

Relevant original source/test evidence:

- loot and discovery logic in `all_src.py`
- related tests in `all_test.py`

- [x] `RPG-RES-036` `test_luck_impacts_loot_modifier`: loot modifier from luck/perception <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-STRAT-073` `test_per_based_hidden_discovery`: hidden discovery from perception
- [x] `RPG-RES-037` `test_loot_recovery_consistency`: loot recovery consistency <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-038` `test_loot_no_duplication`: no duplicated loot <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-039` `test_corpse_loot_convergence`: corpse loot convergence <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-040` `test_loot_and_respawn`: loot and respawn interaction <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-041` `test_loot_tables_exist`: loot table integrity <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-042` `test_full_bag_aborts_looting`: abort looting when full <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-043` `test_overweight_aborts_looting`: abort looting when overweight <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-044` `test_near_weight_limit_penalizes_loot`: weight-limit penalty on looting <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

---

## H. Region-scale strategic and world consequences

Relevant original source/test evidence:

- `StrategicConsequenceService`
- `WorldConsequenceInterpretationService`
- region/world consequence tests in `all_test.py`

- [x] `RPG-WORLD-018` `test_regional_suppression`: regional suppression <!-- SOURCE: src/engine/kernel.py TEST: tests/engine/test_phase5_negative_cases.py PROOF: test -->
- [x] `RPG-STRAT-074` `test_strategic_pivot_on_regional_danger`: pivot on regional danger <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-019` `test_region_fatigue_biasing`: region fatigue biasing <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-048` `test_region_consequence_record`: region consequence record <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-020` `test_conquered_region_triggers_stronghold`: conquered region -> stronghold consequence <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-STRAT-075` `test_strategic_pipeline_home_threat`: home threat in strategic pipeline <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-WORLD-021` `test_world_consequence_*`: world consequence interpretation coverage where applicable <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

---

## I. Death / permadeath / succession / heirlooms / nemesis

Relevant original source/test evidence:

- lifecycle / death / social-consequence logic in `all_src.py`
- related tests in `all_test.py`

- [x] `RPG-PROG-032` `test_aging_and_death`: aging and death <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-033` `test_hero_lifecycle_system_permadeath`: hero permadeath <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-034` `test_permadeath_succession_and_heirlooms`: succession and heirlooms
- [x] `RPG-COMBAT-097` `test_hero_death_creates_scar`: death scar consequences <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-098` `test_near_death_triggers_survival_consequences`: near-death survival consequences <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-099` `test_near_death_hardening`: near-death hardening <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-SOC-040` `test_nemesis_recognition_and_fear_bias`: nemesis recognition and fear bias <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-STRAT-076` `test_nemesis_milestone_creation`: nemesis milestone creation
- [x] `RPG-SOC-041` `test_locational_memory_on_death`: locational memory on death <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-SOC-042` `test_influence_shifts_on_monster_death`: influence shift on monster death <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-SOC-043` `test_influence_shifts_on_hero_death`: influence shift on hero death <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

---

## J. Medical / diagnosis judgment logic

Relevant original source/test evidence:

- diagnosis logic in `all_src.py`
- related tests in `all_test.py`

- [ ] `RPG-MED-001` `test_accurate_diagnosis_high_wisdom`: accurate diagnosis at high wisdom
- [ ] `RPG-MED-002` `test_misdiagnosis_low_wisdom`: misdiagnosis at low wisdom

# Legacy `src` RPG-Core Checklist — Part 7 (Residual Test-Covered Logic)

This checklist is additive to Parts 1–6.

It exists to capture smaller but still real legacy logic families that are explicitly covered by tests and are easy to lose if they remain implicit under broad labels like strategy, progression, or world behavior.

This part should stay test-first. If a behavior is listed here, it should have an identifiable test anchor in the original legacy test surface.

---

## A. Quest lifecycle, generation, and completion logic

Relevant legacy test surface includes quest creation, progression, duplicate suppression, completion, rewards, and quest-type-specific behavior.

- [x] `RPG-STRAT-077` `test_quest_creation`: quest creation baseline <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-078` `test_quest_advance`: quest progression increments correctly <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [ ] `RPG-STRAT-079` `test_quest_advance_does_nothing_when_completed`: completed quests do not advance further
- [ ] `RPG-STRAT-080` `test_quest_progress_ratio`: progress-ratio computation is correct
- [x] `RPG-STRAT-081` `test_generate_quest_returns_quest`: quest generator returns valid quest object <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-PROG-035` `test_generate_quest_respects_level`: generated quests respect level banding <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-STRAT-082` `test_generate_quest_skips_duplicate`: duplicate quest generation is suppressed <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-083` `test_generate_quest_gold_scales_with_level`: quest gold reward scales with level <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-084` `test_generate_explore_quest`: explore-quest generation works <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-085` `test_hunt_quest_completion_awards_rewards`: hunt-quest completion awards rewards <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-086` `test_explore_quest_completes_near_target`: explore-quest completes near target <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-087` `test_gather_quest_advance`: gather-quest progression works <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-088` `test_dynamic_liberate_quest`: liberate-quest generation/progression works <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-089` `test_territory_conquest`: territory-conquest quest/world objective behavior is preserved <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->

---

## B. Trait system logic

Relevant legacy test surface includes trait definitions, trait assignment, trait aggregation, compatibility, and serialization.

- [x] `RPG-PROG-036` `test_trait_serialization`: trait serialization is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-037` `test_get_traits`: trait retrieval works <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-038` `test_trait_defs_not_empty`: trait definitions exist and are non-empty <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-039` `test_with_traits_assigns_traits`: explicit trait assignment works <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-040` `test_no_traits_by_default`: no-trait default behavior is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-041` `test_traits_with_different_race_prefix`: race-prefixed trait handling is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-042` `test_empty_traits_returns_zero_bonus`: empty-trait bonus behavior is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-043` `test_single_known_trait`: single-trait bonus behavior is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-044` `test_multiple_traits_sum`: multiple traits stack/sum correctly <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-PROG-045` `test_unknown_trait_id_ignored`: unknown traits are ignored safely
- [x] `RPG-PROG-046` `test_same_trait_compatible`: trait compatibility logic is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-047` `test_assigns_between_2_and_4_traits`: random/default trait assignment count is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-048` `test_all_assigned_traits_are_valid`: assigned traits are always valid
- [x] `RPG-PROG-049` `test_all_trait_types_have_definitions`: all trait types have definitions <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-050` `test_trait_defs_have_all_utility_fields`: trait utility fields are complete <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-051` `test_trait_defs_have_all_stat_fields`: trait stat fields are complete <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

---

## C. Role derivation and role-aware behavior

Relevant legacy test surface includes role derivation, role transition, role biasing, and tactical role-awareness.

- [ ] `RPG-STRAT-090` `test_initial_role_derivation`: initial role derivation is preserved
- [ ] `RPG-STRAT-091` `test_dynamic_role_transition_with_hysteresis`: dynamic role transition with hysteresis is preserved
- [ ] `RPG-STRAT-092` `test_role_bias_influence`: role bias affects decisions as expected
- [ ] `RPG-COMBAT-100` `test_role_aware_tactical_biases`: tactical behavior reflects role-aware biasing

---

## D. Aptitudes, training-detail law, and stat recomputation

Relevant legacy test surface includes aptitude-driven training, soft caps, fractional accumulation, and recomputation of derived stats.

- [x] `RPG-PROG-052` `test_training_uses_aptitudes`: aptitude-weighted training law is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-053` `test_innate_talents_training`: innate talents affect training as expected <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-054` `test_training_does_not_exceed_cap`: training respects hard caps <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-055` `test_training_accumulates_fractionally`: fractional training accumulation is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-056` `test_training_updates_stats_on_increment`: stat update on training increment is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-057` `test_specialized_training_soft_caps`: soft-cap behavior for specialized training is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-058` `test_output_derived_stat_ceilings`: derived-stat ceiling logic is preserved
- [ ] `RPG-PROG-059` `test_stat_recalculation`: stat recomputation behavior is preserved
- [x] `RPG-PROG-060` `test_attribute_scaling_overlap`: overlapping attribute-scaling law is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

---

## E. Place attachment, home, and anchored behavior

Relevant legacy test surface includes place attachment, home behavior, home storage, retreat-to-home behavior, and home-driven actions.

- [ ] `RPG-WORLD-022` `test_place_attachment_instantiation`: place attachment can be instantiated
- [x] `RPG-WORLD-023` `test_place_attachment_navigation`: place attachment influences navigation correctly <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-024` `test_place_attachment_home_navigation`: home-oriented navigation behavior is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-WORLD-025` `test_no_home_returns_false`: no-home logic is preserved
- [x] `RPG-WORLD-026` `test_home_sets_home_pos`: home position assignment is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-DATA-049` `test_entity_copy_includes_home_storage`: home storage is preserved during copy <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-050` `test_entity_without_home_storage`: no-home-storage case is preserved <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [ ] `RPG-WORLD-027` `test_divergent_home_response`: divergent home response behavior is explicit and preserved where intended
- [x] `RPG-STRAT-093` `test_home_priority_retreat`: home-priority retreat behavior is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-PROG-061` `test_visit_home_upgrade_resolution`: visit-home upgrade resolution is preserved
- [x] `RPG-RES-045` `test_home_visit_leads_to_eating`: home visit can lead to eating behavior <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->

---

## F. Leash, camp, and local anchored ecology

Relevant legacy test surface includes leash behavior, chase abandonment, camp return, and camp reinforcement logic.

- [ ] `RPG-WORLD-028` `test_no_leash_returns_false`: no-leash detection behavior is preserved
- [x] `RPG-WORLD-029` `test_mob_beyond_leash_returns_to_camp`: beyond-leash return-to-camp behavior is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-030` `test_mob_within_leash_wanders_normally`: within-leash wandering behavior is preserved
- [ ] `RPG-WORLD-031` `test_no_leash_mob_wanders_freely`: leash-free wandering behavior is preserved
- [x] `RPG-STRAT-094` `test_chase_beyond_leash_abandons`: chase abandonment beyond leash is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-STRAT-095` `test_chase_within_leash_continues`: chase continuation within leash is preserved
- [ ] `RPG-STRAT-096` `test_no_leash_mob_hunts_freely`: no-leash hunting freedom is preserved
- [x] `RPG-WORLD-032` `test_camp_reinforcements`: camp reinforcement behavior is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

---

## G. Travel topology, path-affordance, and regional traversal law

Relevant legacy test surface includes flow fields, terrain costs, roads, bridges, biome affordances, and difficulty-zone traversal constraints.

- [x] `RPG-WORLD-033` `test_flow_field_basic_navigation`: basic flow-field navigation is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-034` `test_flow_field_respects_terrain_cost`: terrain-cost-sensitive navigation is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-WORLD-035` `test_flow_field_smoothing`: flow-field smoothing is preserved
- [ ] `RPG-WORLD-036` `test_flow_field_smoothing_normalization`: smoothing normalization behavior is preserved
- [ ] `RPG-WORLD-037` `test_navigation_uses_flow_field_for_far_town`: far-town navigation uses flow fields
- [ ] `RPG-WORLD-038` `test_navigation_uses_flow_field_for_world_boss`: world-boss navigation uses flow fields
- [ ] `RPG-WORLD-039` `test_road_cost_is_low`: road traversal cost law is preserved
- [ ] `RPG-WORLD-040` `test_prefers_road_over_swamp`: road preference over swamp is preserved
- [x] `RPG-WORLD-041` `test_each_biome_has_road_network`: biome road-network presence is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-042` `test_road_connects_locations`: road connectivity behavior is preserved
- [ ] `RPG-WORLD-043` `test_bridges_placed_over_water`: bridge placement over water is preserved
- [x] `RPG-WORLD-044` `test_all_four_biomes_have_features`: biome feature presence is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-045` `test_difficulty_sets_level_range`: region difficulty sets level range correctly <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-RES-046` `test_gold_scales_with_difficulty`: difficulty-linked gold scaling is preserved
- [x] `RPG-WORLD-046` `test_in_region_returns_difficulty`: region difficulty query logic is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-047` `test_difficulty_zones_defined`: difficulty-zone definition is preserved
- [ ] `RPG-WORLD-048` `test_lava_only_at_high_difficulty`: lava/high-difficulty coupling is preserved
- [x] `RPG-WORLD-049` `test_all_terrains_have_names`: terrain naming coverage is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-050` `test_all_terrains_have_race_labels`: terrain race-label coverage is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

---

## H. Cooperation, recruitment-adjacent coordination, and proximity bonding

Relevant legacy test surface includes small cooperative and bonding behaviors that affect social or local-world outcomes.

- [x] `RPG-SOC-044` `test_cooperation_recruitment_logic`: cooperation in recruitment/social choice is preserved <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-045` `test_scenario_3_stationary_world_proximity_bonding`: proximity bonding behavior is preserved <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

---

## I. Residual small-world and economy-adjacent local realism

Relevant legacy test surface includes local inventory and burden realism that can affect action outcomes.

- [x] `RPG-RES-047` `test_full_bag_aborts_looting`: full-bag looting abort is preserved <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-048` `test_overweight_aborts_looting`: overweight looting abort is preserved <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-049` `test_near_weight_limit_penalizes_loot`: near-limit loot penalty is preserved <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

These are listed again here intentionally if not already fully owned elsewhere, because they are small and easy to lose.

---

## J. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map residual logic into roadmap phases:

- [ ] Phase 8 owns:
  - leash/camp/local anchored ecology
  - local burden/loot-abort realism
  - local/path-affordance pieces only where they directly affect immediate tactics

- [ ] Phase 9 owns:
  - quests
  - traits
  - roles
  - aptitude/training-detail law
  - place attachment/home behavior when it affects long-horizon choices
  - regional traversal/topology when it affects world-scale intention
  - cooperation/proximity bonding

- [x] No Part 7 item should be left implicit under a generic bucket like “AI improvements” or “progression tuning` <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

---

## Completion rule for Part 7

A Part 7 item is not considered covered merely because it “probably exists” inside a broader subsystem.

Each item should be considered closed only when:

- [ ] the specific legacy behavior has a clear roadmap owner
- [ ] the specific behavior has a direct implementation or explicit divergence decision
- [ ] the specific behavior has test coverage or parity justification
- [ ] the replacement ledger/support boundary reflects the truth of that item

# Legacy `src` Assumption / Invariant Checklist — Part 8

This checklist is additive to Parts 1–7.

It is not a new gameplay-logic trunk.
It exists to capture **legacy assumptions and invariants** that the old system was supposed to have and that are explicitly enforced by tests.

These are the kinds of rules that often get broken during migration because they are treated as “small details,” even though they are foundational to trustworthiness.

This part should remain **test-first**.

---

## A. Default-state and neutral-behavior assumptions

These tests assert what objects or systems are supposed to look like before gameplay meaning starts.

- [ ] `RPG-DATA-051` `test_default_values`: default entity/build values are preserved
- [ ] `RPG-DATA-052` `test_default_values_all_zero`: default zero-valued state is preserved
- [ ] `RPG-DATA-053` `test_default_multiplicative_values_are_1`: default multiplicative modifiers equal 1
- [ ] `RPG-DATA-054` `test_default_additive_values_are_0`: default additive modifiers equal 0
- [ ] `RPG-DATA-055` `test_default_metadata_is_none`: metadata defaults to `None`
- [ ] `RPG-DATA-056` `test_none_metadata_preserved`: `None` metadata remains preserved
- [ ] `RPG-DATA-057` `test_schema_none_metadata`: schema handles `None` metadata correctly
- [ ] `RPG-PROG-062` `test_no_skills_by_default`: entities have no skills by default
- [x] `RPG-RES-050` `test_no_inventory_by_default`: entities have no inventory by default <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-PROG-063` `test_no_traits_by_default`: entities have no traits by default
- [ ] `RPG-STRAT-097` `test_entity_starts_with_no_quests`: entities start with no quests
- [ ] `RPG-INFRA-073` `test_default_core_rate_is_1`: default core subsystem rate is preserved
- [ ] `RPG-INFRA-074` `test_default_environment_rate_is_2`: default environment subsystem rate is preserved
- [ ] `RPG-INFRA-075` `test_default_economy_rate_is_5`: default economy subsystem rate is preserved
- [x] `RPG-WORLD-051` `test_default_region_id`: default region identifier is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-DATA-058` `test_default_empty`: default empty collection/container semantics are preserved
- [ ] `RPG-WORLD-052` `test_empty_zones_returns_1`: empty-zone fallback behavior is preserved
- [x] `RPG-WORLD-053` `test_empty_regions_returns_none`: empty-region lookup returns `None` <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-DATA-059` `test_select_returns_none_on_empty`: selection on empty inputs returns `None`
- [ ] `RPG-STRAT-098` `test_export_empty_strategy`: exporting empty strategy state is safe

---

## B. No-op, empty-tick, and “does nothing safely” assumptions

These tests assert that when there is nothing to do, the system degrades safely and predictably.

- [ ] `RPG-INFRA-076` `test_no_changes_skipped`: no-change updates are skipped safely
- [ ] `RPG-COMBAT-101` `test_effects_tick_on_empty_tick`: effects still tick on empty ticks
- [x] `RPG-RES-051` `test_stamina_regens_on_empty_tick`: stamina regen still occurs on empty ticks <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-102` `test_skill_cooldowns_tick_on_empty_tick`: skill cooldowns still tick on empty ticks <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-STRAT-099` `test_quest_advance_does_nothing_when_completed`: completed quests ignore further advance calls
- [ ] `RPG-INFRA-077` `test_unknown_action_does_nothing`: unknown actions are safely ignored
- [x] `RPG-COMBAT-103` `test_full_hp_no_change`: full-HP state remains unchanged <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-054` `test_no_region_no_penalty`: no-region case applies no penalty <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-055` `test_safe_region_no_penalty`: safe-region case applies no penalty <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-056` `test_unknown_region_returns_0`: unknown region uses zero/fallback difficulty <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-057` `test_no_region_returns_0`: no-region difficulty fallback is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

---

## C. Copy, clone, preservation, and ownership assumptions

These tests assert what is supposed to be preserved across copying and what must not be shared.

- [x] `RPG-STRAT-100` `test_quest_copy`: quest copy preserves quest state <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-DATA-060` `test_entity_copy_preserves_quests`: entity copy preserves quests <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-DATA-061` `test_entity_copy_preserves_attributes`: entity copy preserves attributes <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-DATA-062` `test_entity_copy_preserves_skills`: entity copy preserves skills <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-DATA-063` `test_entity_copy_includes_home_storage`: entity copy preserves home storage <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-064` `test_entity_without_home_storage`: no-home-storage case remains safe <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-WORLD-058` `test_region_copy`: region copy semantics are preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-065` `test_attributes_copy`: attribute copy semantics are preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-DATA-066` `test_copy`: generic model copy semantics are preserved wherever tested <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-WORLD-059` `test_grid_copy_is_not_shared`: copied grids are not aliased
- [x] `RPG-DATA-067` `test_entity_copy_shallow_vs_refs`: copy/ref-sharing behavior is explicit and preserved <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-DATA-068` `test_latest_preserves_metadata`: latest-version object preserves metadata

---

## D. Serialization, schema, and round-trip assumptions

These tests assert that important models are supposed to serialize safely and consistently.

- [ ] `RPG-DATA-069` `test_serialization_round_trip`: serialization round-trip is preserved
- [ ] `RPG-DATA-070` `test_item_serialization`: item serialization is preserved
- [ ] `RPG-DATA-071` `test_enchanted_blade_serialization`: enchanted item serialization is preserved
- [x] `RPG-PROG-064` `test_skill_serialization`: skill serialization is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-065` `test_passive_skill_serialization`: passive skill serialization is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-066` `test_class_serialization`: class serialization is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-067` `test_breakthrough_serialization`: breakthrough serialization is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-068` `test_trait_serialization`: trait serialization is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-DATA-072` `test_history_registry_serialization`: history registry serialization is preserved
- [ ] `RPG-DATA-073` `test_entity_to_full_schema_no_crash`: full schema export does not crash
- [ ] `RPG-DATA-074` `test_serialization_pydantic_model`: pydantic serialization assumption is preserved
- [x] `RPG-DATA-075` `test_serialization_frozen_model_with_proxy`: frozen/proxy serialization is preserved <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-DATA-076` `test_inspection_serialization`: inspection serialization is preserved
- [x] `RPG-DATA-077` `test_cognition_api_serialization`: cognition API serialization is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

---

## E. Freeze, immutability, and deep-isolation assumptions

These tests assert that certain state surfaces are supposed to be frozen, safe, and non-mutating.

- [x] `RPG-DATA-078` `test_entity_deep_copy_isolation`: deep-copy isolation is preserved <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-DATA-079` `test_deep_freeze_nested_collections`: deep freeze handles nested collections
- [x] `RPG-DATA-080` `test_deep_freeze_idempotency`: deep freeze is idempotent <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-DATA-081` `test_freeze_calls_validate`: freeze triggers validation correctly
- [ ] `RPG-DATA-082` `test_nested_freeze_invariants`: nested freeze invariants are preserved
- [x] `RPG-WORLD-060` `test_world_state_freeze_guards`: world-state freeze guards are preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-DATA-083` `test_simulation_model_collection_freeze_list`: list freezing behavior is preserved
- [ ] `RPG-DATA-084` `test_simulation_model_collection_freeze_dict`: dict freezing behavior is preserved
- [ ] `RPG-DATA-085` `test_vector2_coercion_during_freeze`: vector coercion during freeze is preserved
- [ ] `RPG-DATA-086` `test_non_mutation`: non-mutation guarantee is preserved
- [x] `RPG-STRAT-101` `test_build_profile_does_not_mutate_caps`: cognition-profile derivation is non-mutating <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-STRAT-102` `test_build_profile_returns_new_profile_object_each_call`: fresh profile object guarantee is preserved

---

## F. Determinism and repeatability assumptions

These tests assert that the system is supposed to be repeatable under the same conditions.

- [x] `RPG-STRAT-103` `test_profile_derivation_is_deterministic_for_same_entity_state`: deterministic profile derivation <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-STRAT-104` `test_intel_capacity_determinism`: intelligence-capacity determinism is preserved <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-105` `test_strategic_replay_graph_equality`: replay graph equality is preserved <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-078` `test_same_seed_same_result`: same-seed world/result determinism is preserved <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-INFRA-079` `test_harness_non_determinism_different_seed`: different-seed divergence remains explicit <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-080` `test_first_by_id_wins_same_tile`: deterministic same-tile tie-breaking is preserved <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-081` `test_diagonal_same_target_one_wins`: deterministic same-target conflict resolution is preserved <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-WORLD-061` `test_non_conflicting_moves_both_succeed`: independent valid moves both survive
- [x] `RPG-INFRA-082` `test_equidistant_returns_first`: deterministic first-choice behavior on ties is preserved <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

---

## G. Registry, definition, and data-completeness assumptions

These tests assert that key registries and definition maps are supposed to exist and be complete.

- [ ] `RPG-RES-052` `test_item_registry_not_empty`: item registry is non-empty
- [x] `RPG-PROG-069` `test_skill_defs_not_empty`: skill definitions are non-empty <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-070` `test_trait_defs_not_empty`: trait definitions are non-empty <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-DATA-087` `test_registry_not_empty`: generic registry non-empty guarantee is preserved
- [x] `RPG-PROG-071` `test_skill_registry_not_empty`: skill registry is non-empty <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-072` `test_all_trait_types_have_definitions`: all trait types have definitions <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-DATA-088` `test_all_tiers_defined`: all expected tier sets are defined
- [ ] `RPG-DATA-089` `test_tier1_empty`: tier-1 empty expectation is preserved where applicable
- [ ] `RPG-DATA-090` `test_tier4_defined`: tier-4 definition exists where expected
- [x] `RPG-PROG-073` `test_all_base_classes_defined`: base class definitions exist <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-074` `test_breakthroughs_defined`: breakthrough definitions exist <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-DATA-091` `test_all_types_have_name_templates`: type name-template completeness is preserved
- [ ] `RPG-WORLD-062` `test_all_terrains_have_names`: all terrains have names
- [ ] `RPG-WORLD-063` `test_all_terrains_have_race_labels`: all terrains have race labels
- [ ] `RPG-WORLD-064` `test_all_four_biomes_have_features`: all biomes expose expected features
- [ ] `RPG-WORLD-065` `test_all_regions_have_territory`: all regions have territory assignment
- [ ] `RPG-WORLD-066` `test_difficulty_zones_defined`: difficulty zones are defined
- [x] `RPG-RES-053` `test_loot_tables_exist`: loot tables exist <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

---

## H. Safe fallback and degraded-mode assumptions

These tests assert that when something is missing, disabled, or unsupported, the system is supposed to fail soft or fall back safely.

- [x] `RPG-STRAT-106` `test_detour_depth_limit_fallback`: detour depth fallback is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-INFRA-083` `test_worker_pool_fallback_to_inline`: worker pool falls back to inline execution
- [ ] `RPG-INFRA-084` `test_rabbitmq_disabled_no_crash`: RabbitMQ-disabled mode does not crash
- [ ] `RPG-INFRA-085` `test_kafka_disabled_no_crash`: Kafka-disabled mode does not crash
- [ ] `RPG-INFRA-086` `test_redis_disabled_no_crash`: Redis-disabled mode does not crash
- [x] `RPG-CLI-001` `test_headless_runner_importable_without_brokers`: headless runner imports safely without brokers <!-- SOURCE: src/cli/entry.py TEST: tests/cli/test_entry_parity.py PROOF: integration -->
- [ ] `RPG-CLI-002` `test_action_system_importable_without_brokers`: action system imports safely without brokers
- [ ] `RPG-INFRA-087` `test_simulation_step_runs_without_brokers`: simulation can step without brokers
- [ ] `RPG-CLI-003` `test_regression_runner_survives_no_infrastructure`: regression runner survives no-infrastructure mode
- [x] `RPG-PROG-075` `test_get_unknown`: unknown registry/class lookup is handled safely <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-076` `test_unknown_trait_id_ignored`: unknown trait IDs are ignored safely <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-104` `test_unknown_type_falls_back_to_physical`: unknown damage/action type falls back safely <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

---

## I. Caps, clamps, floors, ceilings, and boundedness assumptions

These tests assert what is supposed to happen at boundaries.

- [x] `RPG-COMBAT-105` `test_hp_clamped_after_recalc`: HP is clamped after recomputation <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-077` `test_stamina_cannot_go_below_zero`: stamina lower bound is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-078` `test_stamina_regen_capped`: stamina regeneration upper cap is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-079` `test_training_does_not_exceed_cap`: training hard caps are preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-080` `test_level_up_respects_cap`: level-up cap compliance is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-081` `test_boss_diff_capped_at_4`: boss difficulty cap is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-082` `test_specialized_training_soft_caps`: soft-cap law is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-083` `test_output_derived_stat_ceilings`: derived-stat ceilings are preserved
- [x] `RPG-PROG-084` `test_physical_no_attributes_defaults_mult_to_1`: missing-attribute multiplier defaults are preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-085` `test_magical_no_attributes_defaults_mult_to_1`: magical default multiplier law is preserved
- [ ] `RPG-RES-054` `test_full_bag_returns_zero`: full-bag score/utility floor is preserved
- [x] `RPG-RES-055` `test_overweight_loot_score_zero`: overweight loot utility floor is preserved <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

---

## J. Precedence, selection, and ordering assumptions

These tests assert what the system is supposed to prefer when multiple valid candidates exist.

- [x] `RPG-STRAT-107` `test_objective_derivation_precedence_active_objective_if_no_blocker`: active-objective precedence is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-STRAT-108` `test_objective_derivation_precedence_first_unresolved_if_no_active`: unresolved-first precedence is preserved
- [x] `RPG-STRAT-109` `test_reserved_current_project_slot_is_used_when_current_project_exists`: current-project reserved slot law is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-WORLD-067` `test_next_step_returns_first_tile`: first-step path semantics are preserved
- [ ] `RPG-WORLD-068` `test_returns_nearest`: nearest-target selection is preserved
- [ ] `RPG-INFRA-088` `test_equidistant_returns_first`: stable first-on-tie semantics are preserved
- [x] `RPG-PROG-086` `test_best_ready_skill_returns_highest_power`: best-ready-skill precedence is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-106` `test_best_ready_skill_skips_on_cooldown`: cooldown exclusion precedence is preserved <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-087` `test_best_ready_skill_skips_insufficient_stamina`: stamina exclusion precedence is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-088` `test_best_ready_skill_none_when_no_skills`: no-skill fallback is preserved <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

---

## K. Guardrail and authorization assumptions

These tests assert that the system is supposed to prevent or reject things in specific safe ways.

- [ ] `RPG-INFRA-089` `test_phase_guard_read_unauthorized`: unauthorized phase read is guarded
- [x] `RPG-WORLD-069` `test_no_path_through_walls`: pathfinding guardrail against walls is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-WORLD-070` `test_next_step_no_path`: no-path fallback is preserved
- [x] `RPG-WORLD-071` `test_safe_shot_detection`: safe-shot guard logic is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-107` `test_no_flanking_bonus_when_facing_attacker`: flanking exclusion guardrail is preserved <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-COMBAT-108` `test_no_opportunity_attack_when_moving_toward`: OA guardrail is preserved
- [x] `RPG-COMBAT-109` `test_no_cover_on_open_ground`: cover absence on open ground is preserved <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-089` `test_non_equipment_ignored`: non-equipment inputs are ignored safely <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-090` `test_cannot_breakthrough_no_class`: breakthrough precondition guard is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-PROG-091` `test_no_class`: no-class guard behavior is preserved <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

---

## L. Metadata, inspection, and smoke-stability assumptions

These tests assert that inspection and debug-facing surfaces are supposed to remain safe even in empty or corrupted cases.

- [x] `RPG-API-020` `test_inspector_smoke_empty_state`: empty-state inspector safety is preserved <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-API-021` `test_inspector_smoke_corrupted_state`: corrupted-state inspector safety is preserved <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-API-022` `test_inspector_smoke_maximal_state`: maximal-state inspector safety is preserved <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-STRAT-110` `test_render_strategic_domain_empty`: empty strategic-domain rendering is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-111` `test_empty_strategic_state_rendering`: empty strategic rendering is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-112` `test_cognition_inspector_rendering`: cognition inspector rendering is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-113` `test_cognition_empty_profile`: empty cognition-profile rendering is preserved <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

---

## M. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map assumption logic to roadmap owners rather than creating another giant roadmap phase.

- [ ] Phase 7 owns:
  - serialization / freeze / deep-isolation / determinism / phase guards / non-mutation assumptions

- [ ] Phase 8 owns:
  - immediate-action guardrails
  - local boundedness and combat/tactical caps/clamps
  - local selection/tie-breaking assumptions where action resolution depends on them

- [ ] Phase 9 owns:
  - precedence and boundedness assumptions in cognition/strategy/progression
  - traits / registries / progression caps where they materially shape long-horizon gameplay

- [ ] Phase 10 owns:
  - disabled-mode / fallback / importability / infra-safe assumptions
  - consumer/entry black-box degraded-mode assumptions

- [ ] Phase 11+ owns:
  - governance truth for any surviving invariant classified as preserved/divergent/unsupported

---

## Completion rule for Part 8

A Part 8 item is not closed merely because the system “seems to behave sensibly.”

Each item should be considered closed only when:

- [ ] the specific assumption has a clear roadmap owner
- [ ] the specific assumption has direct implementation or an explicit divergence/unsupported decision
- [ ] the specific assumption has test coverage or proof justification
- [ ] the support boundary and replacement ledger reflect its true status

# Missing / under-specified checklist additions

## 1. Goal registry and goal scorer contract

The checklist mentions goal modifiers, but it does not fully preserve the core goal registry/scorer law from legacy tests.

Add these atomic items:

- [ ] `RPG-STRAT-114` Goal registry contains the expected built-in goals.
- [ ] `RPG-STRAT-115` Goal registry names are unique.
- [ ] `RPG-STRAT-116` Every built-in goal maps to a valid target AI state.
- [x] `RPG-COMBAT-110` Combat goal scores high when hostile enemies are visible. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-111` Flee goal scores high below HP threshold. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-STRAT-117` Explore goal has a stable baseline score.
- [ ] `RPG-STRAT-118` Empty goal candidate list returns `None`.
- [x] `RPG-INFRA-090` RNG value `0.0` selects the highest candidate. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-STRAT-119` `top_n` selection limits candidates before weighted selection.
- [x] `RPG-STRAT-120` Neuroticism can break goal commitment lock under low HP pressure. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-STRAT-121` Legacy `goal_evaluator.py` shim behavior is preserved or intentionally removed.
- [x] `RPG-RES-056` Loot goal returns zero when bag is full. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-057` Trade goal receives urgency when inventory is nearly full or overweight. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

Why this matters: goal scoring is the bridge between cognition and action. If this drifts, V2 entities may have the same systems but completely different behavior.

---

## 2. EntityBuilder construction law

The checklist mentions entity aspects and spawning, but not the builder as an atomic compatibility surface. Legacy has a large fluent `EntityBuilder` contract: default identity, faction, AI state, stats, class attributes, race skills, class skills, inventory, home storage, traits, clique, household, leash, world role, and randomized spawn stats.

Add:

- [x] `RPG-COMBAT-112` EntityBuilder default entity has stable kind, faction, alive combat state, and wander AI state. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-DATA-092` `.kind()`, `.at()`, `.home()`, `.ai_state()`, `.faction()`, `.tier()` preserve exact field effects. <!-- SOURCE: src/core/builder.py TEST: tests/engine/test_local_executor.py PROOF: unit -->
- [x] `RPG-PROG-092` Hero kind enforces minimum stamina behavior. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-113` Base stats initialize combat and progression fields consistently. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-072` Randomized stats use deterministic spawn-domain RNG. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-PROG-093` Hero class derives attributes and caps from class definition. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-WORLD-073` Mob attributes scale by tier.
- [x] `RPG-PROG-094` Race attributes apply racial modifiers and deterministic variance. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-PROG-095` Race skills and class skills can be combined without loss. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-096` No-skills-by-default behavior is preserved.
- [x] `RPG-WORLD-074` Builder supports clique, household, home building, world role, and leash fields. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-093` Builder-created entities deep-copy safely. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->

This is not “just construction.” It is the source of initial state truth.

---

## 3. Registry and data-driven loading law

The checklist mentions registries generally, but it should explicitly preserve the data-driven runtime contract.

Add:

- [x] `RPG-DATA-094` `load_all_registries()` loads items, classes, skills, breakthroughs, traits, spawn configs, and loot configs. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-095` Spawn config entries actually initialize generated entities. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-RES-058` Loot config entries are loaded and used by `EntityGenerator`. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-DATA-096` Item registry lookup returns expected item type and bonuses.
- [x] `RPG-PROG-097` Class definitions contain class skill lists. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-098` Every class skill ID resolves in the skill registry. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-DATA-097` Missing registry entries fail safely, not silently.
- [x] `RPG-DATA-098` Registry loading is deterministic and idempotent. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-DATA-099` Duplicate or malformed data definitions are rejected or explicitly handled.

This is a big blind spot. A V2 port can pass behavior tests with hardcoded objects while silently breaking data-driven gameplay.

---

## 4. Quest lifecycle and generation

The checklist has quest mentions, but it is not atomic enough for the original quest tests.

Add:

- [x] `RPG-STRAT-122` Quest starts with progress `0`, not completed. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-123` Quest progress ratio is correct. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-124` Quest `advance()` returns `True` only on first completion. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-125` Advancing an already completed quest does not mutate state. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-DATA-100` Quest copy is deep enough that copied progress mutation does not affect original. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-DATA-101` Quest serialization omits position for non-position quests. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-DATA-102` Explore quest serialization includes target position. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-126` Quest generation respects hero level. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-127` Quest generation skips duplicates. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-128` Quest rewards scale with level. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-129` Explore quest generation produces valid target positions. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [ ] `RPG-DATA-103` Template map and template list stay consistent.
- [x] `RPG-STRAT-130` Entity quest list starts empty. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-131` Entity copies preserve quest progress independently. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-132` Hunt quest completion grants gold and XP. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-133` Explore quest completes within target proximity. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-134` Gather quest can advance by count. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-STRAT-135` Max active quest limit is enforced. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->

Do not treat “dynamic quests exist” as enough. The old code had model, generator, tracking, reward, and serialization rules.

---

## 5. Equipment enhancement, home storage, shops, treasure chests

This is clearly underrepresented. The checklist mentions progression/classes/items, but not several old mechanics.

Add:

- [x] `RPG-PROG-099` `recalc_derived_stats()` creation mode applies attribute bonuses. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-100` `recalc_derived_stats()` delta mode removes old bonuses before applying new ones.
- [x] `RPG-COMBAT-114` HP clamps to new max HP after stat recalculation. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-RES-059` Noncombat derived stats update vision, HP regen, trade bonus, and loot bonus. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-RES-060` `auto_equip_best()` equips into empty slot.
- [x] `RPG-RES-061` Better equipment replaces worse equipment and returns old item to inventory. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-PROG-101` Worse equipment is not auto-equipped. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-102` Non-equipment items are ignored by auto-equip. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-RES-062` Unknown item power returns zero.
- [ ] `RPG-RES-063` Stronger item power ordering is stable.
- [x] `RPG-RES-064` Home storage add/remove/full/copy behavior is preserved. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-065` Shop contains expanded item set. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [ ] `RPG-RES-066` Buff potion item types are consumable.
- [x] `RPG-PROG-103` Skill learning respects level, prerequisites, and mastery. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-104` All hero classes expose at least one available skill chain. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-RES-067` Treasure chests start available.
- [x] `RPG-RES-068` Chest loot sets respawn tick and unavailable state. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-069` Chest respawns only at or after respawn tick. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-070` Chest loot tables exist for expected tiers. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-104` Entity copy preserves home storage deeply. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-PROG-105` Training that increments an attribute immediately recomputes derived stats. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

This entire area is easy to lose because it sits between inventory, progression, and world objects.

---

## 6. Ranged combat, line-of-sight, cover, and range-aware skills

The existing checklist has ranged legality, but it needs finer atomic rules.

Add:

- [x] `RPG-COMBAT-115` Melee weapons default to range `1`. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-COMBAT-116` Shortbow and longbow have distinct weapon ranges.
- [ ] `RPG-WORLD-075` Clear horizontal line of sight passes.
- [ ] `RPG-WORLD-076` Clear diagonal line of sight passes.
- [x] `RPG-WORLD-077` Wall between attacker and target blocks LOS. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-078` Wall on diagonal path blocks LOS. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-WORLD-079` Adjacent tiles are always visible under legacy rule.
- [x] `RPG-WORLD-080` Wall at endpoint does not block LOS. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-081` Wall at start does not block LOS. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-117` Adjacent wall counts as cover. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-118` Open ground gives no cover. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-119` Melee attack adjacent is valid. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-120` Melee attack out of range is invalid. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-121` Ranged attack at valid distance is valid. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-122` Unarmed entity range is `1`. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-123` Ranged skill can be selected at distance. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-124` Melee skill is not selected at ranged distance. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-106` Starting gear gives warrior sword and ranger bow. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->

The checklist currently risks collapsing this into “range and LOS exist.” That is not enough.

---

## 7. A\* pathfinding details

The checklist mentions movement and pathfinding, but several pathfinding laws are missing or buried.

Add:

- [ ] `RPG-WORLD-082` Straight-line path returns expected step count.
- [ ] `RPG-WORLD-083` Same start and goal returns empty path.
- [ ] `RPG-WORLD-084` Adjacent goal returns single-step path.
- [ ] `RPG-WORLD-085` Path routes around walls.
- [ ] `RPG-WORLD-086` Fully enclosed goal returns no path.
- [ ] `RPG-WORLD-087` Unwalkable goal returns no path.
- [x] `RPG-WORLD-088` Returned path excludes start position. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-INFRA-091` Max-node budget can terminate search with no path. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-WORLD-089` `next_step()` returns first path tile.
- [ ] `RPG-WORLD-090` Occupied tiles are avoided.
- [ ] `RPG-WORLD-091` Goal tile can remain reachable even if listed as occupied.
- [ ] `RPG-WORLD-092` Road cost is lower than floor.
- [ ] `RPG-WORLD-093` Swamp cost is higher than floor.
- [x] `RPG-WORLD-094` Terrain cost registry is used by pathfinding. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-095` Long-distance movement uses A\*. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-096` Short-distance movement can use greedy fallback. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

That last distinction matters: A\* and greedy fallback are different behavior contracts, not implementation details.

---

## 8. Mob leash, chase give-up, and return-to-camp

The checklist has leash references, but the atomic old behavior needs to be explicit.

Add:

- [ ] `RPG-WORLD-097` Entity with `leash_radius=0` is never beyond leash.
- [x] `RPG-WORLD-098` Entity with no home position is never beyond leash. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-WORLD-099` Distance within leash returns false.
- [ ] `RPG-WORLD-100` Distance beyond leash returns true.
- [x] `RPG-COMBAT-125` Leash multiplier extends allowed chase range. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-101` Wander handler sends beyond-leash mob to return-to-camp. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [ ] `RPG-WORLD-102` Within-leash mob continues wandering.
- [ ] `RPG-WORLD-103` No-leash mob wanders freely.
- [ ] `RPG-COMBAT-126` Hunt handler abandons chase beyond `1.5x` leash.
- [ ] `RPG-COMBAT-127` Hunt handler continues chase inside `1.5x` leash.
- [ ] `RPG-COMBAT-128` Hunt handler gives up after chase timeout.
- [x] `RPG-COMBAT-129` Chase ticks reset on combat engagement. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-104` Return-to-camp heals while returning. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-105` Returning mob resumes normal behavior after reaching camp. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

This is not just movement. It prevents mobs from becoming global homing missiles.

---

## 9. Group coordination and contract-party formation

The social checklist is broad, but group mechanics are under-specified.

Add:

- [x] `RPG-SOC-046` Entities with the same `cluster_id` and faction can form a group. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-047` Group requires at least two living members. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-048` Group leader is selected by highest level. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-049` Group anchor follows leader position. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-SOC-050` Members receive group ID linkage. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-051` Group dissolves if leader dies. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-052` Group removes dead members. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-053` Group dissolves if membership drops below two. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-054` Group cohesion decreases with distance from leader. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-055` Shared group goal biases member goal scoring. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-056` Distance from leader increases social regrouping bias. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-057` Active social contracts can instantiate party groups. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-058` Contract kind maps to shared group goal. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-059` Contract party dissolution applies contract consequences. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

Without these, social “contracts” may exist as records but not as behavior.

---

## 10. Calamity / world-boss system

This is a real omission. The checklist mentions calamity evolution, but not the actual world-boss system.

Add:

- [x] `RPG-WORLD-106` World maturity increases on schedule. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-107` Calamity spawn obeys interval and forced-spawn ticks. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-108` Spawned calamity has world-boss identity and role. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-109` Calamity uses legendary stats. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-RES-071` Calamity receives legendary equipment/loot. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-136` Calamity spawn creates bounty quests for heroes. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-110` Calamity aura applies local debuffs. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-111` Camp reinforcements occur on schedule. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-112` Camp reinforcement level increases when camp is full. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-WORLD-113` Faction raids spawn on raid interval. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-114` Raid mobs use raid AI state. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-115` Raid mobs do not return home. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-116` Killing world boss grants fame. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-117` Killing world boss grants title. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-STRAT-137` Bounty completion rewards are applied.

This is not optional world flavor. It affects progression, quests, combat, world pressure, and hero identity.

---

## 11. Region and Voronoi topology

The checklist has world/regions, but not enough of the concrete topology contract.

Add:

- [x] `RPG-WORLD-118` Region contains uses Manhattan distance. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-DATA-105` Region copy deep-copies locations. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-119` Location model preserves type, position, and region ID. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-120` Difficulty tier chosen by distance zones. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-121` Boundary distances map to expected tier.
- [ ] `RPG-WORLD-122` Empty difficulty zones default safely.
- [x] `RPG-WORLD-123` Region name selection is deterministic by terrain counter. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-124` Resetting name counters restarts name sequence.
- [x] `RPG-WORLD-125` Every terrain has region names. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-126` Every terrain has race label. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-127` Difficulty multipliers exist for all tiers.
- [ ] `RPG-WORLD-128` Difficulty multipliers scale upward.
- [ ] `RPG-WORLD-129` All location types have name templates.
- [x] `RPG-WORLD-130` Expected POI types exist: camp, grove, ruins, dungeon, shrine, boss arena, outpost, watchtower, portal, fishing spot, graveyard, obelisk. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-131` Voronoi map coverage is near-total. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-132` Region terrain, overlays, details, and town tiles account for map tiles. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-133` Regions border each other.
- [x] `RPG-WORLD-134` Every region owns some territory. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-135` `find_region_at()` returns nearest region. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-136` Equidistant region lookup returns first region. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-137` Empty region list returns `None`. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-138` Single region always matches. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

This is a map-authority contract. If V2 changes it, spawning, difficulty, resource placement, and exploration all drift.

---

## 12. Platform primitives: RNG and spatial hash

The checklist mentions determinism, but not the primitive contracts.

Add:

- [x] `RPG-INFRA-092` Deterministic RNG repeats exactly for same seed/domain/entity/tick. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-093` RNG domain separation produces different streams for different domains. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-094` `next_int()` always respects inclusive bounds.
- [x] `RPG-WORLD-139` Spatial hash insert places entity in correct cell. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-140` Spatial hash radius query includes neighboring cells. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-141` Spatial hash move removes old cell membership and adds new cell membership. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-142` Spatial hash remove clears membership. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-143` Spatial hash behavior is deterministic independent of insertion order where required. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

These are low-level, but if they drift, every higher-level system becomes untrustworthy.

---

## 13. Phase guard and authoritative phase authorization

The checklist only has one unauthorized phase read item. Legacy tests cover more.

Add:

- [ ] `RPG-INFRA-095` Unauthorized phase read raises.
- [ ] `RPG-INFRA-096` Unauthorized phase mutation raises.
- [ ] `RPG-INFRA-097` Unauthorized phase emit raises.
- [ ] `RPG-INFRA-098` Authorized mutation succeeds only in permitted phase.
- [ ] `RPG-INFRA-099` Internal field access is controlled.
- [x] `RPG-COMBAT-130` Scheduling phase cannot mutate HP. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-INFRA-100` Persistence phase is read-only.
- [ ] `RPG-INFRA-101` Phase guard prevents bypassing authoritative action/update application.
- [ ] `RPG-INFRA-102` Nested phase access follows the same authorization law.

This is directly tied to V2’s “one authoritative mutation path” principle.

---

## 14. Behavior inspection and presenter truth

The checklist excludes UI-only presentation, which is fine. But some inspection/presenter behavior is not merely UI. It is behavioral explainability and debugging truth.

Add under an optional “inspection truth” section:

- [x] `RPG-API-023` AI presenter maps structured decision drivers. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-STRAT-138` Belief inspection includes apparent state. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-API-024` Injury blurring affects API-visible state consistently. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-PROG-107` Stat breakdown service matches real derived stat math. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-131` Combat trace recording is inspectable. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-STRAT-139` AI explainability persists across ticks.
- [ ] `RPG-INFRA-103` Scheduler timeline is inspectable.
- [ ] `RPG-API-025` Entity inspection behavior matches legacy.
- [ ] `RPG-STRAT-140` AI explanation parity is preserved or intentionally divergent.
- [ ] `RPG-INFRA-104` Missing continuity data is handled safely.
- [ ] `RPG-INFRA-105` Corrupted inspection state does not crash.

This should not be mixed with gameplay parity, but it should not disappear either. Debug surfaces are part of operational truth.

---

## 15. Assertion and test helper semantics

The checklist should preserve some internal validation helpers because they define what “consistent” means.

Add:

- [x] `RPG-STRAT-141` Strategic consistency assertion fails on real drift. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-142` Cognition consistency assertion fails when replay and graph diverge. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-143` Graph integrity assertion catches broken cognition graph structure. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-INFRA-106` Determinism assertion compares actual replay outputs, not superficial success. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-107` Overload behavior assertion preserves capacity failure semantics. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-COMBAT-132` Combat arena helper preserves default factions, hostility, tick running, and entity lookup semantics. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-133` Legacy stat helper preserves expected combat math inputs. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

This sounds like test infrastructure, but it encodes legacy truth. Removing it weakens the audit.

---

## 16. Brokerless, recovery, and degraded-mode behavior tied to execution

Some infra is outside RPG-core scope, but not all of it. If missing Kafka/RabbitMQ changes whether the simulation step can run, it belongs in the checklist.

Add:

- [ ] `RPG-INFRA-108` Simulation step runs when brokers are missing.
- [ ] `RPG-INFRA-109` RabbitMQ missing-package path fails closed or disables cleanly.
- [ ] `RPG-INFRA-110` Kafka missing-package path fails closed or disables cleanly.
- [ ] `RPG-INFRA-111` Engine manager recovery handles missing Kafka.
- [ ] `RPG-INFRA-112` Worker pool RabbitMQ dispatch contract is preserved if broker mode is supported.
- [ ] `RPG-INFRA-113` Kafka recovery can reconstruct from snapshot plus event stream.
- [x] `RPG-INFRA-114` Live-vs-manual replay produces same world state for loot recovery. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

This connects directly to V2’s lifecycle and operational-truth goals.

---

# Additional missing atomic RPG-core logic discovered during V2 audit

These items are appended rather than replacing existing checklist items. They are intentionally atomic. Mark them only when fully implemented and proven. Partial implementation remains unchecked.

## Z1. Checklist governance and truthfulness

- [ ] `RPG-GOV-001` Every checklist row has a stable ID.
- [ ] `RPG-GOV-002` Every checklist row has one explicit status: preserved, enhanced, intentionally divergent, unsupported, or not yet checked.
- [ ] `RPG-GOV-003` Every checked row has at least one proof path.
- [ ] `RPG-GOV-004` Every checked row names the implementation path that proves it.
- [ ] `RPG-GOV-005` Every checked row names the test path that proves it.
- [ ] `RPG-GOV-006` Every intentionally divergent row has a concrete reason.
- [ ] `RPG-GOV-007` Every intentionally divergent row has a regression or contract test proving the new law.
- [ ] `RPG-GOV-008` Every unsupported row has a support-boundary note.
- [ ] `RPG-GOV-009` Unsupported behavior is not marked as intentionally divergent.
- [ ] `RPG-GOV-010` Partial behavior is not marked as complete.
- [ ] `RPG-GOV-011` Behavior implemented in a dead or bypassed code path is not marked as complete.
- [ ] `RPG-GOV-012` Behavior implemented in one path but contradicted by another active path is not marked as complete.
- [ ] `RPG-GOV-013` The checklist distinguishes implementation detail from RPG semantic law.
- [ ] `RPG-GOV-014` The checklist keeps smallest necessary logic items instead of collapsing them into subsystem summaries.
- [ ] `RPG-GOV-015` CI can fail when a checked row has no proof reference.
- [ ] `RPG-GOV-016` CI can fail when a divergence has no divergence-register entry.
- [ ] `RPG-GOV-017` CI can fail when a proof path references a missing test file.
- [ ] `RPG-GOV-018` CI can fail when a checklist item references a removed implementation path.
- [ ] `RPG-GOV-019` CI can fail when a test marker is unknown.
- [ ] `RPG-GOV-020` CI can fail when mandatory oracle files are missing.
- [ ] `RPG-GOV-021` CI can fail when an oracle lacks schema version.
- [ ] `RPG-GOV-022` CI can fail when an oracle lacks seed/config metadata.
- [ ] `RPG-GOV-023` CI can fail when unsupported behavior is silently accepted as success.

## Z2. Resource conservation and inventory pressure law

- [x] `RPG-RES-072` All active resource acquisition paths share one conservation law. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-073` `InteractionSystem` harvest path and any standalone `HarvestSystem` path cannot diverge on capacity rules. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-074` `InteractionSystem` loot path and any standalone `LootSystem` path cannot diverge on capacity rules. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-075` A resource node charge is not decremented until inventory receipt is proven possible. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-076` A ground item is not removed until inventory receipt is proven possible. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-077` A corpse loot record is not consumed until inventory receipt is proven possible. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-078` Inventory slot capacity is checked before source mutation. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-079` Inventory weight capacity is checked before source mutation. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-080` Inventory stackability is checked before rejecting for slot pressure. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-081` Inventory add failure preserves the source item/node/corpse. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-082` Inventory add failure resets or preserves the interaction channel according to an explicit rule. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-083` Harvest completion emits both inventory addition and node depletion atomically. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-084` Loot completion emits both inventory addition and source removal atomically. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-RES-085` Partial channel progress does not create items.
- [ ] `RPG-RES-086` Interrupted channel progress does not create items.
- [ ] `RPG-RES-087` Interrupted channel progress does not remove source items.
- [x] `RPG-RES-088` Failed capacity check does not remove source items. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-089` Failed capacity check does not decrement node charges. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-090` Two actors completing the same loot target in the same tick cannot duplicate the item. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-091` Two actors completing the same resource-node charge in the same tick cannot duplicate the yield. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-092` Two actors completing the same corpse loot in the same tick cannot duplicate corpse rewards. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-093` Conflict resolution decides one authoritative winner for contested loot completion. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-094` Conflict resolution decides one authoritative winner per limited resource charge when required. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-095` Item quantity is preserved through pickup, stacking, selling, crafting, and dropping. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-096` Item weight is preserved through pickup, stacking, selling, crafting, and dropping. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-097` Item identity/kind is preserved through pickup, stacking, selling, crafting, and dropping. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-098` Harvest yield uses the node definition, not caller-provided arbitrary item data. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-099` Loot yield uses the ground/corpse source definition, not caller-provided arbitrary item data. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-100` Capacity failure reason is structured and observable. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-101` Resource source mutation and inventory mutation appear in the same authoritative update/apply transaction. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-102` Resource acquisition replay includes both source and inventory state. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-INFRA-115` Resource acquisition replay can prove no duplication across identical seed runs. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-INFRA-116` Resource acquisition replay can prove no item loss under capacity failure. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-103` Resource-node cooldown behavior is deterministic. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-104` Resource-node recharge behavior is deterministic. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-106` Resource-node depletion state survives serialization. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-107` Ground item state survives serialization. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-108` Corpse loot state survives serialization. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-105` Loot/harvest tests include slot pressure. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-106` Loot/harvest tests include weight pressure. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-107` Loot/harvest tests include stack merge under near-full inventory. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-108` Loot/harvest tests include two actors racing for one item. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-109` Loot/harvest tests include failure preserving source state. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-RES-110` Loot/harvest tests include success mutating inventory and source together. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->

## Z3. Authoritative pipeline and bypass prevention

- [ ] `RPG-INFRA-117` Every gameplay update enters the same authoritative refinement/apply pipeline.
- [x] `RPG-INFRA-118` No AI/state system mutates authoritative world state directly during proposal generation. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-INFRA-119` No standalone gameplay system can remove world objects without apply pipeline validation. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-INFRA-120` No standalone gameplay system can add inventory without apply pipeline validation. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-COMBAT-134` No standalone gameplay system can change combat HP without combat legality validation. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-144` No standalone gameplay system can change position without movement legality validation. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-SOC-060` No standalone gameplay system can change reputation/social state without social consequence validation. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-144` No standalone gameplay system can complete quests without quest lifecycle validation. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [ ] `RPG-INFRA-121` Every raw update is either accepted, refined, rejected, or marked unsupported.
- [x] `RPG-INFRA-122` Rejected updates preserve unrelated update domains. <!-- SOURCE: src/core/updates.py TEST: tests/engine/test_hardening_e5.py PROOF: integration -->
- [x] `RPG-INFRA-123` Rejected updates expose structured rejection reason. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-INFRA-124` Rejection reasons are replay-visible or log-visible. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-125` Merge logic for multiple `StateUpdate`s is deterministic. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-126` Merge logic has stable precedence for conflicting entity updates.
- [x] `RPG-INFRA-127` Merge logic has stable precedence for conflicting world updates. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-INFRA-128` Merge logic does not accidentally drop independent updates.
- [ ] `RPG-INFRA-129` Merge logic detects incompatible updates where required.
- [ ] `RPG-INFRA-130` Apply order is documented.
- [ ] `RPG-INFRA-131` Apply order is tested for cross-domain interactions.
- [ ] `RPG-INFRA-132` Apply order cannot depend on dictionary iteration where ordering matters.
- [ ] `RPG-INFRA-133` Apply order cannot depend on thread completion order where gameplay outcome matters.
- [ ] `RPG-INFRA-134` Pipeline tests include direct old-system calls if such calls remain importable.
- [ ] `RPG-INFRA-135` Pipeline tests prove dead/bypassed systems cannot create different gameplay laws.

## Z4. Movement intention, congestion, and blocked-route behavior

- [x] `RPG-WORLD-145` Movement intentions include pursue. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-146` Movement intentions include retreat. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-147` Movement intentions include hold. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-148` Movement intentions include reposition. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-149` Movement intentions include intercept. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-150` Movement intentions include guard. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-151` Movement intentions include regroup or an explicit intentional-divergence note explains why not. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-152` Movement intention influences target choice. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-153` Movement intention influences preferred tile choice. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-154` Movement intention influences blocked-tile fallback. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-155` Movement intention influences willingness to wait. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-156` Movement intention influences willingness to sidestep. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-157` Movement intention influences willingness to reroute. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-158` Movement intention influences willingness to break pursuit. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-159` Blocked movement first checks if target was reached. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-160` Blocked movement distinguishes temporary occupancy from invalid terrain. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-WORLD-161` Blocked movement distinguishes ally-blocked from enemy-blocked. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-162` Blocked movement distinguishes high-priority actor from low-priority actor. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-163` Blocked movement can wait when waiting is strategically valid. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-164` Blocked movement can yield when another actor has higher priority. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-WORLD-165` Blocked movement can sidestep when a safe adjacent alternative exists. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-166` Blocked movement can reroute when the direct step is blocked. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-167` Blocked movement can replan when route cache/path is stale. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-168` Blocked movement can regroup when party cohesion matters. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-169` Blocked movement can abandon route after bounded retry budget. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-170` Occupancy conflict has one authoritative winner per tile per tick. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-WORLD-171` Occupancy conflict losers receive structured reason. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-WORLD-172` Occupancy conflict losers do not overlap the winner. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-WORLD-173` Occupancy conflict does not weaken occupancy law silently. <!-- SOURCE: src/engine/legality.py TEST: tests/engine/test_phase5_combat_legality.py PROOF: unit -->
- [x] `RPG-WORLD-174` Sidestep avoids known occupied tiles. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-175` Sidestep avoids invalid terrain. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-176` Sidestep avoids stepping into lethal/hazardous tiles unless explicitly allowed. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-177` Retreat sidestep prefers increased distance from threat. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-178` Pursuit sidestep prefers preserving progress toward target. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-179` Guard movement prefers preserving guard radius. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-180` Intercept movement predicts target or path rather than chasing current position only. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-181` Regroup movement prefers party anchor or leader position. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-182` Movement fallback is bounded to avoid infinite loops. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-183` Stuck counters increment only when actual movement fails. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-184` Stuck counters reset when meaningful movement succeeds. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-185` Stuck handling can trigger route invalidation. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-186` Stuck handling can trigger strategic replan when movement is impossible. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-187` Movement replay can prove no overlapping entities after conflict resolution. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-188` Movement replay can prove deterministic outcome under same seed. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-189` Movement tests include one actor blocked by ally. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-190` Movement tests include one actor blocked by enemy. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-191` Movement tests include two actors targeting same tile. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-192` Movement tests include corridor congestion. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-193` Movement tests include party regroup movement. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-194` Movement tests include retreat under congestion. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-195` Movement tests include pursuit under congestion. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-196` Movement tests include invalid terrain vs occupied terrain distinction. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

## Z5. Tactical combat, targeting, and action choice consistency

- [ ] `RPG-COMBAT-135` Tactical action choice uses only legal candidate actions.
- [x] `RPG-COMBAT-136` Tactical action choice does not bypass movement/combat legality. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-137` Melee attack requires valid adjacency/engagement rule. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-138` Ranged attack requires valid range rule. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-139` Ranged attack requires valid line-of-sight or an explicit unsupported note. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-197` Area attack requires valid target position. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-140` Area attack affects only entities inside AoE radius. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-141` AoE friendly-fire behavior is explicit. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-142` Cover behavior is explicit if ranged combat supports cover. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-143` Weapon range affects tactical choice. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-144` Skill range affects tactical choice. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-108` Skill cost affects tactical choice. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-145` Readiness/cooldown affects tactical choice. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-109` Exhaustion affects tactical choice. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-146` Low HP affects tactical choice. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-110` Threat level affects tactical choice. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-147` Target stickiness prevents unrealistic full retarget every tick. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-148` Target stickiness can break when target invalid/dead/out of range beyond threshold. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-149` Disengagement has explicit consequence or safe-exit rule. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-150` Opportunity consequences apply only under legal conditions. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-198` Anti-stalemate handles chase loops. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-199` Anti-stalemate handles kite loops. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-200` Anti-stalemate handles repeated step-back loops. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-201` Anti-stalemate does not force illegal movement. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-151` Combat result emits damage trace. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-152` Combat result emits kill/death consequence when applicable. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-STRAT-145` Combat result emits reward/progression consequence when applicable. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-SOC-061` Combat result can trigger social/narrative consequence when applicable. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-STRAT-146` Combat result can trigger strategic update when applicable. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-153` Combat tests cover melee legality. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-154` Combat tests cover ranged legality. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-155` Combat tests cover AoE legality. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-156` Combat tests cover invalid target rejection. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-157` Combat tests cover dead target rejection. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-158` Combat tests cover target stickiness break condition. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-159` Combat tests cover exhaustion/readiness rejection. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

## Z6. Deterministic randomness and replay-stable execution

- [x] `RPG-INFRA-136` Same seed and same inputs produce same final authoritative hash. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-137` Same seed and same inputs produce same replay-visible trajectory. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-138` Different seeds produce meaningful divergence.
- [ ] `RPG-INFRA-139` Local sequential execution and worker execution produce equivalent gameplay outcomes.
- [ ] `RPG-INFRA-140` Thread scheduling order cannot change gameplay outcome.
- [x] `RPG-INFRA-141` Work queue order cannot change gameplay outcome except through documented priority. <!-- SOURCE: src/engine/governor.py TEST: tests/certification/test_envelope_violations.py PROOF: integration -->
- [x] `RPG-INFRA-142` RNG API supports domain separation or another proven call-order-independent scheme. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-143` RNG calls are scoped by deterministic context such as domain/entity/tick/sub-id or equivalent. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-WORLD-202` Spawn randomness is isolated from tactical randomness. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-SOC-062` Tactical randomness is isolated from social randomness. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-063` Social randomness is isolated from world-event randomness. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-ECON-001` Economy/shop randomness is isolated from combat randomness. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-STRAT-147` Quest generation randomness is isolated from movement randomness. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-WORLD-203` Calamity/world-boss randomness is isolated from local action randomness. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-INFRA-144` Adding a new actor cannot perturb unrelated actor decisions unless interaction requires it.
- [x] `RPG-INFRA-145` Adding a new non-interacting system cannot perturb existing RNG outcomes. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-146` Debug/logging/presentation cannot consume gameplay RNG. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-147` Tests detect accidental use of global `random` in gameplay code. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-148` Tests detect nondeterministic set/dict ordering where it affects gameplay.
- [x] `RPG-DATA-109` Replay hash includes all gameplay-relevant domains. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-110` Replay hash excludes presentation-only fields. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-111` Replay hash includes inventory. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-DATA-112` Replay hash includes entities and positions. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-113` Replay hash includes combat state. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-DATA-114` Replay hash includes strategic state. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-DATA-115` Replay hash includes social state. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-DATA-116` Replay hash includes world resources. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-117` Replay hash includes groups/parties. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-118` Replay hash includes quests/contracts. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-119` Replay hash includes progression. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-INFRA-149` Replay tests include repeated identical runs. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-150` Replay tests include sequential vs concurrent execution. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-120` Replay tests include save/load continuation. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

## Z7. Purpose-driven group and party cooperation

- [x] `RPG-SOC-064` Party formation can be driven by accepted social contract. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-148` Party formation can be driven by shared quest or project. <!-- SOURCE: src/engine/quests.py TEST: tests/quests/test_quest_transactions.py PROOF: integration -->
- [x] `RPG-SOC-065` Party formation can be driven by raid membership. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-066` Party formation can be driven by escort/expedition/mercenary/revenge contract kind. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-067` Proximity alone does not create a party unless explicitly modeled as a temporary tactical group. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-068` Temporary tactical group is distinct from contract party. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-069` Contract party has founder/leader. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-070` Contract party has member roles. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-071` Contract party has shared goal. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-072` Contract party links back to the contract/obligation that created it. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-073` Member entity links back to party/group ID. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-074` Member contract links back to party/group ID where relevant. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-075` Party anchor follows leader or agreed anchor rule. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-076` Party cohesion is updated from member positions. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-WORLD-204` Party cohesion affects regroup behavior. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-205` Party cohesion can trigger warnings or replan before dissolution. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-SOC-077` Party dissolves when leader is dead/missing according to explicit rule. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-078` Party dissolves when membership falls below minimum according to explicit rule. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-079` Party dissolves when contract is completed/abandoned/failed according to explicit rule. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-080` Party dissolution updates member group IDs. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-081` Party dissolution updates contract status when appropriate. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-082` Party dissolution applies social/reputation consequences when appropriate. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-083` Party target propagation occurs inside authoritative tick pipeline, not manual test-only invocation. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [ ] `RPG-COMBAT-160` Shared target is valid and alive when assigned.
- [ ] `RPG-COMBAT-161` Shared target clears when invalid/dead.
- [x] `RPG-SOC-084` Group focus fire does not override individual legality constraints. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-WORLD-206` Group behavior does not teleport or force illegal movement. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-SOC-085` Group formation test covers accepted contract. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-086` Group formation test covers no contract / proximity-only rejection. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-087` Group dissolution test covers dead leader. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-088` Group dissolution test covers scattered members. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-149` Group dissolution test covers contract abandonment consequence. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-089` Group coordination test runs through normal kernel tick, not only manual system call. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

## Z8. Strategic projects, blockers, leads, and cognition as RPG behavior

- [x] `RPG-STRAT-150` Strategic project creation is based on current needs/world state. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-151` Strategic project retention is bounded by interruption resistance. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-152` Strategic project switching requires margin or explicit emergency. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-153` Current project has reservation priority. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-154` Current objective has continuity priority. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-155` Objective derivation can create executable objectives. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-156` Objective derivation can create blockers when execution is impossible. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-STRAT-157` Blockers have kind.
- [ ] `RPG-STRAT-158` Blockers have subject/reference.
- [ ] `RPG-STRAT-159` Blockers have severity.
- [ ] `RPG-STRAT-160` Blockers have origin/spawned-from reference where useful.
- [x] `RPG-STRAT-161` Blockers can be resolved by acquiring missing knowledge. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-ECON-002` Blockers can be resolved by acquiring missing material. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-ECON-003` Blockers can be resolved by acquiring missing gold/resource. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [ ] `RPG-STRAT-162` Blockers can be resolved by finding location/target.
- [x] `RPG-STRAT-163` Blockers can be misdiagnosed under low cognition. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-STRAT-164` Misdiagnosis is bounded and explainable.
- [ ] `RPG-STRAT-165` Leads have kind.
- [ ] `RPG-STRAT-166` Leads have subject.
- [ ] `RPG-STRAT-167` Leads have certainty.
- [x] `RPG-STRAT-168` Leads have source trust. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-STRAT-169` Leads can be tested.
- [ ] `RPG-STRAT-170` Tested bad leads are suppressed.
- [ ] `RPG-STRAT-171` Exhausted leads are not retried blindly.
- [x] `RPG-STRAT-172` Lead retention obeys cognition profile capacity. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-173` Concern intake obeys cognition profile capacity. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-174` Detour breadth obeys cognition profile capacity. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-175` Detour depth obeys cognition profile capacity. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-176` Detour overflow suspends or reprioritizes project explicitly. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-177` Strategic overload is represented and observable. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-DATA-121` Strategic state persists across ticks. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-DATA-122` Strategic state survives serialization. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-DATA-123` Strategic state appears in replay/fingerprint. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-178` Strategic explanation exposes why project/objective changed. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-INFRA-151` Strategic explanation does not mutate strategic state. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-179` Strategic tests include high-cognition accurate diagnosis. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-180` Strategic tests include low-cognition misdiagnosis. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-181` Strategic tests include tested-lead suppression. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-182` Strategic tests include detour depth overflow. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-183` Strategic tests include current-objective retention. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-184` Strategic tests include project-switch margin. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->

## Z9. Social contracts, trust, reputation, and lived consequence law

- [x] `RPG-SOC-090` Public reputation and private relationship/bond are separate state. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-091` Private betrayal can override public reputation. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-092` Familiarity changes through interaction evidence. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-093` Trust/sentiment changes through interaction evidence. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-185` Social source trust changes through fulfilled/failed information. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [ ] `RPG-SOC-094` Turning points persist as narrative/life-event records.
- [x] `RPG-STRAT-186` Turning points influence later strategic/social appraisal. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-095` Contract offer has recruiter/founder. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-096` Contract offer has candidate. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-097` Contract offer has terms. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-098` Contract offer has status. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-187` Contract appraisal uses trust/private bond. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-188` Contract appraisal uses greed or reward preference. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-189` Contract appraisal uses capability/role fit. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-190` Contract appraisal uses prior trauma/betrayal. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-099` Accepted contract creates explicit obligation/contract state. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-100` Honored contract improves relevant social/reputation state. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-101` Broken contract worsens relevant social/reputation state. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-191` Abandoned contract can create betrayal/turning point where appropriate. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-102` Contract outcome propagates to all affected members. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-103` Contract outcome can affect public reputation. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-104` Contract outcome can affect private bonds. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-105` Contract outcome can affect future recruitment decisions. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-192` Contract outcome can affect strategic directives. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-INFRA-152` Social updates are authoritative updates, not direct mutation during appraisal. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-STRAT-193` Social appraisal is bounded by social bandwidth/cognition where applicable. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-106` Social tests include direct betrayal by recruiter. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-107` Social tests include general betrayal trauma. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-108` Social tests include high reward overcoming neutral reluctance when legal. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-109` Social tests include reputation distinct from private trust. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-110` Social tests include contract honored. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-111` Social tests include contract broken/abandoned. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-SOC-112` Social tests include party dissolution consequence if contract-backed. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

## Z10. Progression, classes, skills, equipment, and growth law

- [x] `RPG-PROG-111` XP/reward grant is authoritative and traceable to event. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-112` Level-up thresholds are deterministic. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-113` Attribute point grant is deterministic. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-114` Attribute allocation checks available points. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-115` Attribute allocation checks valid attribute name. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-116` Attribute allocation applies aptitude multiplier or explicit divergence. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-117` Attribute caps are enforced. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-118` Effective stats recompute from base stats plus gear plus traits plus modifiers. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-119` Effective stats clamp to valid ranges.
- [x] `RPG-PROG-120` Skill definition includes ID. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-121` Skill definition includes type/category. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-122` Skill definition includes target rule. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-COMBAT-162` Skill definition includes range where relevant. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-163` Skill definition includes cost/cooldown where relevant. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-123` Physical skill scaling is defined. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-124` Magical skill scaling is defined. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-125` Elemental skill scaling is defined. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-126` Hybrid skill scaling is defined. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-127` Skill scaling uses effective stats, not raw stats, where intended. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-PROG-128` Passive skills apply through defined modifier path.
- [ ] `RPG-COMBAT-164` Active skills require legality checks before applying effects.
- [x] `RPG-PROG-129` Class selection or assignment is explicit. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-130` Class starting gear is data-driven or documented. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-131` Class skill unlocks are deterministic. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-132` Gear equip validates slot. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-133` Gear equip validates ownership/inventory. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-PROG-134` Gear equip changes effective stats through authoritative update. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-135` Gear ranking logic is deterministic. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-136` Better gear can be selected by equipment service if that behavior is supported. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-RES-111` Home storage preserves items. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-ECON-004` Shop buy checks gold before adding item. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-112` Shop buy checks inventory capacity before subtracting gold. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-ECON-005` Shop sell checks item exists before adding gold. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-ECON-006` Crafting checks recipe exists. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-ECON-007` Crafting checks materials. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-ECON-008` Crafting checks gold/cost. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-RES-113` Crafting checks inventory capacity for output. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-ECON-009` Crafting consumes materials and adds output atomically. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-DATA-124` Progression replay includes XP/level/attributes/skills/gear. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-137` Progression tests include attribute allocation. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-138` Progression tests include cap enforcement. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-139` Progression tests include skill scaling. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-PROG-140` Progression tests include gear equip. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [x] `RPG-ECON-010` Progression tests include crafting atomicity. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->

## Z11. World, region, spawn, calamity, and ecology law

- [x] `RPG-WORLD-207` World seed controls world generation. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-208` World generation is deterministic under same seed. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-209` Region assignment is deterministic. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-210` Region topology is stable for same seed. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-RES-114` Region resource placement is deterministic. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-STRAT-194` Region difficulty/threat appraisal is deterministic. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-DATA-125` Spawn tables are data-driven or documented as hardcoded intentionally. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-211` Spawned entity loadout is valid.
- [ ] `RPG-WORLD-212` Spawned entity faction is valid.
- [ ] `RPG-WORLD-213` Spawned entity role is valid.
- [ ] `RPG-WORLD-214` Spawned entity home/leash fields are valid where needed.
- [x] `RPG-WORLD-215` Spawn avoids invalid terrain. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-216` Spawn avoids occupied tile or uses conflict-safe placement. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-217` Camp placement is deterministic. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-218` Camp guards spawn near camp. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-219` Camp guards have leash/return behavior. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-WORLD-220` Leash gives up chase after explicit condition.
- [x] `RPG-WORLD-221` Return-to-camp path is legal movement, not teleport, unless intentional. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-222` Calamity trigger rule is deterministic. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-223` Calamity escalation rule is deterministic. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-224` Calamity consequences affect world state authoritatively. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-225` World boss spawn rule is deterministic. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-126` World boss state appears in replay/fingerprint. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-ECON-011` Building sabotage affects building state authoritatively. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-COMBAT-165` Building damage affects service availability if supported. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-ECON-012` Building repair restores service availability if supported. <!-- SOURCE: src/town/shop.py TEST: tests/town/test_town_building_contract.py PROOF: integration -->
- [x] `RPG-INFRA-153` World dynamics run even on quiet ticks where required. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-INFRA-154` World dynamics do not depend on presentation/API polling. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-127` World state survives serialization. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-DATA-128` World replay includes resources/buildings/regions/camps/calamities. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-226` World tests include same-seed generation. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-227` World tests include different-seed divergence. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-228` World tests include camp/leash behavior. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-229` World tests include calamity/boss behavior if supported. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->

## Z12. Phase guard, authorization, and mutation boundary law

- [ ] `RPG-INFRA-155` Each engine phase declares allowed read domains.
- [ ] `RPG-INFRA-156` Each engine phase declares allowed write/update domains.
- [ ] `RPG-INFRA-157` Each engine phase declares allowed emit/event domains.
- [ ] `RPG-INFRA-158` Unauthorized read is detected or explicitly allowed.
- [ ] `RPG-INFRA-159` Unauthorized write is rejected.
- [ ] `RPG-INFRA-160` Unauthorized emit is rejected or flagged.
- [ ] `RPG-INFRA-161` Phase guard cannot be disabled silently in production/certification profiles.
- [ ] `RPG-INFRA-162` Phase guard failure is structured and observable.
- [ ] `RPG-INFRA-163` Phase guard failure does not partially mutate world state.
- [ ] `RPG-INFRA-164` AI/thought phase cannot write authoritative state directly.
- [ ] `RPG-INFRA-165` Presentation phase cannot mutate authoritative state.
- [x] `RPG-INFRA-166` Replay phase cannot mutate authoritative state. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-167` Metrics/logging phase cannot mutate authoritative state. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [ ] `RPG-INFRA-168` Worker phase cannot bypass authoritative apply.
- [ ] `RPG-INFRA-169` Phase guard tests cover allowed read.
- [ ] `RPG-INFRA-170` Phase guard tests cover blocked write.
- [ ] `RPG-INFRA-171` Phase guard tests cover blocked emit.
- [ ] `RPG-INFRA-172` Phase guard tests cover no partial mutation on violation.

## Z13. Spatial index and map authority law

- [x] `RPG-WORLD-230` Spatial index can add entity/object to cell. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-231` Spatial index can remove entity/object from cell. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-232` Spatial index can move entity/object between cells. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-233` Spatial index query returns current occupants. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-234` Spatial index does not return removed occupants. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-235` Spatial index does not duplicate moved occupants. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-236` Spatial index supports deterministic query ordering when order matters. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-237` Spatial index stays consistent with authoritative entity positions after apply. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-238` Spatial index update is atomic with position update. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-239` Movement legality uses authoritative map/spatial truth. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-COMBAT-166` Combat range queries use authoritative map/spatial truth where applicable. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-WORLD-240` Perception queries use authoritative map/spatial truth where applicable. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-241` Spawn placement uses authoritative map/spatial truth. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-242` Spatial index survives serialization or can be rebuilt deterministically. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-243` Spatial tests include add/query. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-244` Spatial tests include remove/query. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-WORLD-245` Spatial tests include move/query. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] Spatial tests include sync after movement apply. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->

## Z14. API, inspector, logging, and replay truth surface

- [x] `RPG-DATA-129` API state view is derived from authoritative state. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-DATA-130` API state view does not mutate authoritative state. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-DATA-131` API exposes supported gameplay state only. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-DATA-132` API marks unsupported state honestly. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-DATA-133` Inspector reads authoritative/presenter state only. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-DATA-134` Inspector does not crash on empty optional gameplay state. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-STRAT-195` Inspector exposes cognition/strategy where supported. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-SOC-113` Inspector exposes social/contracts where supported. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-RES-115` Inspector exposes inventory/equipment where supported. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-COMBAT-167` Inspector exposes combat/progression where supported. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] `RPG-INFRA-173` Logs are structured.
- [ ] `RPG-INFRA-174` Logs include timestamp.
- [x] `RPG-INFRA-175` Logs include level. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-INFRA-176` Logs include component.
- [ ] `RPG-INFRA-177` Logs include message.
- [x] `RPG-INFRA-178` Logs include rejection reasons where relevant. <!-- SOURCE: src/engine/pipeline.py TEST: tests/engine/test_replay_determinism.py PROOF: integration -->
- [ ] `RPG-INFRA-179` Logs include final authoritative hash at shutdown.
- [x] `RPG-INFRA-180` Metrics count accepted/rejected updates where relevant. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-RES-116` Metrics count resource pressure rejection where relevant. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-WORLD-246` Metrics count movement congestion where relevant. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-DATA-135` Metrics count unsupported behavior attempts where relevant. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] `RPG-DATA-136` Replay manifest write is atomic. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-137` Replay manifest failure preserves old manifest. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-138` Replay finalization respects timeout. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-139` Replay includes enough state to debug RPG logic. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-DATA-140` Replay excludes presentation-only noise. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] API/inspector/logging tests include missing optional fields. <!-- SOURCE: src/api/presenters/state_presenter.py TEST: tests/api/test_rest_parity.py PROOF: integration -->
- [x] Replay tests include corrupt/write-failure behavior. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->

## Z15. Safe degraded mode and infrastructure fallback law

- [ ] `RPG-INFRA-181` Broker-disabled mode still runs core RPG simulation.
- [ ] `RPG-INFRA-182` RabbitMQ disabled mode does not import/connect unexpectedly.
- [ ] `RPG-INFRA-183` Kafka disabled mode does not import/connect unexpectedly.
- [ ] `RPG-INFRA-184` Redis disabled/missing mode does not crash RPG core if optional.
- [ ] `RPG-INFRA-185` Local sequential executor preserves gameplay laws.
- [ ] `RPG-INFRA-186` Worker executor preserves gameplay laws.
- [x] `RPG-INFRA-187` Fallback executor does not change deterministic outcome. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-188` Shutdown suspends new work arrival.
- [x] `RPG-INFRA-189` Shutdown flushes replay/logging within timeout. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [ ] `RPG-INFRA-190` Shutdown emits final authoritative hash.
- [ ] `RPG-INFRA-191` Failure in optional infrastructure does not corrupt authoritative state.
- [ ] `RPG-INFRA-192` Degraded mode is observable, not silent.
- [x] `RPG-INFRA-193` Degraded mode tests cover brokerless execution. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-INFRA-194` Degraded mode tests cover shutdown. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-INFRA-195` Degraded mode tests cover optional dependency absence. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

## Z16. Small but necessary default/no-op/safety laws

- [x] `RPG-WORLD-247` Empty world tick does not crash. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [x] `RPG-WORLD-248` Empty world tick advances passive time if required. <!-- SOURCE: src/engine/world_dynamics.py TEST: tests/rpg/test_living_world_ph9.py PROOF: longrun -->
- [ ] `RPG-STRAT-196` Entity with missing optional strategy state gets safe default.
- [x] `RPG-SOC-114` Entity with missing optional social state gets safe default. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-RES-117` Entity with missing optional inventory state gets safe default or explicit invalid-state error. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-COMBAT-168` Entity with missing required combat state fails loudly before gameplay. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-INFRA-196` No-op update preserves state hash except allowed time/metadata changes. <!-- SOURCE: src/platform/rng.py TEST: tests/engine/test_long_run_determinism.py PROOF: longrun -->
- [x] `RPG-INFRA-197` Copy/clone of state is deep enough to protect authoritative state from worker mutation. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [x] `RPG-INFRA-198` Frozen snapshot cannot be mutated by AI proposal code. <!-- SOURCE: src/core/immutability.py TEST: tests/core/test_authoritative_state_contract.py PROOF: negative -->
- [ ] `RPG-DATA-141` Serialization round-trip preserves gameplay state.
- [x] `RPG-DATA-142` Serialization round-trip rejects unknown critical fields unless intentionally allowed. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-PROG-141` Default values do not create free items/gold/XP. <!-- SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: integration -->
- [ ] `RPG-SOC-115` Default values do not create hidden contracts/quests.
- [x] `RPG-WORLD-249` Default values do not create invisible movement permissions. <!-- SOURCE: src/engine/movement.py TEST: tests/rpg/test_movement_congestion.py PROOF: integration -->
- [x] `RPG-RES-118` Default values do not bypass capacity/caps. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-COMBAT-169` Clamp/floor/ceiling rules are explicit for HP. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-COMBAT-170` Clamp/floor/ceiling rules are explicit for stamina/readiness. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-SOC-116` Clamp/floor/ceiling rules are explicit for reputation/trust if bounded. <!-- SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->
- [x] `RPG-STRAT-197` Clamp/floor/ceiling rules are explicit for cognition metrics if bounded. <!-- SOURCE: src/core/strategic.py TEST: tests/engine/test_phase6_strategic_cognition.py PROOF: integration -->
- [x] `RPG-RES-119` Clamp/floor/ceiling rules are explicit for inventory weight/slots. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_resource_conservation.py PROOF: race -->
- [x] `RPG-INFRA-199` Safe fallback tests cover empty state. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-INFRA-200` Safe fallback tests cover no-op update. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-INFRA-201` Safe fallback tests cover copy isolation. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] `RPG-INFRA-202` Safe fallback tests cover serialization round-trip. <!-- SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->

---

## Z17. Transaction Legality and Economy Hardening

- [x] `RPG-RES-200` Capacity enforcement must account for removals during conversion (CRAFTING). <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_transaction_completion.py PROOF: integration -->
- [x] `RPG-RES-201` Capacity enforcement must use standardized `INVENTORY_FULL` reason code for all resource transfer rejections. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_transaction_completion.py PROOF: integration -->
- [x] `RPG-RES-202` Authoritative application of resource transfers must be atomic across source depletion and destination receipt. <!-- SOURCE: src/engine/apply.py TEST: tests/rpg/test_transaction_completion.py PROOF: integration -->
- [x] `RPG-ECON-200` Shop buy rejections must distinguish between `INVENTORY_FULL`, `INSUFFICIENT_GOLD`, and `OUT_OF_STOCK`. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_transaction_completion.py PROOF: integration -->
- [x] `RPG-ECON-201` Shop sell rejections must distinguish between `LIQUIDITY_EXHAUSTED` and `TARGET_INVALID`. <!-- SOURCE: src/core/conservation.py TEST: tests/rpg/test_transaction_completion.py PROOF: integration -->
- [x] `RPG-ECON-202` Regional price modifiers must impact authoritative transaction costs. <!-- SOURCE: src/systems/market.py TEST: tests/rpg/test_domain_8_economy.py PROOF: integration -->
- [x] `RPG-ECON-203` Strategic intelligence must abandon shopping projects when buildings are non-functional. <!-- SOURCE: src/systems/strategic.py TEST: tests/rpg/test_domain_8_economy.py PROOF: integration -->

## Z18. V2 RPG Hardening Extras (E5/E6)

- [x] `RPG-COMBAT-200` Surround penalty: being surrounded by 3 or more hostiles applies damage multipliers. <!-- SOURCE: src/engine/combat.py TEST: tests/engine/test_hardening_e5.py PROOF: integration -->
- [x] `RPG-INFRA-203` Emergency governor throttle drops non-critical subsystems when tick budget exceeds 100ms limit. <!-- SOURCE: src/engine/governor.py TEST: tests/engine/test_hardening_e5.py PROOF: integration -->
- [x] `RPG-STRAT-200` Strategic intelligence phase realigned upstream of combat to inform single-tick intent. <!-- SOURCE: src/engine/pipeline.py TEST: tests/engine/test_phase_order_contract.py PROOF: integration -->
- [x] `RPG-SOC-200` Phantom leader dissolution immediately updates group sliding state during resolution. <!-- SOURCE: src/engine/pipeline.py TEST: tests/social/test_contract_lifecycle_phase7.py PROOF: integration -->

---

# Final audit note

This file is intentionally longer than the previous generated checklist. The previous version was a summary. This one is an exhaustive semantic ledger. Do not collapse these items unless the implementation also collapses the behavior into a single proven law with enough tests to cover the atomic cases.

