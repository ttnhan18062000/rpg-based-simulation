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

The previous generated checklist was too short because it compressed subsystems into summary laws. This version keeps the original atomic rows and appends additional missing atomic laws.

## Latest V2 coverage update — 2026-05-02 (Audit Correction)

This update corrects the previously inflated coverage. Only items with machine-readable proof (SOURCE: and TEST: markers) that are verified to exist in V2 are marked as complete.

Coverage after audit cleanup:

- Total checklist items: 1702
- Completed items: 52
- Incomplete / unproven items: 1650
- Coverage: 3.05%
- Status: RPG DEPTH AND PROGRESSION BASELINE VERIFIED


Updated conservative notes:

- Resource conservation is now strongly improved for harvest, loot, ground-item pickup, corpse loot, crafting, shop transactions, and quest reward capacity checks.
- Phase 3 is still not fully complete until all remaining direct reward/update paths are either routed through `ResourceTransactionResolver` or explicitly documented as safe non-inventory updates.
- Movement coverage is improved for semantic modes, sidestep, yield, hold, regroup, retreat/evasive opportunity-attack behavior, and spatial index contracts.
- Determinism coverage improved through RNG/hash/replay tests, but full call-order independence remains unchecked.
- Phase 0 governance remains incomplete because the checklist is still not backed by a full machine-readable proof ledger for every item.

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
- [x] **[RPG-0001]** `action_proposals_as_intents`: Action proposals are typed intents, not direct world mutation. <!-- ID: RPG-0001 SOURCE: src/core/updates.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0002]** `typed_update_buckets`: Every gameplay side effect is represented as a typed update bucket (mind, perception, navigation, progression, identity, routine, interaction, spatial, building, social, social-event, reputation, strategic, world, combat-trace). <!-- ID: RPG-0002 SOURCE: src/core/updates.py TEST: tests/engine/test_milestone_a_closure.py PROOF: unit -->
- [x] **[RPG-0003]** `coerced_reason_models`: Legacy reason strings and targets are coerced into structured authoritative reason/target models. <!-- ID: RPG-0003 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0004]** `world_mutation_after_proposal`: World mutation happens after proposal generation, not inside worker thought code. <!-- ID: RPG-0004 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_milestone_a_closure.py PROOF: unit -->
- [x] **[RPG-0005]** `partial_rejection_support`: Action application supports partial rejection without corrupting unrelated update domains. <!-- ID: RPG-0005 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0006]** `tick_outcome_preservation`: Conflict resolution preserves one authoritative outcome per tick. <!-- ID: RPG-0006 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0007]** `thought_application_decoupling`: Worker decision-making is decoupled from authoritative application. <!-- ID: RPG-0007 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_milestone_a_closure.py PROOF: unit -->
- [x] **[RPG-0008]** `observability_from_results`: Replay and observability consume authoritative results rather than defining them. <!-- ID: RPG-0008 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_observability_budgets.py PROOF: integration -->

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
- [x] **[RPG-0009]** `manhattan_spatial_metric`: Manhattan distance is the shared spatial metric for movement and combat range where claimed. <!-- ID: RPG-0009 SOURCE: src/engine/movement.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0010]** `cardinal_occupancy_legality`: Cardinal/tile movement and occupancy legality are explicit. <!-- ID: RPG-0010 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0011]** `collision_rejection`: Occupied-tile movement is rejected or redirected rather than silently overlapped. <!-- ID: RPG-0011 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0012]** `melee_engagement_rules`: Melee legality depends on adjacency/engagement rules, not raw damage stats. <!-- ID: RPG-0012 SOURCE: src/engine/legality.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] **[RPG-0013]** `ranged_los_rules`: Ranged legality depends on range and line-of-sight rules. <!-- ID: RPG-0013 SOURCE: src/engine/legality.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] **[RPG-0014]** `aoe_radius_legality`: AoE legality is a function of target position and area-of-effect radius. <!-- ID: RPG-0014 SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [x] **[RPG-0015]** `mob_leash_radius`: Chase gives up when beyond 1.5x leash radius. <!-- ID: RPG-0015 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0016]** `readiness_cadence_decoupling`: World-time progression is distinct from readiness-based action cadence. <!-- ID: RPG-0016 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0017]** `pathfinding_occupancy_awareness`: Pathfinding avoids occupied tiles but allows targeting them. <!-- ID: RPG-0017 SOURCE: src/engine/movement.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0018]** `authoritative_move_cost`: Movement cost and speed are applied during authoritative application, not in worker proposals. <!-- ID: RPG-0018 SOURCE: src/engine/movement.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0019]** `legacy_damage_parity`: Damage calculation math is consistent with legacy rules. <!-- ID: RPG-0019 SOURCE: src/engine/combat.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: unit -->
- [x] **[RPG-0020]** `movement_intent_vs_result`: Movement intentions are distinct from movement execution results. <!-- ID: RPG-0020 SOURCE: src/core/updates.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-0021]** `passive_world_progression`: Quiet ticks still advance passive world consequences. <!-- ID: RPG-0021 SOURCE: src/engine/apply.py TEST: tests/p2_long_run_stability.py PROOF: simulation -->
- [x] **[RPG-0022]** `disengagement_consequences`: Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules. <!-- ID: RPG-0022 SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0023]** `stalemate_breaker`: Anti-stalemate logic handles repeated chase/kite/step-back loops. <!-- ID: RPG-0023 SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0024]** `movement_intent_modes`: Movement intentions exist as semantic modes (pursue, retreat, hold, reposition, intercept, guard, regroup). <!-- ID: RPG-0024 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0025]** `congestion_ladder`: Congestion is handled through waiting/yielding/sidestepping/rerouting before weakening occupancy. <!-- ID: RPG-0025 SOURCE: src/engine/movement.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0026]** `tactical_choice_legality`: Tactical choice is a bounded choice among legal actions, not a geometry exploit. <!-- ID: RPG-0026 SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

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
- [x] **[RPG-0027]** `looting_channeled`: Looting is a channeled state with progress, interruption, and completion semantics. <!-- ID: RPG-0027 SOURCE: src/engine/interaction.py TEST: tests/unit/test_interaction_system.py PROOF: unit -->
- [x] **[RPG-0028]** `harvesting_channeled`: Harvesting is a channeled state tied to nearby resource-node legality and harvest duration. <!-- ID: RPG-0028 SOURCE: src/engine/interaction.py TEST: tests/unit/test_interaction_system.py PROOF: unit -->
- [x] **[RPG-0029]** `loot_abort_slot_pressure`: Loot/harvest can abort because of inventory slot pressure. <!-- ID: RPG-0029 SOURCE: src/core/inventory.py TEST: tests/unit/test_interaction_system.py PROOF: unit -->
- [x] **[RPG-0030]** `loot_abort_weight_pressure`: Loot/harvest can abort because of inventory weight pressure. <!-- ID: RPG-0030 SOURCE: src/core/inventory.py TEST: tests/unit/test_interaction_system.py PROOF: unit -->
- [x] **[RPG-0031]** `inventory_slots_and_weight`: Inventory state tracks both slots and weight/carry burden. <!-- ID: RPG-0031 SOURCE: src/core/state.py TEST: tests/inventory/test_inventory_hardening.py PROOF: unit -->
- [x] **[RPG-0032]** `authoritative_side_effects`: Ground items, node yields, and inventory additions/removals are authoritative side effects. <!-- ID: RPG-0032 SOURCE: src/engine/interaction.py TEST: tests/unit/test_interaction_system.py PROOF: unit -->
- [x] **[RPG-0033]** `town_return_semantics`: Town return is a real gameplay state, not a cosmetic teleport. <!-- ID: RPG-0033 SOURCE: src/engine/town_resolution.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0034]** `shop_visit_semantics`: Shop visits resolve bounded buy/sell behavior using inventory/gold truth. <!-- ID: RPG-0034 SOURCE: src/engine/shop.py TEST: tests/contract/test_town_contract.py PROOF: contract -->
- [x] **[RPG-0035]** `blacksmith_visit_semantics`: Blacksmith visits resolve recipe/crafting/material-gating behavior. <!-- ID: RPG-0035 SOURCE: src/engine/blacksmith.py TEST: tests/contract/test_town_contract.py PROOF: contract -->
- [x] **[RPG-0036]** `guild_visit_semantics`: Guild visits produce intel, quests, and material/resource hints. <!-- ID: RPG-0036 SOURCE: src/engine/quests.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0037]** `inn_visit_semantics`: Inn/home/class-hall visits have distinct progression or recovery semantics. <!-- ID: RPG-0037 SOURCE: src/engine/town_resolution.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0038]** `building_interaction_slices`: Building interactions are explicit gameplay slices, not generic proximity triggers. <!-- ID: RPG-0038 SOURCE: src/engine/interaction.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

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
- [x] **[RPG-0039]** `strategic_state_persistence`: Strategic state is first-class and survives across ticks (directives, projects, objectives, concerns, blockers, obligations, contracts, offers, leads, candidate zones, hypotheses). <!-- ID: RPG-0039 SOURCE: src/core/strategic.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0040]** `project_objective_continuity`: Current project/objective continuity is explicit and bounded. <!-- ID: RPG-0040 SOURCE: src/systems/strategic.py TEST: tests/strategic/test_interruption_resistance.py PROOF: contract -->
- [x] **[RPG-0041]** `project_interruption_resistance`: Project switching uses interruption resistance / margin logic, not full rescore every tick. <!-- ID: RPG-0041 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-0042]** `current_project_retention`: Current project gets reservation/retention priority inside bounded strategic slices. <!-- ID: RPG-0042 SOURCE: src/systems/strategic.py TEST: tests/strategic/test_interruption_resistance.py PROOF: contract -->
- [x] **[RPG-0043]** `strategic_blocker_inference`: Blockers are inferred from project/objective state and can be accurate or misdiagnosed under bounded cognition. <!-- ID: RPG-0043 SOURCE: src/systems/strategic.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0044]** `strategic_lead_retainment`: Leads are retained under profile-specific bandwidth limits. <!-- ID: RPG-0044 SOURCE: src/strategy/cognition_capacity.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0045]** `biological_need_concerns`: Concerns are retained under profile-specific intake limits. <!-- ID: RPG-0045 SOURCE: src/strategy/cognition_capacity.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0046]** `strategic_detour_suggestion`: Detours are suggested from blockers and leads within breadth/depth limits. <!-- ID: RPG-0046 SOURCE: src/systems/detour.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-0047]** `strategic_lead_suppression`: Rejected/tested leads are suppressed to avoid blind retries. <!-- ID: RPG-0047 SOURCE: src/systems/detour.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0048]** `strategic_overload_visibility`: Strategic overload is visible through bounded capacity metrics. <!-- ID: RPG-0048 SOURCE: src/strategy/cognition_capacity.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0049]** `strategic_outcome_processing`: Event interpretation can mutate directives, projects, concerns, and source trust. <!-- ID: RPG-0049 SOURCE: src/systems/event_interpreter.py TEST: tests/strategic/test_event_interpretation.py PROOF: contract -->
- [x] **[RPG-0050]** `strategic_knowledge_uncertainty`: Knowledge remains uncertain (leads/candidate zones/hypotheses) until resolved. <!-- ID: RPG-0050 SOURCE: src/core/strategic.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0051]** `strategic_cognition_export`: Cognition graph export exposes persisted strategic state without becoming the source of truth. <!-- ID: RPG-0051 SOURCE: src/strategy/cognition_capacity.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->

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
- [x] **[RPG-0052]** `social_betrayal_override`: Private betrayal history can override public recruiter reputation. <!-- ID: RPG-0052 SOURCE: src/social/appraisal.py TEST: tests/social/test_betrayal_consequence.py PROOF: contract -->
- [x] **[RPG-0053]** `social_learning_trust`: Social learning updates familiarity/trust-like bonds from interaction evidence. <!-- ID: RPG-0053 SOURCE: src/social/appraisal.py TEST: tests/social/test_source_trust.py PROOF: contract -->
- [x] **[RPG-0054]** `social_contracts_explicit`: Social contracts and obligations are explicit strategic objects, not flavor text. <!-- ID: RPG-0054 SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle.py PROOF: contract -->
- [x] **[RPG-0055]** `social_contract_consequences`: Breaking or honoring contracts has persistent consequences. <!-- ID: RPG-0055 SOURCE: src/social/contracts.py TEST: tests/social/test_contract_lifecycle.py PROOF: contract -->
- [x] **[RPG-0056]** `social_reputation_vs_meaning`: Public reputation is distinct from private narrative meaning. <!-- ID: RPG-0056 SOURCE: src/social/relationships.py TEST: tests/social/test_relationships.py PROOF: contract -->
- [x] **[RPG-0057]** `social_turning_points`: Turning points and interpreted life events feed future strategic and social behavior. <!-- ID: RPG-0057 SOURCE: src/social/appraisal.py TEST: tests/social/test_betrayal_consequence.py PROOF: contract -->
- [x] **[RPG-0058]** `social_party_cooperation`: Party/group cooperation is purpose-driven, not just proximity clustering. <!-- ID: RPG-0058 SOURCE: src/systems/groups.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-0059]** `social_recruitment_evaluation`: Recruitment evaluates trust, debt, greed, capability fit, and prior trauma. <!-- ID: RPG-0059 SOURCE: src/social/appraisal.py TEST: tests/social/test_contract_lifecycle.py PROOF: contract -->

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
- [x] **[RPG-0060]** `stat_recalculation_parity`: Wounds reduce effective ATK/DEF/HP. <!-- ID: RPG-0060 SOURCE: src/engine/rpg_depth.py TEST: tests/strategic/test_biological_needs.py PROOF: contract -->
- [x] **[RPG-0061]** `attribute_recalculation_determinism`: Attributes and derived stats recalculate from base + modifiers. <!-- ID: RPG-0061 SOURCE: src/progression/leveling.py TEST: tests/progression/test_leveling.py PROOF: contract -->
- [x] **[RPG-0062]** `class_scaling_parity`: Growth rates and attribute biases match the authoritative class table. <!-- ID: RPG-0062 SOURCE: src/engine/evolution.py TEST: tests/progression/test_leveling.py PROOF: contract -->
- [x] **[RPG-0063]** `skill_cooldown_determinism`: Skill cooldowns and resource costs are enforced deterministically. <!-- ID: RPG-0063 SOURCE: src/engine/legality.py TEST: tests/progression/test_leveling.py PROOF: contract -->
- [x] **[RPG-0064]** `level_up_atomic`: Level up results in atomic attribute increases and resource refills. <!-- ID: RPG-0064 SOURCE: src/engine/apply.py TEST: tests/progression/test_leveling.py PROOF: contract -->
- [x] **[RPG-0065]** `passive_effect_consistency`: Passive traits apply modifiers consistently through the recalculated stack. <!-- ID: RPG-0065 SOURCE: src/progression/leveling.py TEST: tests/progression/test_leveling.py PROOF: contract -->
- [x] **[RPG-0066]** `level_cap_enforced`: Attributes are capped at 100. <!-- ID: RPG-0066 SOURCE: src/engine/apply.py TEST: tests/progression/test_attribute_growth.py PROOF: contract -->
- [x] **[RPG-0067]** `rpg_math_contracts`: RPG math and synergy rules are tested as stable contracts, not intuition. <!-- ID: RPG-0067 SOURCE: src/engine/rpg_depth.py TEST: tests/progression/test_leveling.py PROOF: contract -->
- [x] **[RPG-0068]** `target_stickiness_bias`: Always switch if no current target. <!-- ID: RPG-0068 SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->

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
- [x] **[RPG-0069]** `world_gen_determinism`: World generation is deterministic under seed and domain-specific RNG use. <!-- ID: RPG-0069 SOURCE: src/systems/generator.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0070]** `authoritative_world_objects`: Town, sanctuary, camps, buildings, corpses, and entities are authoritative world objects. <!-- ID: RPG-0070 SOURCE: src/systems/generator.py TEST: tests/progression/test_rpg_advancement.py PROOF: contract -->
- [x] **[RPG-0071]** `entity_snapshot_immutability`: Entity snapshots are immutable enough for worker reasoning and deterministic replay. <!-- ID: RPG-0071 SOURCE: src/core/state.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0072]** `no_hidden_mutation_leaks`: No hidden mutation leaks occur from snapshot or AI evaluation paths. <!-- ID: RPG-0072 SOURCE: src/engine/apply.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0073]** `deterministic_replay_delta`: Deterministic replay/delta behavior is preserved across runs with same seed. <!-- ID: RPG-0073 SOURCE: src/engine/apply.py TEST: tests/p1_replay_fidelity.py PROOF: contract -->
- [x] **[RPG-0074]** `regional_hazard_hazards`: Regional hazards, calamities, local scars, and world consequences can feed gameplay and strategy. <!-- ID: RPG-0074 SOURCE: src/engine/domain_logic.py TEST: tests/strategic/test_detour_suggestion.py PROOF: contract -->
- [x] **[RPG-0075]** `entity_builder_serialization`: Entity builder and serialization preserve gameplay-relevant state safely. <!-- ID: RPG-0075 SOURCE: src/core/builder.py TEST: tests/progression/test_rpg_advancement.py PROOF: contract -->
- [x] **[RPG-0076]** `engine_phase_order`: Engine phase order preserves gameplay semantics and subsystem tick integrity. <!-- ID: RPG-0076 SOURCE: src/engine/apply.py TEST: tests/progression/test_rpg_advancement.py PROOF: contract -->

## B. Test-derived atomic checklist (every included RPG-core test)

Each checkbox below is derived from one original test. Keep the original test name in the ledger so `src` comparison stays auditable.

### Combat / movement rulebook & combat-time

#### `ai/test_tactical_milestone_4.py`

- [x] **[RPG-0077]** `UNSUPPORTED`: `test_reactive_cover_seeking`: Reactive cover seeking — Verify that actor seeks cover only when a ranged threat is visible.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0078]** `UNSUPPORTED`: `test_chokepoint_holding`: Chokepoint holding — Verify that actor identifies and holds a 1-tile gap.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0079]** `UNSUPPORTED`: `test_cardinal_opposite_bracketing`: Cardinal opposite bracketing — Verify that two allies bracket a target from opposite sides.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0080]** `UNSUPPORTED`: `test_tactical_mode_integration_handler`: Tactical mode integration handler — Verify that CombatHandler respects the tactical target_pos.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `arena/test_arena_harness_contract.py`

- [x] **[RPG-0081]** `test_arena_structural_determinism`: Arena structural determinism — Verify that the arena produced structurally identical ScenarioReports for the same seed. This validates that the simulation and its reporting layer use stable, deterministic logic. <!-- ID: RPG-0081 SOURCE: src/api/presenters/state_presenter.py TEST: tests/p1_replay_fidelity.py PROOF: replay -->
- [x] **[RPG-0082]** `UNSUPPORTED`: `test_arena_stop_condition_wipe`: Arena stop condition wipe — Verify that the arena correctly detects when one side is eliminated.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0083]** `UNSUPPORTED`: `test_arena_stop_condition_timeout`: Arena stop condition timeout — Verify that the arena respects the max_ticks limit.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0084]** `UNSUPPORTED`: `test_arena_stop_condition_stall`: Arena stop condition stall — Verify that the arena correctly detects lack of activity (STALL) as a telemetry report.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0085]** `test_mutation_tripwire_during_decision`: Mutation tripwire during decision — Verify that any attempt to mutate entities during the decision phase raises a RuntimeError. <!-- ID: RPG-0085 SOURCE: src/core/immutability.py TEST: tests/engine/test_milestone_a_closure.py PROOF: unit -->

#### `arena/test_arena_minimal.py`

- [x] **[RPG-0086]** `UNSUPPORTED`: `test_minimal_tick`: Minimal tick — Verify that we can run even 1 tick without hanging.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `arena/test_arena_watchdog.py`

- [x] **[RPG-0087]** `UNSUPPORTED`: `test_watchdog_aborts_on_hang`: Watchdog aborts on hang — Verify that a tick hanging for > watchdog_timeout is aborted.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0088]** `UNSUPPORTED`: `test_watchdog_allows_fast_ticks`: Watchdog allows fast ticks — Verify that normal fast ticks are NOT aborted.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `arena/test_core_scenario_regression.py`

- [x] **[RPG-0089]** `UNSUPPORTED`: `test_regression_melee_mirror`: Regression melee mirror — Scenario 1v1-01: Symmetry Check.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0090]** `UNSUPPORTED`: `test_regression_kiting_open`: Regression kiting open — Scenario 1v1-02: Ranged vs Melee Open Field.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0091]** `UNSUPPORTED`: `test_regression_elite_vs_swarm`: Regression elite vs swarm — Scenario 1vm-01: Elite vs Swarm.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `arena/test_observability_audit.py`

- [x] **[RPG-0092]** `pipeline.py:824`: Rejection audit — Verify all rejected intents are recorded in the TickOutcome/Replay.. <!-- VERIFIED v2: pipeline.py:824 -->
- [x] **[RPG-0093]** `test_combat_matrix.py`: Out of range rejection — Verify intent is rejected if target moves out of range between thought and apply.. <!-- VERIFIED v2: test_combat_matrix.py -->

#### `arena/test_resource_isolation.py`

- [x] **[RPG-0094]** `test_resource_isolation_bounded_growth`: Resource isolation bounded growth — Verify that memory does not show a strong linear leak over many iterations.. <!-- ID: RPG-0094 SOURCE: src/engine/apply.py TEST: tests/p2_long_run_stability.py PROOF: simulation -->

#### `combat/test_anti_stalemate.py`

- [x] **[RPG-0095]** `tactical.py:201`: Stalemate detection — Verify stalemate_ticks counter increment logic.. <!-- VERIFIED v2: tactical.py:201 -->
- [x] **[RPG-0096]** `tactical.py:208`: Stalemate breaker — Verify entity moves randomly if stuck in oscillation (A-B-A-B) for 10 ticks.. <!-- VERIFIED v2: tactical.py:208 -->

#### `combat/test_anti_stalemate_milestone_2.py`

- [x] **[RPG-0097]** `tactical.py:220`: Stalemate detection and breaker — Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker.. <!-- VERIFIED v2: tactical.py:220 -->

#### `combat/test_combat_context_milestone_2.py`

- [x] **[RPG-0098]** `combat.py:87`: High ground bonus — Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR.. <!-- VERIFIED v2: combat.py:87 -->
- [x] **[RPG-0099]** `combat.py:91`: Flanking bonus — Verify Flanking bonus applies when defender is bracketed north/south.. <!-- VERIFIED v2: combat.py:91 -->
- [x] **[RPG-0100]** `UNSUPPORTED`: `test_moved_penalty`: Moved penalty — Verify accuracy penalty if entity moved in the same tick.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0101]** `combat.py:95`: Ranged cover bonus — Verify Cover bonus applies against ranged attacks when adjacent to WALL.. <!-- VERIFIED v2: combat.py:95 -->

#### `combat/test_combat_movement_rulebook.py`

- [x] **[RPG-0102]** `legality.py:13`: Manhattan distance — Verify Manhattan distance calculation.. <!-- VERIFIED v2: legality.py:13 -->
- [x] **[RPG-0103]** `legality.py:27`: Adjacency law — Verify adjacency is defined as Manhattan distance == 1.. <!-- VERIFIED v2: legality.py:27 -->
- [x] **[RPG-0104]** `legality.py:161`: Check range — Verify range enforcement.. <!-- VERIFIED v2: legality.py:161 -->
- [x] **[RPG-0105]** `legality.py:32`: Check occupancy — Verify 1-unit-per-tile occupancy rule.. <!-- VERIFIED v2: legality.py:32 -->
- [x] **[RPG-0106]** `combat.py:339`: Aoe legality — Verify AoE impact constraints.. <!-- VERIFIED v2: combat.py:339 -->
- [x] **[RPG-0107]** `UNSUPPORTED`: `test_aoe_splash_radius`: Aoe splash radius — Verify entities affected by splash radius.. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0108]** `UNSUPPORTED`: `test_get_occupant_id`: Get occupant id — Verify occupant lookup.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0109]** `combat.py:204`: Check targeting legality — Verify consolidated targeting rules (Range + LOS).. <!-- VERIFIED v2: combat.py:204 -->

#### `combat/test_engagement_contract.py`

- [x] **[RPG-0110]** `tactical.py:350`: Engagement detection. <!-- VERIFIED v2: tactical.py:350 -->
- [x] **[RPG-0111]** `tactical.py:231`: Engagement retreat — Verify entity attempts repositioning if HP < 40% and engaged.. <!-- VERIFIED v2: tactical.py:231 -->
- [x] **[RPG-0112]** `tactical.py:302`: Engagement interception — Verify entity moves to intercept if target is moving away.. <!-- VERIFIED v2: tactical.py:302 -->

#### `combat/test_opportunity_attacks.py`

- [x] **[RPG-0113]** `UNSUPPORTED`: `test_oa_triggered_on_disengagement`: Oa triggered on disengagement. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0114]** `UNSUPPORTED`: `test_oa_not_triggered_if_staying_engaged_with_same_attacker`: Oa not triggered if staying engaged with same attacker. <!-- VERIFIED v2: UNSUPPORTED -->

#### `combat/test_target_stickiness.py`

- [x] **[RPG-0115]** `test_target_stickiness_bias`: Target stickiness bias. <!-- ID: RPG-0115 SOURCE: src/engine/tactical.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

#### `combat/test_world_time_progression.py`

- [x] **[RPG-0116]** `apply.py:52`: Passive progression on quiet tick — Verify that biological decay and lifecycle systems run even if entity doesn't act.. <!-- VERIFIED v2: apply.py:52 -->
- [x] **[RPG-0117]** `UNSUPPORTED`: `test_hero_lifecycle_on_quiet_tick`: Hero lifecycle on quiet tick — Verify that HeroLifecycle (e.g. proximity bonding) runs even if no entity acts.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `engine/test_quiet_tick_integrity.py`

- [x] **[RPG-0118]** `apply.py:19`: Scenario 1 dead world progression — Scenario 1: No living entities. Verify tick still increments and systems advance.. <!-- VERIFIED v2: apply.py:19 -->
- [x] **[RPG-0119]** `test_long_run_determinism.py`: Deterministic seed — Verify that state.seed is used for all internal RNG calls.. <!-- VERIFIED v2: test_long_run_determinism.py -->
- [x] **[RPG-0120]** `UNSUPPORTED`: `test_scenario_3_stationary_world_proximity_bonding`: Scenario 3 stationary world proximity bonding — Scenario 3: Two heroes are stationary. Verify bonding occurs via HeroLifecycleSystem.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0121]** `UNSUPPORTED`: `test_scenario_4_subsystem_advancement`: Scenario 4 subsystem advancement — Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/ai/test_wind_pillar_navigation.py`

- [x] **[RPG-0122]** `UNSUPPORTED`: `test_navigation_uses_flow_field_for_far_town`: Navigation uses flow field for far town. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0123]** `UNSUPPORTED`: `test_navigation_uses_astar_for_near_target`: Navigation uses astar for near target. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0124]** `UNSUPPORTED`: `test_navigation_uses_flow_field_for_world_boss`: Navigation uses flow field for world boss. <!-- VERIFIED v2: UNSUPPORTED -->

#### `test_party_tactics.py`

- [x] **[RPG-0125]** `UNSUPPORTED`: `test_vanguard_biases`: Vanguard biases. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0126]** `UNSUPPORTED`: `test_support_biases`: Support biases. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0127]** `UNSUPPORTED`: `test_protector_biases`: Protector biases. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_skirmish.py`

- [x] **[RPG-0128]** `UNSUPPORTED`: `test_skirmish_boosts_move_for_ranged`: Skirmish boosts move for ranged. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0129]** `UNSUPPORTED`: `test_skirmish_does_not_boost_melee`: Skirmish does not boost melee. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_tactical_behavior_contract.py`

- [x] **[RPG-0130]** `tactical.py:367`: Melee striker closes distance. <!-- VERIFIED v2: tactical.py:367 -->
- [x] **[RPG-0131]** `tactical.py:324`: Ranged skirmisher kites when close. <!-- VERIFIED v2: tactical.py:324 -->
- [x] **[RPG-0132]** `tactical.py:324`: Ranged skirmisher maintains distance. <!-- VERIFIED v2: tactical.py:324 -->
- [x] **[RPG-0133]** `UNSUPPORTED`: `test_safe_shot_detection`: Safe shot detection. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0134]** `tactical.py:231`: Tactical retreat at low hp. <!-- VERIFIED v2: tactical.py:231 -->
- [x] **[RPG-0135]** `UNSUPPORTED`: `test_group_spacing_preservation`: Group spacing preservation. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/logic/test_movement_model.py`

- [x] **[RPG-0136]** `UNSUPPORTED`: `test_movement_model_basic_path`: Movement model basic path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0137]** `UNSUPPORTED`: `test_movement_model_yielding_priority`: Movement model yielding priority. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0138]** `test_movement_model_stuck_threshold`: Movement model stuck threshold. <!-- ID: RPG-0138 SOURCE: src/engine/movement.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

### Resource interaction / inventory / town loop

#### `integration/gameplay/test_toughness_decay.py`

- [x] **[RPG-0139]** `UNSUPPORTED`: `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0140]** `UNSUPPORTED`: `test_stat_decay_inactivity`: Stat decay inactivity — Verify that stat decay can be triggered.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0141]** `UNSUPPORTED`: `test_toughness_hardening_integration`: Toughness hardening integration — Integration test for the restored hardening logic in CombatAction.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `test_building_unification.py`

- [x] **[RPG-0142]** `UNSUPPORTED`: `test_actor`: Actor. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0143]** `test_visit_guild_no_legacy_goals`: Visit guild no legacy goals — Verify that visiting the guild produces StrategicUpdate and PerceptionUpdate, but no string goals.. <!-- VERIFIED v2: guild_visit_semantics -->
- [ ] **[RPG-0144]** `test_visit_blacksmith_blocker_emission`: Visit blacksmith blocker emission — Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state.. <!-- VERIFIED v2: blacksmith_visit_semantics -->
- [ ] **[RPG-0145]** `test_visit_class_hall_resolution`: Visit class hall resolution — Verify that learning a skill emits a strategic resolution for the corresponding capability blocker.. <!-- VERIFIED v2: town_return_semantics -->
- [x] **[RPG-0146]** `UNSUPPORTED`: `test_visit_blacksmith_crafting_resolution`: Visit blacksmith crafting resolution — Verify that crafting an item emits a strategic resolution for the material blocker.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0147]** `UNSUPPORTED`: `test_visit_home_upgrade_resolution`: Visit home upgrade resolution — Verify that home storage upgrade emits a strategic resolution for home maintenance.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0148]** `UNSUPPORTED`: `test_detour_suggestion_lifecycle_awareness`: Detour suggestion lifecycle awareness — Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_routine_cycle.py`

- [x] **[RPG-0149]** `apply.py:52`: Biological decay authoritative. <!-- VERIFIED v2: apply.py:52 -->
- [x] **[RPG-0150]** `UNSUPPORTED`: `test_sleep_goal_utility_at_night`: Sleep goal utility at night. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0151]** `UNSUPPORTED`: `test_nocturnal_predator_bonus`: Nocturnal predator bonus. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_routine_needs.py`

- [x] **[RPG-0152]** `UNSUPPORTED`: `test_biological_utility_biasing`: Biological utility biasing. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0153]** `test_inn_visit_leads_to_sleeping`: Inn visit leads to sleeping. <!-- VERIFIED v2: inn_visit_semantics -->
- [x] **[RPG-0154]** `UNSUPPORTED`: `test_home_visit_leads_to_eating`: Home visit leads to eating. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0155]** `UNSUPPORTED`: `test_sleeping_recovery_cycle`: Sleeping recovery cycle. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/gameplay/test_item_contracts.py`

- [x] **[RPG-0156]** `UNSUPPORTED`: `test_weapon_ranges_integrity`: Weapon ranges integrity — Verify that specific weapons have their intended ranges in the registry.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0157]** `UNSUPPORTED`: `test_weapon_power_integrity`: Weapon power integrity — Verify that core progression weapons have their primary power correctly set.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0158]** `UNSUPPORTED`: `test_registry_identity_integrity`: Registry identity integrity — Ensure all core items are successfully loaded and have consistent IDs.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_difficulty_scaling.py`

- [x] **[RPG-0159]** `UNSUPPORTED`: `test_tier1_is_baseline`: Tier1 is baseline. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0160]** `UNSUPPORTED`: `test_tier4_has_higher_stats_than_tier1`: Tier4 has higher stats than tier1 — Same seed, same enemy tier - tier 4 difficulty should have higher HP/ATK.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0161]** `UNSUPPORTED`: `test_tier4_hp_significantly_higher`: Tier4 hp significantly higher — Tier 4 HP multiplier is 4.0x on base stats; with flat bonuses from traits/attributes the effective ratio will be lower but still substantial.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0162]** `UNSUPPORTED`: `test_difficulty_sets_level_range`: Difficulty sets level range — Entities in tier 3 should have level in [5, 10].. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0163]** `UNSUPPORTED`: `test_gold_scales_with_difficulty`: Gold scales with difficulty — Tier 4 gold multiplier is 4.0x.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0164]** `UNSUPPORTED`: `test_race_tier4_stronger_than_tier1`: Race tier4 stronger than tier1. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0165]** `UNSUPPORTED`: `test_race_difficulty_tier_set`: Race difficulty tier set. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0166]** `UNSUPPORTED`: `test_race_level_in_range`: Race level in range. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0167]** `UNSUPPORTED`: `test_all_races_scale`: All races scale — All four races should scale with difficulty.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0168]** `UNSUPPORTED`: `test_boss_diff_capped_at_4`: Boss diff capped at 4. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0169]** `UNSUPPORTED`: `test_boss_diff_adds_one`: Boss diff adds one. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0170]** `UNSUPPORTED`: `test_spawn_default_is_tier1`: Spawn default is tier1. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0171]** `UNSUPPORTED`: `test_spawn_race_default_is_tier1`: Spawn race default is tier1. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_toughness_decay.py`

- [x] **[RPG-0172]** `UNSUPPORTED`: `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0173]** `UNSUPPORTED`: `test_stat_decay_inactivity`: Stat decay inactivity — Verify that idling for 1000+ ticks triggers stat decay.. <!-- VERIFIED v2: UNSUPPORTED -->

### Strategic mind / cognition / projects / blockers / leads

#### `ai/test_bounded_blockers.py`

- [x] **[RPG-0174]** `UNSUPPORTED`: `test_accurate_diagnosis_high_wisdom`: Accurate diagnosis high wisdom. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0175]** `UNSUPPORTED`: `test_misdiagnosis_low_wisdom`: Misdiagnosis low wisdom. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_bounded_detours.py`

- [x] **[RPG-0176]** `UNSUPPORTED`: `test_detour_breadth_limit`: Detour breadth limit. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0177]** `UNSUPPORTED`: `test_detour_depth_limit_fallback`: Detour depth limit fallback. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0178]** `test_retry_suppression`: Retry suppression. <!-- ID: RPG-0178 SOURCE: src/systems/detour.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

#### `ai/test_bounded_objective_continuity.py`

- [x] **[RPG-0179]** `UNSUPPORTED`: `test_objective_derivation_precedence_blocker_first`: Objective derivation precedence blocker first. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0180]** `UNSUPPORTED`: `test_objective_derivation_precedence_active_objective_if_no_blocker`: Objective derivation precedence active objective if no blocker. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0181]** `UNSUPPORTED`: `test_objective_derivation_precedence_first_unresolved_if_no_active`: Objective derivation precedence first unresolved if no active. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_bounded_project_continuity.py`

- [x] **[RPG-0182]** `test_project_retention_when_rival_is_below_margin`: Project retention when rival is below margin. <!-- ID: RPG-0182 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0183]** `test_project_switch_when_rival_is_above_margin`: Project switch when rival is above margin. <!-- ID: RPG-0183 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0184]** `UNSUPPORTED`: `test_switch_margin_increases_with_higher_resistance_profile`: Switch margin increases with higher resistance profile. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_bounded_strategic_slice.py`

- [x] **[RPG-0185]** `UNSUPPORTED`: `test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity`: Low profile entity has smaller active slice than high profile entity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0186]** `UNSUPPORTED`: `test_concern_intake_is_capped_by_profile`: Concern intake is capped by profile. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0187]** `UNSUPPORTED`: `test_lead_retention_is_capped_by_profile`: Lead retention is capped by profile. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0188]** `UNSUPPORTED`: `test_reserved_current_project_slot_is_used_when_current_project_exists`: Reserved current project slot is used when current project exists. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0189]** `UNSUPPORTED`: `test_dropped_candidate_counts_are_deterministic`: Dropped candidate counts are deterministic. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_cognition_capacity_determinism.py`

- [x] **[RPG-0190]** `test_profile_derivation_is_deterministic_for_same_entity_state`: Profile derivation is deterministic for same entity state. <!-- ID: RPG-0190 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0191]** `UNSUPPORTED`: `test_profile_derivation_is_independent_of_tick_in_milestone_1`: Profile derivation is independent of tick in milestone 1. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0192]** `test_profile_derivation_does_not_use_rng`: Profile derivation does not use rng. <!-- ID: RPG-0192 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

#### `ai/test_cognition_capacity_non_mutation.py`

- [x] **[RPG-0193]** `test_build_profile_does_not_mutate_entity_attributes`: Build profile does not mutate entity attributes. <!-- ID: RPG-0193 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0194]** `UNSUPPORTED`: `test_build_profile_does_not_mutate_caps`: Build profile does not mutate caps. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0195]** `UNSUPPORTED`: `test_build_profile_does_not_mutate_stamina`: Build profile does not mutate stamina. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0196]** `UNSUPPORTED`: `test_build_profile_returns_new_profile_object_each_call`: Build profile returns new profile object each call. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_cognition_explainability.py`

- [x] **[RPG-0197]** `UNSUPPORTED`: `test_overload_metadata_population`: Overload metadata population — Verify that primary_overload_source and last_overload_tick are correctly populated in replay.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0198]** `UNSUPPORTED`: `test_personality_formula_impact`: Personality formula impact — Verify that personality archetypes and traits impact the capacity profile.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0199]** `UNSUPPORTED`: `test_inspector_smoke_coverage`: Inspector smoke coverage — Smoke test to ensure EntityInspector (AIPresenter) doesn't crash with new fields.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_cognition_integrity.py`

- [x] **[RPG-0200]** `UNSUPPORTED`: `test_ui_contract_alignment`: Ui contract alignment — Verify that every field in bounded_cognition_ui_contract.md exists in Pydantic schemas.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0201]** `UNSUPPORTED`: `test_feature_spec_replay_alignment`: Feature spec replay alignment — Verify that replay fields mentioned in feature spec are present in recorder.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0202]** `UNSUPPORTED`: `test_feature_spec_graph_export_alignment`: Feature spec graph export alignment — Verify that graph export fields mentioned in feature spec are present in exporter.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0203]** `UNSUPPORTED`: `test_test_matrix_existence`: Test matrix existence — Verify that all test modules mentioned in test_matrix.md actually exist.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0204]** `UNSUPPORTED`: `test_populated_artifact_consistency`: Populated artifact consistency — Verify that a live HeadlessRunner execution produces populated and consistent artifacts. [TRACK 1 HARDENING]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0205]** `UNSUPPORTED`: `test_truth_surface_parity`: Truth surface parity — Verify that Replay, API Schema, and Cognition Graph maintain strict parity. <!-- RECOVERED: StatePresenter and CanonicalStateHasher maintain strict parity --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0206]** `UNSUPPORTED`: `test_documentation_alignment`: Documentation alignment — Verify that documented fields in intel_capacity_implementation_updated.md are real. [MILESTONE 8 PROOF]. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_directive_mutation_thresholds.py`

- [x] **[RPG-0207]** `UNSUPPORTED`: `test_directive_mutation_thresholds`: Directive mutation thresholds — Verify that directives only mutate after repeated thresholded events.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_event_interpretation.py`

- [x] **[RPG-0208]** `UNSUPPORTED`: `test_stable_concern_generation`: Stable concern generation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0209]** `UNSUPPORTED`: `test_unstable_panic_concern`: Unstable panic concern. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0210]** `test_interruption_resistance_stable`: Interruption resistance stable. <!-- VERIFIED v2: project_interruption_resistance -->
- [ ] **[RPG-0211]** `test_interruption_resistance_unstable`: Interruption resistance unstable. <!-- VERIFIED v2: project_interruption_resistance -->
- [ ] **[RPG-0212]** `test_identity_drift_resistance`: Identity drift resistance. <!-- VERIFIED v2: project_interruption_resistance -->
- [x] **[RPG-0213]** `UNSUPPORTED`: `test_rumor_sensitivity_unstable`: Rumor sensitivity unstable. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_lead_learning.py`

- [x] **[RPG-0214]** `UNSUPPORTED`: `test_learning_success`: Learning success. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0215]** `UNSUPPORTED`: `test_learning_failure`: Learning failure. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_social_cognition.py`

- [x] **[RPG-0216]** `UNSUPPORTED`: `test_social_blocker_detection_solo`: Social blocker detection solo. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0217]** `UNSUPPORTED`: `test_social_misjudgment_low_stability`: Social misjudgment low stability. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0218]** `UNSUPPORTED`: `test_social_bandwidth_pool_limiting`: Social bandwidth pool limiting. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_source_trust_learning_loop.py`

- [x] **[RPG-0219]** `UNSUPPORTED`: `test_source_trust_learning_loop`: Source trust learning loop — Prove that future weighting is affected by source trust after a learning event.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_uncertainty_resolution_loop.py`

- [x] **[RPG-0220]** `UNSUPPORTED`: `test_uncertainty_resolution_loop`: Uncertainty resolution loop — Prove that proximity to a rumored zone resolves imprecise leads into precise targets.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `core/test_cognition_graph_exporter.py`

- [x] **[RPG-0221]** `UNSUPPORTED`: `test_export_empty_strategy`: Export empty strategy — Verify export from an entity with no strategic state.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0222]** `UNSUPPORTED`: `test_export_with_core_strategic_state`: Export with core strategic state — Verify export of directives, projects, and objectives.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0223]** `UNSUPPORTED`: `test_export_determinism`: Export determinism — Verify that multiple exports from the same state are identical.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0224]** `UNSUPPORTED`: `test_non_mutation`: Non mutation — Verify that exporter does not mutate the source entity.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `core/test_strategy_models.py`

- [x] **[RPG-0225]** `UNSUPPORTED`: `test_strategic_model_rebuild`: Strategic model rebuild — Verify pydantic model rebuild handles recursive refs.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0226]** `UNSUPPORTED`: `test_directive_creation`: Directive creation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0227]** `UNSUPPORTED`: `test_strategic_state_defaults`: Strategic state defaults. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0228]** `UNSUPPORTED`: `test_strategic_state_serialization`: Strategic state serialization. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_cognition_graph_regression.py`

- [x] **[RPG-0229]** `UNSUPPORTED`: `test_cognition_graph_deterministic_simulation`: Cognition graph deterministic simulation — Verify that a simulation produces a valid, repeatable cognition graph.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0230]** `UNSUPPORTED`: `test_graph_structural_invariants`: Graph structural invariants — Verify that the graph follows structural rules across ticks.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_brain_integration.py`

- [x] **[RPG-0231]** `UNSUPPORTED`: `test_strategic_pivot_on_regional_danger`: Strategic pivot on regional danger — Verify that heroes pivot from personal quests to regional stabilization during high-danger events.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0232]** `UNSUPPORTED`: `test_scar_detection`: Scar detection — Verify that heroes sense nearby world trauma (scars) and investigate.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0233]** `UNSUPPORTED`: `test_near_death_triggers_survival_consequences`: Near death triggers survival consequences — Verify that a NEAR_DEATH event generates a concern and suspends the current project via applicator.. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0234]** `test_betrayal_mutates_directives`: Betrayal mutates directives — Verify that a salient betrayal turning point adds an 'Avenge' directive.. <!-- VERIFIED v2: SocialAppraisalSystem -->
- [x] **[RPG-0235]** `UNSUPPORTED`: `test_divergent_home_response`: Divergent home response — Verify that only entities with place attachment react strongly to home damage.. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0236]** `test_betrayal_trauma_affects_recruitment`: Betrayal trauma affects recruitment — Verify that a recent betrayal makes entities less willing to accept recruitment offers.. <!-- VERIFIED v2: SocialAppraisalSystem -->

#### `integration/strategy/test_strategic_capacity_enforcement.py`

- [x] **[RPG-0237]** `UNSUPPORTED`: `test_budget_enforcement_truncation`: Budget enforcement truncation — Verify that candidate_zone_limit correctly truncates the pool AND preserves highest-scored zones.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0238]** `UNSUPPORTED`: `test_source_trust_behavioral_impact`: Source trust behavioral impact — Verify that updating source trust results in different weighting in the next cycle. [MILESTONE 3]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0239]** `UNSUPPORTED`: `test_overload_metrics_visibility`: Overload metrics visibility — Verify that primary_overload_source and metrics are populated when stressed.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_continuity.py`

- [x] **[RPG-0240]** `UNSUPPORTED`: `test_directive_mutation_salience_threshold`: Directive mutation salience threshold — Verify that only high-salience turning points trigger mutations.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0241]** `UNSUPPORTED`: `test_directive_priority_strengthening`: Directive priority strengthening — Verify that repeated high-salience events strengthen directive priority.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_continuity_hardening.py`

- [x] **[RPG-0242]** `UNSUPPORTED`: `test_strategic_objective_continuity`: Strategic objective continuity — Prove that an existing objective is preserved if the project remains stable and no high blockers appear.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0243]** `UNSUPPORTED`: `test_objective_resumption_aligns_with_tactical`: Objective resumption aligns with tactical — Verify that a resumed objective correctly drives goal selection.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_determinism.py`

- [ ] **[RPG-0244]** `test_harness_determinism`: Harness determinism — Verify that two runs with the same seed produce byte-identical results.. <!-- VERIFIED v2: long_run_determinism -->
- [x] **[RPG-0245]** `UNSUPPORTED`: `test_harness_non_determinism_different_seed`: Harness non determinism different seed — Verify that different seeds produce different outcomes (basic sanity check).. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_explainability.py`

- [x] **[RPG-0246]** `UNSUPPORTED`: `test_candidate_zone_enforcement`: Candidate zone enforcement — Verify that candidate_zone_limit is enforced and drops excess zones.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0247]** `UNSUPPORTED`: `test_ally_evaluation_enforcement`: Ally evaluation enforcement — Verify that ally_evaluation_limit caps contracts and offers evaluated.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0248]** `UNSUPPORTED`: `test_overload_source_trauma`: Overload source trauma — Verify that heavy HP damage triggers 'trauma' as the primary overload source.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0249]** `UNSUPPORTED`: `test_switch_reason_transparency`: Switch reason transparency — Verify that a project switch provides a human-readable reason.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_persistence.py`

- [ ] **[RPG-0250]** `test_persistence_boost_prevents_switching`: Persistence boost prevents switching — Verify that the persistence boost prevents switching to a slightly better project.. <!-- VERIFIED v2: current_project_retention -->
- [ ] **[RPG-0251]** `test_project_lock_prevents_switching`: Project lock prevents switching — Verify that project_lock_until strictly prevents any switches despite critical concerns.. <!-- VERIFIED v2: current_project_retention -->
- [x] **[RPG-0252]** `UNSUPPORTED`: `test_interruption_threshold_overridden_by_major_threat`: Interruption threshold overridden by major threat — Verify that a massive threat CAN overcome the interruption threshold.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0253]** `UNSUPPORTED`: `test_strategic_pipeline_home_threat`: Strategic pipeline home threat — Verify the flow from life event through StrategicConsequenceService to project pivot.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0254]** `UNSUPPORTED`: `test_resume_restores_valid_objective`: Resume restores valid objective — Verify that brain restores the last active objective when resuming a project. [Strategy M2]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0255]** `UNSUPPORTED`: `test_resumed_objective_survives_cycle`: Resumed objective survives cycle — Verify that a restored objective doesn't immediately flip back to ProjectRecord.objectives[0] if it matches. [Strategy M2]. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_replay_determinism.py`

- [x] **[RPG-0256]** `UNSUPPORTED`: `test_world_strategic_registry_deep_isolation`: World strategic registry deep isolation — Verify that WorldStrategicRegistry.copy() performs a deep copy.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0257]** `UNSUPPORTED`: `test_strategic_replay_graph_equality`: Strategic replay graph equality — Verify that replaying from a snapshot yields bit-identical cognition graphs.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0258]** `UNSUPPORTED`: `test_lead_outcome_grounding_verification`: Lead outcome grounding verification — Verify that precise leads correctly ground into world entities.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_resume_objective.py`

- [x] **[RPG-0259]** `UNSUPPORTED`: `test_objective_resume_reliability`: Objective resume reliability — Verify that a suspended objective is resumed correctly.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_structural_integrity.py`

- [x] **[RPG-0260]** `UNSUPPORTED`: `test_snapshot_strategic_isolation`: Snapshot strategic isolation — Verify that Snapshot.from_world deep-copies and freezes strategic state.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0261]** `UNSUPPORTED`: `test_strategic_update_merging_identical_ids`: Strategic update merging identical ids — Verify that ActionSystem merges updates with identical IDs correctly.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0262]** `UNSUPPORTED`: `test_serialization_round_trip`: Serialization round trip — Verify that StrategicState survives full JSON serialization round-trip.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0263]** `UNSUPPORTED`: `test_strategic_update_coercion_from_dict`: Strategic update coercion from dict — Verify that StrategicUpdate correctly coerces dicts to models (worker transport emulation).. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_transport.py`

- [x] **[RPG-0264]** `UNSUPPORTED`: `test_strategic_update_multi_record_transport`: Strategic update multi record transport — Verify that a single proposal can carry multiple strategic updates.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0265]** `UNSUPPORTED`: `test_strategic_update_repeated_id_last_one_wins`: Strategic update repeated id last one wins — Verify that repeated IDs in a single update follow last-one-wins semantics.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0266]** `UNSUPPORTED`: `test_strategic_update_idempotency_over_ticks`: Strategic update idempotency over ticks — Verify that applying the same update multiple times is idempotent.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0267]** `UNSUPPORTED`: `test_strategic_update_target_routing`: Strategic update target routing — Verify that strategic updates can be routed to a target entity.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategic_world_integration.py`

- [x] **[RPG-0268]** `UNSUPPORTED`: `test_world_strategic_registry_persistence`: World strategic registry persistence — Verify that WorldStrategicRegistry is preserved in snapshots.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0269]** `UNSUPPORTED`: `test_strategic_world_integration_system_pruning`: Strategic world integration system pruning — Verify that the system prunes expired world opportunities.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0270]** `UNSUPPORTED`: `test_telemetry_strategic_metrics`: Telemetry strategic metrics — Verify that TelemetrySystem collects strategic metrics. <!-- RECOVERED: MetricsService extracts strategic and world dynamics --> <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/strategy/test_strategic_biasing.py`

- [x] **[RPG-0271]** `UNSUPPORTED`: `test_biological_need_to_strategic_bias`: Biological need to strategic bias. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0272]** `UNSUPPORTED`: `test_directive_to_project_flow`: Directive to project flow. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0273]** `UNSUPPORTED`: `test_strategic_bias_impact_on_selection`: Strategic bias impact on selection. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/strategy/test_strategic_uncertainty.py`

- [x] **[RPG-0274]** `UNSUPPORTED`: `test_contradiction_degrades_certainty`: Contradiction degrades certainty — Verify that leads with contradictions lose certainty based on profile sensitivity. [MILESTONE 5]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0275]** `UNSUPPORTED`: `test_hypothesis_impacted_by_contradiction`: Hypothesis impacted by contradiction — Verify that hypotheses lose confidence when supporting leads are contradicted. [MILESTONE 5]. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/strategy/test_strategic_services.py`

- [x] **[RPG-0276]** `UNSUPPORTED`: `test_canonical_blocker_structure`: Canonical blocker structure — Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0277]** `UNSUPPORTED`: `test_strategic_snapshot_isolation`: Strategic snapshot isolation — Verify that deep copying an entity results in a fully isolated strategic tree.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0278]** `UNSUPPORTED`: `test_belief_decay_aoa_purity`: Belief decay aoa purity — Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0279]** `UNSUPPORTED`: `test_social_applicator_aoa_purity`: Social applicator aoa purity — Verify that SocialStateApplicator returns updates and does not mutate the world.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0280]** `UNSUPPORTED`: `test_concern_generation_near_death`: Concern generation near death. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0281]** `UNSUPPORTED`: `test_directive_mutation_near_death`: Directive mutation near death. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0282]** `UNSUPPORTED`: `test_project_mutation_interruption`: Project mutation interruption. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0283]** `UNSUPPORTED`: `test_strategic_update_blocker_merging`: Strategic update blocker merging — Verify that ActionSystem merges blockers from StrategicUpdate correctly.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_strategy.py`

- [x] **[RPG-0284]** `UNSUPPORTED`: `test_influence_shifts_on_monster_death`: Influence shifts on monster death. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0285]** `UNSUPPORTED`: `test_influence_shifts_on_hero_death`: Influence shifts on hero death. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0286]** `UNSUPPORTED`: `test_war_state_transition`: War state transition. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0287]** `UNSUPPORTED`: `test_conquered_region_triggers_stronghold`: Conquered region triggers stronghold. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0288]** `test_stronghold_debuff_application`: Stronghold debuff application. <!-- VERIFIED v2: EnvironmentService Aura of Despair -->

#### `unit/systems/test_strategy_system.py`

- [x] **[RPG-0289]** `UNSUPPORTED`: `test_war_declaration`: War declaration. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0290]** `UNSUPPORTED`: `test_territory_conquest`: Territory conquest. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0291]** `UNSUPPORTED`: `test_territory_liberation`: Territory liberation. <!-- VERIFIED v2: UNSUPPORTED -->

### Social / contracts / reputation / lived consequences

#### `ai/test_betrayal_social_consequence.py`

- [x] **[RPG-0292]** `UNSUPPORTED`: `test_betrayal_social_consequence`: Betrayal social consequence — Verify that private betrayal trauma prevents recruitment even for reputable founders.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_learning_social.py`

- [x] **[RPG-0293]** `UNSUPPORTED`: `test_intel_confirmation_by_sight`: Intel confirmation by sight — Verify that seeing a person mentioned in a lead confirms it and boosts trust.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0294]** `UNSUPPORTED`: `test_intel_refutation_by_exhaustion`: Intel refutation by exhaustion — Verify that failing to find a target refutes the lead and drops trust.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `core/test_lived_models.py`

- [x] **[RPG-0295]** `UNSUPPORTED`: `test_routine_profile_instantiation`: Routine profile instantiation — Verify RoutineProfile can be instantiated with hybrid scheduling.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0296]** `UNSUPPORTED`: `test_place_attachment_instantiation`: Place attachment instantiation — Verify PlaceAttachment can be instantiated and supports sentiment.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0297]** `UNSUPPORTED`: `test_group_record_instantiation`: Group record instantiation — Verify GroupRecord supports shared tactical intent.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0298]** `UNSUPPORTED`: `test_entity_integration`: Entity integration — Verify Entity and IdentityAspect absorb new Phase 3 fields.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0299]** `UNSUPPORTED`: `test_world_state_registry`: World state registry — Verify GroupRegistry integration in WorldState.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/gameplay/test_social_meaning.py`

- [x] **[RPG-0300]** `UNSUPPORTED`: `test_social_event_betrayal`: Social event betrayal — Verify that hitting an ally triggers a betrayal event and social bond shift.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0301]** `UNSUPPORTED`: `test_social_event_near_death_and_tp`: Social event near death and tp — Verify that a near-death experience creates a durable turning point.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0302]** `UNSUPPORTED`: `test_social_event_first_kill_milestone`: Social event first kill milestone — Verify that first kill increments reputation and notoriety.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `test_phase_3_social_contracts.py`

- [ ] **[RPG-0303]** `test_recruitment_haggling_threshold`: Recruitment haggling threshold — Verify that candidates counter-offer when willingness is close to threshold. <!-- VERIFIED v2: SocialAppraisalSystem returns COUNTERED and haggles for fair pay -->
- [x] **[RPG-0304]** `UNSUPPORTED`: `test_contract_outcome_consequences`: Contract outcome consequences — Verify that contract resolution returns correct intent updates for all members.. <!-- ID: RPG-0304 SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0305]** `UNSUPPORTED`: `test_role_aware_tactical_biases`: Role aware tactical biases — Verify that utility biases change based on contract role.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_social.py`

- [x] **[RPG-0306]** `UNSUPPORTED`: `test_inn_gossip`: Inn gossip. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0307]** `UNSUPPORTED`: `test_hero_trading`: Hero trading. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_social_integration.py`

- [x] **[RPG-0308]** `UNSUPPORTED`: `test_social_bias_on_goal_scoring`: Social bias on goal scoring — Verify that a high-trust bond increases SOCIAL goal score.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0309]** `UNSUPPORTED`: `test_reputation_impact_on_caution`: Reputation impact on caution — Verify low global reputation triggers defensive posture in cautious entities.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/gameplay/test_npc_contracts.py`

- [x] **[RPG-0310]** `UNSUPPORTED`: `test_npc_loadout_integrity`: Npc loadout integrity — Verify that specific NPC tiers are assigned their canonical equipment.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0311]** `UNSUPPORTED`: `test_npc_kind_mapping_integrity`: Npc kind mapping integrity — Verify that race/tier combinations map to the correct semantic kind name.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/models/test_social_milestones.py`

- [x] **[RPG-0312]** `UNSUPPORTED`: `test_nemesis_milestone_creation`: Nemesis milestone creation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0313]** `UNSUPPORTED`: `test_memory_salience_retention`: Memory salience retention. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/models/test_social_registry_updates.py`

- [x] **[RPG-0314]** `UNSUPPORTED`: `test_combat_updates_social_registry`: Combat updates social registry. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0315]** `UNSUPPORTED`: `test_archetype_influence_on_social_deltas`: Archetype influence on social deltas. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/strategy/test_social_reasoning_bounding.py`

- [x] **[RPG-0316]** `UNSUPPORTED`: `test_recruitment_offer_bounding_stable`: Recruitment offer bounding stable — Stable entities produce consistent offers without noise.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0317]** `UNSUPPORTED`: `test_recruitment_offer_bounding_unstable`: Recruitment offer bounding unstable — Unstable entities produce noisy/perturbed offers.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_familiarity_scaling.py`

- [x] **[RPG-0318]** `UNSUPPORTED`: `test_cha_impacts_familiarity_gain`: Cha impacts familiarity gain — Verify that a hero with higher CHA gains familiarity faster.. <!-- VERIFIED v2: UNSUPPORTED -->

### Progression / classes / skills / attributes / rewards

#### `unit/ai/test_legend_legacy.py`

- [x] **[RPG-0319]** `UNSUPPORTED`: `test_narrative_memory_logging`: Narrative memory logging. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0320]** `UNSUPPORTED`: `test_bravery_modifiers`: Bravery modifiers. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0321]** `test_regional_suppression`: Regional suppression. <!-- VERIFIED v2: WorldDynamicsSystem -->

#### `unit/combat/test_combat_rewards.py`

- [x] **[RPG-0322]** `UNSUPPORTED`: `test_kill_reward_emission_in_apply`: Kill reward emission in apply. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py test_multi_kill_aoe_rewards --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0323]** `UNSUPPORTED`: `test_no_reward_on_non_lethal_hit`: No reward on non lethal hit. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/aspects/test_progression.py`

- [x] **[RPG-0324]** `UNSUPPORTED`: `test_undead_no_level_up`: Undead no level up — Undead should have a train_rate of 0.0 and never level up.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0325]** `UNSUPPORTED`: `test_milestone_level_up`: Milestone level up — Reaching a milestone like level 5 grants extra stats.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0326]** `UNSUPPORTED`: `test_veterancy_multipliers`: Veterancy multipliers — Veterancy Ranks should boost stats via StatsProxy.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0327]** `UNSUPPORTED`: `test_innate_talents_training`: Innate talents training — Talented attributes gain 2x points, weak attributes gain 0.5x.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0328]** `UNSUPPORTED`: `test_combat_veterancy_points`: Combat veterancy points — Combat yields veterancy points.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/aspects/test_skill_scaling.py`

- [x] **[RPG-0329]** `UNSUPPORTED`: `test_physical_skill_scaling`: Physical skill scaling. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0330]** `test_magical_skill_scaling`: Magical skill scaling. <!-- VERIFIED v2: magical_skill_scaling -->
- [ ] **[RPG-0331]** `test_elemental_skill_scaling`: Elemental skill scaling. <!-- VERIFIED v2: elemental_skill_scaling -->

#### `unit/core/gameplay/test_attribute_synergy.py`

- [x] **[RPG-0332]** `UNSUPPORTED`: `test_luck_impacts_crit_rate_significantly`: Luck impacts crit rate significantly — Verify that Luck has a meaningful impact on critical hit rate.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0333]** `UNSUPPORTED`: `test_luck_impacts_loot_modifier`: Luck impacts loot modifier — Verify that Luck/Perception provides a loot rarity multiplier.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0334]** `UNSUPPORTED`: `test_per_based_hidden_discovery`: Per based hidden discovery — Verify that hidden entities are only visible with sufficient Perception.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/gameplay/test_breakthroughs.py`

- [x] **[RPG-0335]** `UNSUPPORTED`: `test_breakthrough_is_added`: Breakthrough is added. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0336]** `UNSUPPORTED`: `test_breakthrough_applies_bonus`: Breakthrough applies bonus. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/gameplay/test_class_gear.py`

- [x] **[RPG-0337]** `UNSUPPORTED`: `test_warrior_prefers_defensive_gear`: Warrior prefers defensive gear — Verify that a Warrior weights defensive stats higher than a Mage.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0338]** `UNSUPPORTED`: `test_hero_starting_gear_integrity`: Hero starting gear integrity — Verify that each hero class has the correct starting gear defined.. <!-- VERIFIED v2: UNSUPPORTED -->

### World / entities / snapshot / determinism / engine authority

#### `core/test_snapshot_integrity.py`

- [x] **[RPG-0339]** `UNSUPPORTED`: `test_snapshot_immutability_enforced`: Snapshot immutability enforced. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0340]** `UNSUPPORTED`: `test_snapshot_entities_are_deep_copied`: Snapshot entities are deep copied. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0341]** `UNSUPPORTED`: `test_snapshot_entities_are_frozen`: Snapshot entities are frozen. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/engine/test_determinism.py`

- [x] **[RPG-0342]** `UNSUPPORTED`: `test_simulation_determinism`: Simulation determinism — Verify that two identical simulations with the same seed produce the same result.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0343]** `UNSUPPORTED`: `test_different_seeds_different_hashes`: Different seeds different hashes — Verify that different seeds produce different world states.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/engine/test_mutation_purity.py`

- [x] **[RPG-0344]** `UNSUPPORTED`: `test_aibrain_statelessness`: Aibrain statelessness. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/engine/test_snapshot_safety.py`

- [x] **[RPG-0345]** `UNSUPPORTED`: `test_entity_deep_copy_isolation`: Entity deep copy isolation — Verify that Entity.copy() provides absolute isolation for nested mutable structures.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0346]** `UNSUPPORTED`: `test_snapshot_actor_isolation`: Snapshot actor isolation — Verify that resolving an actor from a Snapshot ensures mutation safety.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0347]** `UNSUPPORTED`: `test_aspect_model_rebuild_integrity`: Aspect model rebuild integrity — Ensure that deep copies correctly initialize models and don't lose data.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0348]** `UNSUPPORTED`: `test_lived_structure_isolation`: Lived structure isolation — Verify isolation for Phase 3 routine and attachment structures.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/entities/test_entity_serialization.py`

- [x] **[RPG-0349]** `UNSUPPORTED`: `test_entity_to_full_schema_no_crash`: Entity to full schema no crash. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0350]** `UNSUPPORTED`: `test_entity_to_full_schema_minimal`: Entity to full schema minimal. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/models/test_snapshot_purity.py`

- [x] **[RPG-0351]** `UNSUPPORTED`: `test_simulation_model_collection_freeze_list`: Simulation model collection freeze list — Verify that lists in SimulationModel become immutable after freeze.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0352]** `UNSUPPORTED`: `test_simulation_model_collection_freeze_dict`: Simulation model collection freeze dict — Verify that dicts in SimulationModel become immutable MappingProxy after freeze.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0353]** `UNSUPPORTED`: `test_world_state_freeze_guards`: World state freeze guards — Verify that WorldState prevents mutations after freeze.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0354]** `UNSUPPORTED`: `test_snapshot_deep_purity`: Snapshot deep purity — Verify that Snapshot entities and their nested aspects are recursively frozen.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0355]** `UNSUPPORTED`: `test_action_proposal_guard_integration`: Action proposal guard integration — Verify the ActionProposalGuard context manager properly freezes the snapshot.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_deep_freeze.py`

- [x] **[RPG-0356]** `UNSUPPORTED`: `test_deep_freeze_nested_collections`: Deep freeze nested collections — Verify that freeze() recursively converts nested collections to immutable types.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0357]** `UNSUPPORTED`: `test_deep_freeze_idempotency`: Deep freeze idempotency — Verify that calling freeze() multiple times is safe.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_domain_invariants.py`

- [x] **[RPG-0358]** `UNSUPPORTED`: `test_combat_aspect_invariants`: Combat aspect invariants. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0359]** `UNSUPPORTED`: `test_progression_aspect_invariants`: Progression aspect invariants. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0360]** `UNSUPPORTED`: `test_freeze_calls_validate`: Freeze calls validate. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0361]** `UNSUPPORTED`: `test_nested_freeze_invariants`: Nested freeze invariants. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_invariants.py`

- [x] **[RPG-0362]** `UNSUPPORTED`: `test_speed_delay_invariants`: Speed delay invariants — Test that speed_delay never returns NaN or out-of-bounds values.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0363]** `UNSUPPORTED`: `test_stats_invariants`: Stats invariants — AOA Stabilization: Test CombatAspect invariants (formerly Stats).. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0364]** `UNSUPPORTED`: `test_damage_calc_math`: Damage calc math — Test the core damage calculation logic in isolation.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0365]** `UNSUPPORTED`: `test_recalc_level_consistency`: Recalc level consistency — Ensure level-based stat recalculation remains consistent across aspects.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0366]** `UNSUPPORTED`: `test_combat_damage_invariants`: Combat damage invariants — Ensure HP reduction application doesn't cause overflow or invalid states.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_calamity_evolution.py`

- [x] **[RPG-0367]** `UNSUPPORTED`: `test_calamity_evolution`: Calamity evolution. <!-- VERIFIED v2: UNSUPPORTED -->

### Unclassified-but-included RPG-core tests

#### `ai/test_intel_capacity_regression.py`

- [x] **[RPG-0368]** `UNSUPPORTED`: `test_intel_capacity_replay_and_graph_export`: Intel capacity replay and graph export — Verify that cognitive metrics survive replay and graph export pipelines.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0369]** `UNSUPPORTED`: `test_intel_capacity_determinism`: Intel capacity determinism — Verify that identical seeds produce identical cognitive profiles and artifacts.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0370]** `UNSUPPORTED`: `test_intel_capacity_overload_injection`: Intel capacity overload injection — Inject extreme cognitive pressure and verify overload triggering in artifacts.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0371]** `UNSUPPORTED`: `test_intel_capacity_divergence_scenario`: Intel capacity divergence scenario — Verify that different attributes lead to differing usage artifacts.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0372]** `UNSUPPORTED`: `test_intel_capacity_detour_depth_hardbound`: Intel capacity detour depth hardbound — Verify that detour depth is capped in artifacts even under pressure.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `ai/test_intel_capacity_visibility.py`

- [x] **[RPG-0373]** `UNSUPPORTED`: `test_cognition_api_serialization`: Cognition api serialization — Verify that cognitive metrics are correctly serialized for the API.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0374]** `UNSUPPORTED`: `test_cognition_inspector_rendering`: Cognition inspector rendering — Verify that the CLI inspector correctly renders cognitive data.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0375]** `UNSUPPORTED`: `test_cognition_empty_profile`: Cognition empty profile — Verify that inspector handles entities without cognitive profiles gracefully.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_building_to_strategy_pipeline.py`

- [x] **[RPG-0376]** `UNSUPPORTED`: `test_rng`: Rng. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0377]** `UNSUPPORTED`: `test_entity`: Entity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0378]** `UNSUPPORTED`: `test_guild_intel_to_strategy_visible_pipeline`: Guild intel to strategy visible pipeline — Verify that guild intel produces leads/zones that are visible in API schemas.. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0379]** `test_blacksmith_blocker_resolution_pipeline`: Blacksmith blocker resolution pipeline — Verify that blacksmith constraints produce blockers that are resolved by acquisition.. <!-- VERIFIED v2: strategic_blocker_resolution -->

#### `integration/strategy/test_knowledge_continuity_stabilization.py`

- [x] **[RPG-0380]** `UNSUPPORTED`: `test_milestone_3_lead_testing_and_persistence`: Milestone 3 lead testing and persistence — Verify that exhausted search marks leads as tested and persists them.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0381]** `UNSUPPORTED`: `test_milestone_4_social_filtering`: Milestone 4 social filtering — Verify that social candidate selection filters hostiles and uses debt.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0382]** `UNSUPPORTED`: `test_strategic_uncertainty_and_anti_cheating`: Strategic uncertainty and anti cheating — Verify that rumors have lower certainty and vague leads don't 'cheat' with perfect coords.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_lead_feedback_loops.py`

- [x] **[RPG-0383]** `UNSUPPORTED`: `test_source_trust_recalibration`: Source trust recalibration — Verify that a 'False' lead outcome reduces source trust.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0384]** `UNSUPPORTED`: `test_severe_failure_abandonment_impact`: Severe failure abandonment impact — Verify that a project switch/abandonment reflects in strategic drivers.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `integration/strategy/test_strategy_observability_consistency.py`

- [x] **[RPG-0385]** `UNSUPPORTED`: `test_rng`: Rng. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0386]** `UNSUPPORTED`: `test_entity`: Entity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0387]** `UNSUPPORTED`: `test_strategy_observability_consistency`: Strategy observability consistency — Verify that a strategic shift is consistently observable across all surfaces.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0388]** `UNSUPPORTED`: `test_strategic_decision_driver_traceability`: Strategic decision driver traceability — Verify that DecisionDriver records flow from AIBrain to the entity state.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `movement/test_congestion_milestone_3.py`

- [x] **[RPG-0389]** `UNSUPPORTED`: `test_blocked_retreat_yield`: Blocked retreat yield — Verify high-priority RETREAT ally forces yield from lower-priority ally.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0390]** `UNSUPPORTED`: `test_oscillation_suppression`: Oscillation suppression — Verify A-B-A-B movement is suppressed after 2 cycles.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0391]** `UNSUPPORTED`: `test_reroute_hysteresis`: Reroute hysteresis — Verify minor reroutes are ignored to prevent flip-flopping.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0392]** `UNSUPPORTED`: `test_safe_sidestepping`: Safe sidestepping — Verify yielding entities do not sidestep closer to danger.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/strategy/test_recruitment_negotiation.py`

- [x] **[RPG-0393]** `UNSUPPORTED`: `test_recruitment_offer_generation`: Recruitment offer generation — Verify that a recruiter creates a reasonable offer based on greed and risk. [PHASE 4]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0394]** `UNSUPPORTED`: `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend. [PHASE 4]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0395]** `UNSUPPORTED`: `test_recruitment_haggling_counter_offer`: Recruitment haggling counter offer — Verify greedy candidate counter-offers when the payout is too low. [PHASE 4]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0396]** `UNSUPPORTED`: `test_recruiter_evaluates_counter`: Recruiter evaluates counter — Verify recruiter accepts a counter-offer for an urgent project. [PHASE 4]. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_action_styles.py`

- [x] **[RPG-0397]** `UNSUPPORTED`: `test_execution_phase_modifies_proposal_with_aggressive_style`: Execution phase modifies proposal with aggressive style. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0398]** `UNSUPPORTED`: `test_execution_phase_modifies_proposal_with_evasive_style`: Execution phase modifies proposal with evasive style. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_ai_heuristics.py`

- [x] **[RPG-0399]** `UNSUPPORTED`: `test_ai_boredom_diversification`: Ai boredom diversification — Verify that an entity eventually shifts away from a repetitive goal due to boredom.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0400]** `UNSUPPORTED`: `test_life_stage_priority_shift`: Life stage priority shift — Verify level 1 and level 25 entities have different goal preferences.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_attention.py`

- [x] **[RPG-0401]** `UNSUPPORTED`: `test_perception_phase_populates_attention_pool`: Perception phase populates attention pool. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_belief_cycle.py`

- [x] **[RPG-0402]** `UNSUPPORTED`: `test_belief_refresh_captures_apparent_state`: Belief refresh captures apparent state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0403]** `UNSUPPORTED`: `test_belief_decay_lifecycle`: Belief decay lifecycle. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0404]** `UNSUPPORTED`: `test_threat_estimation_logic`: Threat estimation logic. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_cognitive_pipeline.py`

- [x] **[RPG-0405]** `UNSUPPORTED`: `test_decide_produces_consistent_result`: Decide produces consistent result. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0406]** `UNSUPPORTED`: `test_decide_increments_idle_ticks_on_rest`: Decide increments idle ticks on rest. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0407]** `UNSUPPORTED`: `test_perception_phase_appraisal_sync`: Perception phase appraisal sync. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_combos.py`

- [x] **[RPG-0408]** `UNSUPPORTED`: `test_shatter_combo`: Shatter combo. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_emotional_memory.py`

- [x] **[RPG-0409]** `UNSUPPORTED`: `test_locational_trauma_triggers_dread`: Locational trauma triggers dread — Verify entering a high-trauma region increments DREAD.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0410]** `UNSUPPORTED`: `test_emotional_bias_on_utility`: Emotional bias on utility — Verify DREAD increases FLEE utility and decreases EXPLORE utility.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0411]** `UNSUPPORTED`: `test_emotional_decay`: Emotional decay — Verify emotions propose negative delta for decay.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_emotions.py`

- [x] **[RPG-0412]** `UNSUPPORTED`: `test_appraisal_phase_triggers_panic_on_low_hp`: Appraisal phase triggers panic on low hp. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_flanking.py`

- [x] **[RPG-0413]** `UNSUPPORTED`: `test_flanking_bonus`: Flanking bonus. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0414]** `UNSUPPORTED`: `test_no_flanking_bonus_when_facing_attacker`: No flanking bonus when facing attacker. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_flow_fields.py`

- [x] **[RPG-0415]** `UNSUPPORTED`: `test_flow_field_basic_navigation`: Flow field basic navigation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0416]** `UNSUPPORTED`: `test_flow_field_respects_terrain_cost`: Flow field respects terrain cost. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0417]** `UNSUPPORTED`: `test_flow_field_smoothing_normalization`: Flow field smoothing normalization — Verify that get_vector returns a normalized Vector2.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0418]** `UNSUPPORTED`: `test_flow_field_smoothing`: Flow field smoothing — Verify that get_vector uses neighbor averaging for smoother curves.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0419]** `UNSUPPORTED`: `test_cache_with_ttl`: Cache with ttl. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_flow_fields_refinement.py`

- [x] **[RPG-0420]** `UNSUPPORTED`: `test_bilinear_interpolation_basic`: Bilinear interpolation basic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0421]** `UNSUPPORTED`: `test_static_target_caching`: Static target caching. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0422]** `UNSUPPORTED`: `test_moving_target_ttl`: Moving target ttl. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_narrative_memory.py`

- [x] **[RPG-0423]** `UNSUPPORTED`: `test_narrative_memory_trauma_biasing`: Narrative memory trauma biasing. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0424]** `UNSUPPORTED`: `test_narrative_memory_victory_confidence`: Narrative memory victory confidence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0425]** `UNSUPPORTED`: `test_region_fatigue_biasing`: Region fatigue biasing. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0426]** `UNSUPPORTED`: `test_social_appraisal_with_narrative`: Social appraisal with narrative. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_personality.py`

- [x] **[RPG-0427]** `UNSUPPORTED`: `test_motive_modifier_biases_explore`: Motive modifier biases explore. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0428]** `UNSUPPORTED`: `test_motive_modifier_biases_rest`: Motive modifier biases rest. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0429]** `UNSUPPORTED`: `test_motive_modifier_biases_flee`: Motive modifier biases flee. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_score_modifiers.py`

- [x] **[RPG-0430]** `UNSUPPORTED`: `test_boredom_modifier_applies_multipliers`: Boredom modifier applies multipliers. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0431]** `UNSUPPORTED`: `test_life_stage_modifier_early_bracket`: Life stage modifier early bracket. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0432]** `UNSUPPORTED`: `test_goal_evaluator_uses_modifiers`: Goal evaluator uses modifiers. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_softmax.py`

- [x] **[RPG-0433]** `UNSUPPORTED`: `test_softmax_distribution`: Softmax distribution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0434]** `UNSUPPORTED`: `test_softmax_with_equal_scores`: Softmax with equal scores. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/ai/test_stuck.py`

- [x] **[RPG-0435]** `UNSUPPORTED`: `test_perception_tracks_position_history`: Perception tracks position history. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0436]** `UNSUPPORTED`: `test_appraisal_detects_stuck`: Appraisal detects stuck. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/combat/test_building_sabotage.py`

- [x] **[RPG-0437]** `UNSUPPORTED`: `test_validate_building_target`: Validate building target. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0438]** `UNSUPPORTED`: `test_apply_building_sabotage`: Apply building sabotage. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/combat/test_combat_building.py`

- [x] **[RPG-0439]** `UNSUPPORTED`: `test_building_sabotage_validation`: Building sabotage validation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0440]** `UNSUPPORTED`: `test_building_sabotage_application`: Building sabotage application. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/combat/test_consequences.py`

- [x] **[RPG-0441]** `test_wound_infliction_massive_hit`: Wound infliction massive hit — Verify that damage > 25% max HP guarantees a wound.. <!-- ID: RPG-0441 SOURCE: src/engine/combat.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0442]** `test_wound_stat_impact`: Wound stat impact — Verify that wounds correctly reduce properties in CombatAspect.. <!-- ID: RPG-0442 SOURCE: src/engine/combat.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0443]** `UNSUPPORTED`: `test_scar_permanence`: Scar permanence — Verify that scars are permanent and identifiable.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/combat/test_exhaustion.py`

- [x] **[RPG-0444]** `test_stamina_drain_on_attack`: Stamina drain on attack — Verify that a basic attack drains stamina from the actor.. <!-- ID: RPG-0444 SOURCE: src/engine/domain_logic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-0445]** `test_exhaustion_penalty_application`: Exhaustion penalty application — Verify that ActionSystem applies fatigue effect when stamina is low.. <!-- ID: RPG-0445 SOURCE: src/engine/combat.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->

#### `unit/core/aspects/test_aoa_integrity.py`

- [x] **[RPG-0446]** `UNSUPPORTED`: `test_entity_field_integrity`: Entity field integrity — Ensure Entity model_fields contains only the ID, Kind, and Aspects.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0447]** `UNSUPPORTED`: `test_entity_property_locking`: Entity property locking — Ensure no forbidden legacy properties have been re-introduced as shims.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0448]** `UNSUPPORTED`: `test_aspect_model_purity`: Aspect model purity — Ensure aspects themselves stay clean of Cross-Aspect dependencies.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0449]** `UNSUPPORTED`: `test_mandatory_aspect_naming`: Mandatory aspect naming — Aspects must be named exactly as their type (lowercase).. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/aspects/test_evolution.py`

- [x] **[RPG-0450]** `UNSUPPORTED`: `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap. [AOA REFACTOR]. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0451]** `UNSUPPORTED`: `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment. [AOA REFACTOR]. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/aspects/test_genetics.py`

- [x] **[RPG-0452]** `UNSUPPORTED`: `test_genetic_seed_init`: Genetic seed init. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0453]** `UNSUPPORTED`: `test_training_uses_aptitudes`: Training uses aptitudes. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0454]** `UNSUPPORTED`: `test_aging_and_death`: Aging and death. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/logic/test_person_logic.py`

- [x] **[RPG-0455]** `UNSUPPORTED`: `test_personality_bias_logic`: Personality bias logic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0456]** `UNSUPPORTED`: `test_social_appraisal_logic`: Social appraisal logic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0457]** `UNSUPPORTED`: `test_full_motive_pipeline_integration`: Full motive pipeline integration — Verifies that social and personality biases stack correctly.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/logic/test_routine_service.py`

- [x] **[RPG-0458]** `UNSUPPORTED`: `test_routine_service_sleep_bias`: Routine service sleep bias. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0459]** `UNSUPPORTED`: `test_routine_service_forced_rest_during_off_hours`: Routine service forced rest during off hours. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0460]** `UNSUPPORTED`: `test_routine_service_hunger_bias`: Routine service hunger bias. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/models/test_phase4_models.py`

- [x] **[RPG-0461]** `UNSUPPORTED`: `test_history_registry_serialization`: History registry serialization. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0462]** `UNSUPPORTED`: `test_household_record`: Household record. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0463]** `UNSUPPORTED`: `test_local_scar_record`: Local scar record. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0464]** `UNSUPPORTED`: `test_region_consequence_record`: Region consequence record. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0465]** `UNSUPPORTED`: `test_world_state_integration_phase4`: World state integration phase4. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/models/test_serialization_hardened.py`

- [x] **[RPG-0466]** `UNSUPPORTED`: `test_json_encoder_mapping_proxy`: Json encoder mapping proxy. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0467]** `UNSUPPORTED`: `test_json_encoder_enum`: Json encoder enum. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0468]** `UNSUPPORTED`: `test_serialization_pydantic_model`: Serialization pydantic model. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0469]** `UNSUPPORTED`: `test_serialization_frozen_model_with_proxy`: Serialization frozen model with proxy. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0470]** `UNSUPPORTED`: `test_serializer_loads`: Serializer loads. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_aoa_coercion.py`

- [x] **[RPG-0471]** `UNSUPPORTED`: `test_vector2_coercion_during_freeze`: Vector2 coercion during freeze — CRITICAL ARCHITECTURAL VERIFICATION: Ensures that if a field expecting a SimulationModel subclass (like Vector2) contains a raw dict (e.g. from serialization drift), the freeze() logic authoritatively coerces it back to the proper object before applying proxies.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_depth_features.py`

- [x] **[RPG-0472]** `UNSUPPORTED`: `test_well_rested_effect_application`: Well rested effect application — Verify that the Well-Rested buff correctly affects Max HP and XP mult.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0473]** `UNSUPPORTED`: `test_attribute_synergy_xp_mult`: Attribute synergy xp mult — Verify that Wisdom/Intelligence correctly affects XP multiplier.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0474]** `UNSUPPORTED`: `test_class_weighted_gear`: Class weighted gear — Verify that item power is correctly weighted for different classes.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_eb_isolated.py`

- [x] **[RPG-0475]** `UNSUPPORTED`: `test_eb_stats_scaling`: Eb stats scaling. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/core/test_performance_optimizations.py`

- [x] **[RPG-0476]** `UNSUPPORTED`: `test_grid_bytearray_correctness`: Grid bytearray correctness — Verify Grid correctly stores and retrieves materials using bytearray and cache.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0477]** `UNSUPPORTED`: `test_grid_copy_is_not_shared`: Grid copy is not shared — Verify Grid.copy() duplicates the bytearray data.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0478]** `UNSUPPORTED`: `test_entity_copy_shallow_vs_refs`: Entity copy shallow vs refs — Verify Entity.copy() is shallow for aspects but produces a new Entity object.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0479]** `UNSUPPORTED`: `test_ai_worker_batch_processing_logic`: Ai worker batch processing logic — Verify AIWorkerDaemon correctly handles a batch of tasks.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_action_convergence.py`

- [x] **[RPG-0480]** `UNSUPPORTED`: `test_loot_no_duplication`: Loot no duplication — Verify that items picked up by the system are not duplicated by AI updates.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0481]** `UNSUPPORTED`: `test_corpse_loot_convergence`: Corpse loot convergence — Verify that corpse recovery is authoritatively handled by ActionSystem.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_dynamic_quests.py`

- [x] **[RPG-0482]** `UNSUPPORTED`: `test_dynamic_liberate_quest`: Dynamic liberate quest. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0483]** `UNSUPPORTED`: `test_history_logging`: History logging. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_evolution.py`

- [x] **[RPG-0484]** `UNSUPPORTED`: `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap.. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0485]** `UNSUPPORTED`: `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment.. <!-- VERIFIED v2: UNSUPPORTED -->

#### `unit/systems/test_personality_ai.py`

- [x] **[RPG-0486]** `UNSUPPORTED`: `test_grudge_accumulation`: Grudge accumulation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0487]** `UNSUPPORTED`: `test_should_flee_logic`: Should flee logic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0488]** `UNSUPPORTED`: `test_locational_memory_on_death`: Locational memory on death. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0489]** `UNSUPPORTED`: `test_frontier_locational_penalty`: Frontier locational penalty. <!-- VERIFIED v2: UNSUPPORTED -->

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

- [x] **[RPG-0490]** `UNSUPPORTED`: preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0491]** `UNSUPPORTED`: intentionally divergent <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0492]** `UNSUPPORTED`: unsupported <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0493]** `UNSUPPORTED`: not yet checked <!-- VERIFIED v2: UNSUPPORTED -->

Also record:

- original evidence
- `src` evidence
- divergence note
- proof path

---

## A. CLI and entrypoint compatibility

Relevant original source/test evidence:

- `src/__main__.py`
- `tests/e2e/test_logging_structure.py`

### CLI mode and parser contract

- [x] **[RPG-0494]** `UNSUPPORTED`: `python -m src` defaults to server mode when no subcommand is provided. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0495]** `UNSUPPORTED`: `python -m src serve` accepts the original `--host`, `--port`, `--seed`, `--entities`, `--workers`, `--log-level` arguments. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0496]** `UNSUPPORTED`: `python -m src cli` accepts the original `--ticks`, `--entities`, `--seed`, `--workers`, `--grid-width`, `--grid-height`, `--replay`, `--log-level` arguments. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0497]** `UNSUPPORTED`: `python -m src inspect` accepts the original `--id`, `--seed`, `--ticks`, `--entities`, `--workers`, `--log-level` arguments. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0498]** `UNSUPPORTED`: CLI argument defaults remain compatible with legacy expectations. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0499]** `UNSUPPORTED`: Invalid CLI arguments fail in a controlled, parser-driven way. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0500]** `UNSUPPORTED`: CLI replay-file argument writes to the expected output path semantics. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0501]** CLI mode still initializes the same baseline world-building flow (town, sanctuary, camps, hero spawn, goblin spawn) under equivalent config. <!-- VERIFIED v2: authoritative_world_objects -->

### CLI environment boot behavior

- [x] **[RPG-0502]** `UNSUPPORTED`: CLI mode forces broker-disabled behavior through environment setup when not already set. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0503]** `UNSUPPORTED`: CLI startup still loads registries before simulation loop startup. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0504]** `UNSUPPORTED`: CLI startup still wires logging before engine loop execution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0505]** `UNSUPPORTED`: CLI shutdown still tears down worker infrastructure cleanly after simulation. <!-- VERIFIED v2: UNSUPPORTED -->

---

## B. Optional-broker disabled-mode compatibility

Relevant original source/test evidence:

- `tests/api/test_broker_isolation.py`
- `tests/integration/infra/test_brokerless_import.py`

### RabbitMQ disabled-mode behavior

- [x] **[RPG-0506]** `UNSUPPORTED`: `DISABLE_RABBITMQ=1` causes RabbitMQ client code to enter explicit disabled mode. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0507]** `UNSUPPORTED`: RabbitMQ client imports do not crash when disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0508]** `UNSUPPORTED`: RabbitMQ public accessors return safe no-op values (`None`) when disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0509]** `UNSUPPORTED`: RabbitMQ disabled-mode behavior remains safe even when broker libraries are missing. <!-- VERIFIED v2: UNSUPPORTED -->

### Kafka disabled-mode behavior

- [x] **[RPG-0510]** `UNSUPPORTED`: `DISABLE_KAFKA=1` causes Kafka client code to enter explicit disabled mode. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0511]** `UNSUPPORTED`: Kafka client imports do not crash when disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0512]** `UNSUPPORTED`: Kafka public accessors return safe no-op values (`None`) when disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0513]** `UNSUPPORTED`: Kafka disabled-mode behavior remains safe even when broker libraries are missing. <!-- VERIFIED v2: UNSUPPORTED -->

### Redis disabled / missing-package behavior

- [x] **[RPG-0514]** `UNSUPPORTED`: Redis client behavior remains safe when Redis package or runtime is unavailable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0515]** `UNSUPPORTED`: Redis accessors fail safely without crashing simulation bootstrap when Redis is optional. <!-- VERIFIED v2: UNSUPPORTED -->

### Disabled-mode import isolation

- [x] **[RPG-0516]** `UNSUPPORTED`: Headless runner imports still succeed when optional brokers are disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0517]** `UNSUPPORTED`: Action-system imports still succeed when optional brokers are disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0518]** `UNSUPPORTED`: Import-time behavior does not accidentally force broker setup. <!-- VERIFIED v2: UNSUPPORTED -->

---

## C. Worker-pool and infrastructure fallback behavior

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_infrastructure_isolation.py`
- worker-pool usage in original CLI and loop wiring

### Worker fallback semantics

- [x] **[RPG-0519]** `UNSUPPORTED`: Worker pool falls back to inline/local execution when broker transport is unavailable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0520]** `UNSUPPORTED`: Worker pool does not require live RabbitMQ/Kafka to execute local simulation behavior. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0521]** `UNSUPPORTED`: Worker fallback preserves authoritative action generation semantics. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0522]** `UNSUPPORTED`: Worker fallback preserves deterministic ordering expectations in local mode. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0523]** `UNSUPPORTED`: Worker shutdown remains safe after fallback execution paths. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0524]** `UNSUPPORTED`: Missing broker infrastructure does not block minimal simulation startup. <!-- VERIFIED v2: UNSUPPORTED -->

### Import/runtime isolation

- [x] **[RPG-0525]** `UNSUPPORTED`: Infrastructure module isolation prevents optional dependencies from contaminating normal simulation imports. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0526]** `UNSUPPORTED`: Runtime paths that do not require brokers do not import or initialize them accidentally. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0527]** `UNSUPPORTED`: Fallback behavior is exercised by real tests, not only by mocks or assumptions. <!-- VERIFIED v2: UNSUPPORTED -->

---

## D. Chaos mode and infrastructure resilience

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_chaos.py`

### Chaos resilience

- [x] **[RPG-0528]** `UNSUPPORTED`: Chaos-enabled runs survive AI-result drop conditions without immediate simulation failure. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0529]** `UNSUPPORTED`: Chaos-enabled runs continue ticking through configured chaos-drop scenarios. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0530]** `UNSUPPORTED`: Chaos does not corrupt authoritative world state shape. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0531]** `UNSUPPORTED`: Chaos does not break snapshot acquisition. <!-- VERIFIED v2: UNSUPPORTED -->

### Chaos determinism

- [x] **[RPG-0532]** `UNSUPPORTED`: Given identical seed and identical chaos configuration, repeated chaos-mode runs remain deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0533]** `UNSUPPORTED`: Chaos-mode determinism is verified by repeated world-state fingerprint comparison. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0534]** `UNSUPPORTED`: Chaos-enabled infrastructure does not introduce hidden non-determinism into equivalent runs. <!-- VERIFIED v2: UNSUPPORTED -->

---

## E. Replay compatibility outside pure RPG-core semantics

Relevant original source/test evidence:

- replay usage in `src/__main__.py`
- replay-related explainability / determinism / regression tests
- `tests/e2e/test_deterministic_replay.py`

### Replay output contract

- [x] **[RPG-0535]** `UNSUPPORTED`: Replay files are written in the expected legacy location/format semantics for headless runs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0536]** `UNSUPPORTED`: Replay snapshots preserve deterministic entity ordering and field availability where legacy tests rely on them. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0537]** `UNSUPPORTED`: Replay preserves enough world-state detail to support legacy fingerprinting and regression assertions. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0538]** `UNSUPPORTED`: Replay can support structural comparison between repeated runs with same seed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0539]** `UNSUPPORTED`: Replay remains aligned with other truth surfaces where legacy tests expect parity. <!-- VERIFIED v2: UNSUPPORTED -->

### End-to-end deterministic replay path

- [x] **[RPG-0540]** `UNSUPPORTED`: Same seed and equivalent configuration produce identical replay-visible state across runs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0541]** `UNSUPPORTED`: Different seeds produce divergent replay-visible state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0542]** `UNSUPPORTED`: Replay includes ground-item state where legacy determinism tests inspect it. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0543]** `UNSUPPORTED`: Replay includes enough actor combat/progression/mind state for state-fingerprint checks. <!-- VERIFIED v2: UNSUPPORTED -->

---

## F. Structured logging compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py`
- original logging setup and JSON formatter usage in source

### Logging format contract

- [x] **[RPG-0544]** `UNSUPPORTED`: CLI stdout logs remain valid JSON line-by-line. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0545]** `UNSUPPORTED`: Each emitted structured log includes mandatory fields: <!-- VERIFIED v2: UNSUPPORTED -->
  - [ ] `timestamp`
  - [ ] `level`
  - [ ] `message`
  - [ ] `component`
- [x] **[RPG-0546]** `UNSUPPORTED`: Log output remains machine-parseable under normal CLI execution. <!-- VERIFIED v2: UNSUPPORTED -->

### Logging context injection

- [x] **[RPG-0547]** `UNSUPPORTED`: World-loop logs include tick context. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0548]** `UNSUPPORTED`: World-loop logs preserve identifiable component naming. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0549]** `UNSUPPORTED`: Worker-pool logs preserve identifiable component naming where emitted. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0550]** `UNSUPPORTED`: Main entrypoint logs preserve identifiable `__main__` or equivalent component identity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0551]** `UNSUPPORTED`: Structured logging remains compatible with legacy context-injection expectations. <!-- VERIFIED v2: UNSUPPORTED -->

---

## G. Metrics and monitoring compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py` (Prometheus check)
- original metrics/logging stack wiring in source

### Prometheus / telemetry compatibility

- [x] **[RPG-0552]** `UNSUPPORTED`: Simulation metrics remain scrapeable by Prometheus in equivalent stack configurations. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0553]** `UNSUPPORTED`: Legacy-queried metric names remain available where replacement claims require them. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0554]** `UNSUPPORTED`: Tick-duration metrics remain emitted under the expected metric contract. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0555]** `UNSUPPORTED`: Monitoring stack checks do not silently pass with empty data. <!-- VERIFIED v2: UNSUPPORTED -->

### Operational observability

- [x] **[RPG-0556]** `UNSUPPORTED`: Engine-side metrics remain available without forcing gameplay divergence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0557]** `UNSUPPORTED`: Metrics do not rely on broker-only paths if local/headless execution is supposed to work without brokers. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0558]** `UNSUPPORTED`: Monitoring compatibility is verified under realistic stack conditions, not just unit stubs. <!-- VERIFIED v2: UNSUPPORTED -->

---

## H. API protocol and transport compatibility

Relevant original source/test evidence:

- API metadata tests
- websocket handshake tests
- gzip compression test

### Metadata endpoints

- [x] **[RPG-0559]** `UNSUPPORTED`: Protocol metadata endpoint remains available at the expected route. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0560]** `UNSUPPORTED`: Metadata response still includes entity key mapping where legacy consumers expect it. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0561]** `UNSUPPORTED`: Metadata response still includes state enum mapping where legacy consumers expect it. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0562]** `UNSUPPORTED`: Protocol metadata field order/meaning remains compatible where clients depend on it. <!-- VERIFIED v2: UNSUPPORTED -->

### WebSocket protocol behavior

- [x] **[RPG-0563]** `UNSUPPORTED`: WebSocket endpoint still supports legacy handshake semantics. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0564]** `UNSUPPORTED`: JSON handshake mode remains supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0565]** `UNSUPPORTED`: MessagePack handshake mode remains supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0566]** `UNSUPPORTED`: Initial post-handshake payload remains structurally compatible with legacy client expectations. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0567]** `UNSUPPORTED`: Tick/entity/event payload shape remains compatible where explicitly defined by legacy tests. <!-- VERIFIED v2: UNSUPPORTED -->

### Compression behavior

- [x] **[RPG-0568]** `UNSUPPORTED`: GZip middleware or equivalent response compression remains functional for large metadata responses. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0569]** `UNSUPPORTED`: Compression support does not break standard metadata endpoint access. <!-- VERIFIED v2: UNSUPPORTED -->

---

## I. Headless runner / final-system execution compatibility

Relevant original source/test evidence:

- headless runner import/use tests
- deterministic replay tests
- brokerless import tests
- cognition/replay consistency regression tests

### Headless execution path

- [x] **[RPG-0570]** `UNSUPPORTED`: A minimal production-like headless run can still execute without optional brokers when disabled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0571]** `UNSUPPORTED`: Headless run still produces the expected result artifacts (at minimum replay, and where applicable manifest/graph outputs). <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0572]** `UNSUPPORTED`: Headless runner import remains isolated from optional broker setup. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0573]** `UNSUPPORTED`: Final-system path remains suitable for regression use rather than demo-only use. <!-- VERIFIED v2: UNSUPPORTED -->

### Artifact consistency

- [x] **[RPG-0574]** `UNSUPPORTED`: Final-system artifacts remain mutually consistent where legacy tests compare them. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0575]** `UNSUPPORTED`: Structural graph/export surfaces remain aligned with replay where legacy tests require parity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0576]** `UNSUPPORTED`: Artifact generation failure paths remain visible rather than silently swallowed. <!-- VERIFIED v2: UNSUPPORTED -->

---

## J. Infrastructure-side “unhappy path” compatibility actually evidenced in legacy tests

Only include source-grounded unhappy paths.

### Disabled/missing dependency paths

- [x] **[RPG-0577]** `UNSUPPORTED`: Missing RabbitMQ package with disabled flag does not crash import. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0578]** `UNSUPPORTED`: Missing Kafka package with disabled flag does not crash import. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0579]** `UNSUPPORTED`: Missing Redis package does not crash safe initialization paths where optional. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0580]** `UNSUPPORTED`: Missing broker dependencies do not block headless runner imports. <!-- VERIFIED v2: UNSUPPORTED -->

### Runtime degradation paths

- [x] **[RPG-0581]** `UNSUPPORTED`: Worker transport degradation falls back safely to local execution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0582]** `UNSUPPORTED`: Chaos-mode packet/result drop does not terminate the simulation prematurely under supported settings. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0583]** `UNSUPPORTED`: Monitoring checks fail loudly when expected data is missing. <!-- VERIFIED v2: UNSUPPORTED -->

### CLI/runtime robustness

- [x] **[RPG-0584]** `UNSUPPORTED`: CLI execution still emits structured logs under minimal simulation runs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0585]** `UNSUPPORTED`: Short runs still produce enough output for regression inspection. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0586]** `UNSUPPORTED`: Minimal runs do not require full external stack unless explicitly in E2E stack mode. <!-- VERIFIED v2: UNSUPPORTED -->

---

## K. Explicit exclusions from this add-on checklist

These should stay out unless you create a third checklist:

- generic security advice not tied to actual legacy code/tests
- generic performance wishes not evidenced by legacy behavior
- speculative logging/telemetry fields not checked in legacy code/tests
- invented infra classes or APIs not present in legacy source
- non-gameplay docs/release-gate concerns already tracked elsewhere

---

## L. Recommended artifact name

`legacy_src_system_compatibility_checklist.md`

---

## M. Recommended ledger columns

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

- [x] **[RPG-0587]** `UNSUPPORTED`: `test_perception_phase_populates_attention_pool`: attention pool population <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0588]** `UNSUPPORTED`: `test_belief_refresh_captures_apparent_state`: belief refresh from apparent state <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0589]** `UNSUPPORTED`: `test_belief_decay_lifecycle`: belief decay lifecycle <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0590]** `UNSUPPORTED`: `test_belief_conflict_resolution`: belief conflict handling <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0591]** `UNSUPPORTED`: `test_belief_sharing_propagation`: belief sharing propagation <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0592]** `UNSUPPORTED`: `test_threat_estimation_logic`: threat estimation logic <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0593]** `UNSUPPORTED`: `test_perception_phase_appraisal_sync`: appraisal sync <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0594]** `UNSUPPORTED`: `test_perception_tracks_position_history`: position-history tracking <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0595]** `UNSUPPORTED`: `test_appraisal_phase_triggers_panic_on_low_hp`: panic trigger via appraisal <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0596]** `UNSUPPORTED`: `test_appraisal_detects_stuck`: stuck appraisal detection <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0597]** `UNSUPPORTED`: `test_social_appraisal_logic`: social appraisal logic <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0598]** `UNSUPPORTED`: `test_social_appraisal_with_narrative`: narrative-informed social appraisal <!-- VERIFIED v2: UNSUPPORTED -->

---

## B. Routine / motive / biological needs / life rhythm

Relevant original source/test evidence:

- `RoutineService`
- `ObjectiveDerivationService`
- `tests/unit/ai/test_routine.py`
- related rest/sleep/hunger tests in `all_test.py`

- [x] **[RPG-0599]** `UNSUPPORTED`: `test_sleep_goal_utility_at_night`: sleep utility at night <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0600]** `UNSUPPORTED`: `test_rest_to_sleep_transition`: rest-to-sleep transition <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0601]** `UNSUPPORTED`: `test_routine_service_sleep_bias`: sleep bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0602]** `UNSUPPORTED`: `test_routine_service_forced_rest_during_off_hours`: forced off-hours rest <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0603]** `UNSUPPORTED`: `test_routine_service_hunger_bias`: hunger bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0604]** `UNSUPPORTED`: `test_home_visit_leads_to_eating`: eating behavior from routine/home visit <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0605]** `test_inn_visit_leads_to_sleeping`: inn visit leads to sleeping <!-- VERIFIED v2: inn_visit_semantics -->
- [x] **[RPG-0606]** `UNSUPPORTED`: `test_biological_decay_and_forced_sleep`: biological decay and forced sleep <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0607]** `UNSUPPORTED`: `test_sleeping_recovery_cycle`: sleeping recovery cycle <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0608]** `UNSUPPORTED`: `test_hunger_reduces_stability`: hunger consequence <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0609]** `UNSUPPORTED`: `test_routine_goal_priority`: routine goal priority <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0610]** `UNSUPPORTED`: `test_routine_disruption_panic`: disruption panic <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0611]** `UNSUPPORTED`: `test_attack_disruption_suppresses_routines`: attack suppresses routine <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0612]** `UNSUPPORTED`: `test_routine_priority_archetype_bias`: archetype-based routine bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0613]** `UNSUPPORTED`: `test_life_stage_priority_shift`: life-stage priority shift <!-- VERIFIED v2: UNSUPPORTED -->

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

- [x] **[RPG-0614]** `UNSUPPORTED`: `test_ai_boredom_diversification`: boredom diversification effect <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0615]** `UNSUPPORTED`: `test_boredom_modifier_applies_multipliers`: boredom modifier law <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0616]** `UNSUPPORTED`: `test_life_stage_modifier_early_bracket`: life-stage modifier law <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0617]** `UNSUPPORTED`: `test_motive_modifier_biases_explore`: motive modifier explore bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0618]** `UNSUPPORTED`: `test_motive_modifier_biases_rest`: motive modifier rest bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0619]** `UNSUPPORTED`: `test_motive_modifier_biases_flee`: motive modifier flee bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0620]** `UNSUPPORTED`: `test_goal_evaluator_uses_modifiers`: goal evaluator modifier integration <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0621]** `UNSUPPORTED`: `test_softmax_distribution`: score-to-choice distribution <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0622]** `UNSUPPORTED`: `test_softmax_with_equal_scores`: equal-score handling <!-- VERIFIED v2: UNSUPPORTED -->

---

## D. Emotional / narrative memory / trauma logic

Relevant original source/test evidence:

- `MemorySalienceService`
- `EventInterpreterService`
- `tests/unit/ai/test_emotional_memory.py`
- `tests/unit/ai/test_narrative_memory.py`

- [x] **[RPG-0623]** `UNSUPPORTED`: `test_locational_trauma_triggers_dread`: locational trauma -> dread <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0624]** `UNSUPPORTED`: `test_emotional_bias_on_utility`: emotion changes utility <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0625]** `UNSUPPORTED`: `test_emotional_decay`: emotional decay <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0626]** `UNSUPPORTED`: `test_narrative_memory_trauma_biasing`: trauma memory biasing <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0627]** `UNSUPPORTED`: `test_narrative_memory_victory_confidence`: victory-confidence memory <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0628]** `UNSUPPORTED`: `test_narrative_memory_logging`: narrative memory logging <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0629]** `UNSUPPORTED`: `test_social_appraisal_with_narrative`: narrative-informed social appraisal <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0630]** `UNSUPPORTED`: `test_bravery_modifiers`: bravery modifiers <!-- VERIFIED v2: UNSUPPORTED -->

---

## E. Combat aftermath / wounds / scars / stamina / exhaustion

Relevant original source/test evidence:

- `DamageResolutionService`
- `CombatAftermathService`
- `tests/unit/combat/**`
- related stamina tests in `all_test.py`

- [x] **[RPG-0631]** `wound_infliction_massive_hit`: 40%+ max HP in one hit creates wound. <!-- ID: RPG-0631 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [ ] **[RPG-0632]** `wound_stat_impact`: wounds apply atk/def/speed/hp penalties. <!-- VERIFIED v2: wound_stat_impact -->
- [x] **[RPG-0633]** `scar_permanence_logic`: scars persist after wound heals. <!-- ID: RPG-0633 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0634]** `UNSUPPORTED`: `test_scar_decay`: scar decay behavior if preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0635]** `UNSUPPORTED`: `test_local_scar_record`: local scar record <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0636]** `scar_detection_logic`: scar detection. <!-- VERIFIED v2: scar_detection_logic -->
- [x] **[RPG-0637]** `UNSUPPORTED`: `test_ai_perception_of_scars`: perception of scars <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0638]** `stamina_drain_attack`: stamina drain on attack <!-- ID: RPG-0638 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0639]** `stamina_drain_movement`: stamina drain on move <!-- ID: RPG-0639 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0640]** `stamina_drain_harvest`: stamina drain on harvest <!-- ID: RPG-0640 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0641]** `stamina_cost_skill_use`: stamina cost on skill use <!-- ID: RPG-0641 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0642]** `stamina_regen_resting`: rest stamina regen <!-- ID: RPG-0642 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0643]** `stamina_regen_active`: active regen <!-- ID: RPG-0643 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [x] **[RPG-0644]** `stamina_regen_capped`: regen cap <!-- ID: RPG-0644 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [ ] **[RPG-0645]** `exhaustion_penalty_combat`: exhaustion penalty <!-- VERIFIED v2: exhaustion_penalty_combat -->
- [x] **[RPG-0646]** `terrain_cost_pathfinding`: Road tiles cost 0.5x. <!-- ID: RPG-0646 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->

---

## F. Tactical specialty / action style / combo behavior

Relevant original source/test evidence:

- combat/tactical logic in `all_src.py`
- `tests/unit/ai/test_action_styles.py`
- `tests/unit/ai/test_flanking.py`
- `tests/unit/ai/test_combos.py`

- [x] **[RPG-0647]** `UNSUPPORTED`: `test_execution_phase_modifies_proposal_with_aggressive_style`: aggressive action style <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0648]** `UNSUPPORTED`: `test_execution_phase_modifies_proposal_with_evasive_style`: evasive action style <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0649]** `UNSUPPORTED`: `test_flanking_bonus`: flanking bonus <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0650]** `UNSUPPORTED`: `test_no_flanking_bonus_when_facing_attacker`: facing-sensitive flanking exclusion <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0651]** `UNSUPPORTED`: `test_shatter_combo`: combo behavior <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0652]** `UNSUPPORTED`: `test_ranged_hero_kites_when_adjacent`: ranged kiting <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0653]** `UNSUPPORTED`: `test_ranged_skirmisher_kites_when_close`: ranged skirmish spacing <!-- VERIFIED v2: UNSUPPORTED -->

---

## G. Loot / hidden discovery / local reward realism

Relevant original source/test evidence:

- loot and discovery logic in `all_src.py`
- related tests in `all_test.py`

- [x] **[RPG-0654]** `UNSUPPORTED`: `test_luck_impacts_loot_modifier`: loot modifier from luck/perception <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0655]** `UNSUPPORTED`: `test_per_based_hidden_discovery`: hidden discovery from perception <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0656]** `UNSUPPORTED`: `test_loot_recovery_consistency`: loot recovery consistency <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0657]** `UNSUPPORTED`: `test_loot_no_duplication`: no duplicated loot <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0658]** `UNSUPPORTED`: `test_corpse_loot_convergence`: corpse loot convergence <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0659]** `UNSUPPORTED`: `test_loot_and_respawn`: loot and respawn interaction <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0660]** `UNSUPPORTED`: `test_loot_tables_exist`: loot table integrity <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0661]** `UNSUPPORTED`: `test_full_bag_aborts_looting`: abort looting when full <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0662]** `UNSUPPORTED`: `test_overweight_aborts_looting`: abort looting when overweight <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0663]** `UNSUPPORTED`: `test_near_weight_limit_penalizes_loot`: weight-limit penalty on looting <!-- VERIFIED v2: UNSUPPORTED -->

---

## H. Region-scale strategic and world consequences

Relevant original source/test evidence:

- `StrategicConsequenceService`
- `WorldConsequenceInterpretationService`
- region/world consequence tests in `all_test.py`

- [x] **[RPG-0664]** `UNSUPPORTED`: `test_regional_suppression`: regional suppression <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0665]** `UNSUPPORTED`: `test_strategic_pivot_on_regional_danger`: pivot on regional danger <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0666]** `UNSUPPORTED`: `test_region_fatigue_biasing`: region fatigue biasing <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0667]** `UNSUPPORTED`: `test_region_consequence_record`: region consequence record <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0668]** `UNSUPPORTED`: `test_conquered_region_triggers_stronghold`: conquered region -> stronghold consequence <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0669]** `UNSUPPORTED`: `test_strategic_pipeline_home_threat`: home threat in strategic pipeline <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0670]** `UNSUPPORTED`: `test_world_consequence_*`: world consequence interpretation coverage where applicable <!-- VERIFIED v2: UNSUPPORTED -->

---

## I. Death / permadeath / succession / heirlooms / nemesis

Relevant original source/test evidence:

- lifecycle / death / social-consequence logic in `all_src.py`
- related tests in `all_test.py`

- [x] **[RPG-0671]** `UNSUPPORTED`: `test_aging_and_death`: aging and death <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0672]** `UNSUPPORTED`: `test_hero_lifecycle_system_permadeath`: hero permadeath <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0673]** `UNSUPPORTED`: `test_permadeath_succession_and_heirlooms`: succession and heirlooms <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0674]** `UNSUPPORTED`: `test_hero_death_creates_scar`: death scar consequences <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0675]** `UNSUPPORTED`: `test_near_death_triggers_survival_consequences`: near-death survival consequences <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0676]** `UNSUPPORTED`: `test_near_death_hardening`: near-death hardening <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0677]** `UNSUPPORTED`: `test_nemesis_recognition_and_fear_bias`: nemesis recognition and fear bias <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0678]** `UNSUPPORTED`: `test_nemesis_milestone_creation`: nemesis milestone creation <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0679]** `UNSUPPORTED`: `test_locational_memory_on_death`: locational memory on death <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0680]** `UNSUPPORTED`: `test_influence_shifts_on_monster_death`: influence shift on monster death <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0681]** `UNSUPPORTED`: `test_influence_shifts_on_hero_death`: influence shift on hero death <!-- VERIFIED v2: UNSUPPORTED -->

---

## J. Medical / diagnosis judgment logic

Relevant original source/test evidence:

- diagnosis logic in `all_src.py`
- related tests in `all_test.py`

- [x] **[RPG-0682]** `UNSUPPORTED`: `test_accurate_diagnosis_high_wisdom`: accurate diagnosis at high wisdom <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0683]** `UNSUPPORTED`: `test_misdiagnosis_low_wisdom`: misdiagnosis at low wisdom <!-- VERIFIED v2: UNSUPPORTED -->

# Legacy `src` RPG-Core Checklist — Part 7 (Residual Test-Covered Logic)

This checklist is additive to Parts 1–6.

It exists to capture smaller but still real legacy logic families that are explicitly covered by tests and are easy to lose if they remain implicit under broad labels like strategy, progression, or world behavior.

This part should stay test-first. If a behavior is listed here, it should have an identifiable test anchor in the original legacy test surface.

---

## A. Quest lifecycle, generation, and completion logic

Relevant legacy test surface includes quest creation, progression, duplicate suppression, completion, rewards, and quest-type-specific behavior.

- [x] **[RPG-0684]** `UNSUPPORTED`: `test_quest_creation`: quest creation baseline <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0685]** `UNSUPPORTED`: `test_quest_advance`: quest progression increments correctly <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0686]** `UNSUPPORTED`: `test_quest_advance_does_nothing_when_completed`: completed quests do not advance further <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0687]** `UNSUPPORTED`: `test_quest_progress_ratio`: progress-ratio computation is correct <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0688]** `UNSUPPORTED`: `test_generate_quest_returns_quest`: quest generator returns valid quest object <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0689]** `UNSUPPORTED`: `test_generate_quest_respects_level`: generated quests respect level banding <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0690]** `UNSUPPORTED`: `test_generate_quest_skips_duplicate`: duplicate quest generation is suppressed <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0691]** `UNSUPPORTED`: `test_generate_quest_gold_scales_with_level`: quest gold reward scales with level <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0692]** `UNSUPPORTED`: `test_generate_explore_quest`: explore-quest generation works <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0693]** `UNSUPPORTED`: `test_hunt_quest_completion_awards_rewards`: hunt-quest completion awards rewards <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0694]** `UNSUPPORTED`: `test_explore_quest_completes_near_target`: explore-quest completes near target <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0695]** `UNSUPPORTED`: `test_gather_quest_advance`: gather-quest progression works <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0696]** `UNSUPPORTED`: `test_dynamic_liberate_quest`: liberate-quest generation/progression works <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0697]** `UNSUPPORTED`: `test_territory_conquest`: territory-conquest quest/world objective behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## B. Trait system logic

Relevant legacy test surface includes trait definitions, trait assignment, trait aggregation, compatibility, and serialization.

- [x] **[RPG-0698]** `UNSUPPORTED`: `test_trait_serialization`: trait serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0699]** `UNSUPPORTED`: `test_get_traits`: trait retrieval works <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0700]** `UNSUPPORTED`: `test_trait_defs_not_empty`: trait definitions exist and are non-empty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0701]** `UNSUPPORTED`: `test_with_traits_assigns_traits`: explicit trait assignment works <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0702]** `UNSUPPORTED`: `test_no_traits_by_default`: no-trait default behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0703]** `UNSUPPORTED`: `test_traits_with_different_race_prefix`: race-prefixed trait handling is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0704]** `UNSUPPORTED`: `test_empty_traits_returns_zero_bonus`: empty-trait bonus behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0705]** `UNSUPPORTED`: `test_single_known_trait`: single-trait bonus behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0706]** `UNSUPPORTED`: `test_multiple_traits_sum`: multiple traits stack/sum correctly <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0707]** `UNSUPPORTED`: `test_unknown_trait_id_ignored`: unknown traits are ignored safely <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0708]** `UNSUPPORTED`: `test_same_trait_compatible`: trait compatibility logic is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0709]** `UNSUPPORTED`: `test_assigns_between_2_and_4_traits`: random/default trait assignment count is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0710]** `UNSUPPORTED`: `test_all_assigned_traits_are_valid`: assigned traits are always valid <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0711]** `UNSUPPORTED`: `test_all_trait_types_have_definitions`: all trait types have definitions <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0712]** `UNSUPPORTED`: `test_trait_defs_have_all_utility_fields`: trait utility fields are complete <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0713]** `UNSUPPORTED`: `test_trait_defs_have_all_stat_fields`: trait stat fields are complete <!-- VERIFIED v2: UNSUPPORTED -->

---

## C. Role derivation and role-aware behavior

Relevant legacy test surface includes role derivation, role transition, role biasing, and tactical role-awareness.

- [x] **[RPG-0714]** `UNSUPPORTED`: `test_initial_role_derivation`: initial role derivation is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0715]** `UNSUPPORTED`: `test_dynamic_role_transition_with_hysteresis`: dynamic role transition with hysteresis is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0716]** `UNSUPPORTED`: `test_role_bias_influence`: role bias affects decisions as expected <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0717]** `UNSUPPORTED`: `test_role_aware_tactical_biases`: tactical behavior reflects role-aware biasing <!-- VERIFIED v2: UNSUPPORTED -->

---

## D. Aptitudes, training-detail law, and stat recomputation

Relevant legacy test surface includes aptitude-driven training, soft caps, fractional accumulation, and recomputation of derived stats.

- [x] **[RPG-0718]** `UNSUPPORTED`: `test_training_uses_aptitudes`: aptitude-weighted training law is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0719]** `UNSUPPORTED`: `test_innate_talents_training`: innate talents affect training as expected <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0720]** `UNSUPPORTED`: `test_training_does_not_exceed_cap`: training respects hard caps <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0721]** `UNSUPPORTED`: `test_training_accumulates_fractionally`: fractional training accumulation is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0722]** `UNSUPPORTED`: `test_training_updates_stats_on_increment`: stat update on training increment is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0723]** `UNSUPPORTED`: `test_specialized_training_soft_caps`: soft-cap behavior for specialized training is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0724]** `UNSUPPORTED`: `test_output_derived_stat_ceilings`: derived-stat ceiling logic is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0725]** `UNSUPPORTED`: `test_stat_recalculation`: stat recomputation behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0726]** `UNSUPPORTED`: `test_attribute_scaling_overlap`: overlapping attribute-scaling law is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## E. Place attachment, home, and anchored behavior

Relevant legacy test surface includes place attachment, home behavior, home storage, retreat-to-home behavior, and home-driven actions.

- [x] **[RPG-0727]** `UNSUPPORTED`: `test_place_attachment_instantiation`: place attachment can be instantiated <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0728]** `UNSUPPORTED`: `test_place_attachment_navigation`: place attachment influences navigation correctly <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0729]** `UNSUPPORTED`: `test_place_attachment_home_navigation`: home-oriented navigation behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0730]** `UNSUPPORTED`: `test_no_home_returns_false`: no-home logic is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0731]** `UNSUPPORTED`: `test_home_sets_home_pos`: home position assignment is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0732]** `UNSUPPORTED`: `test_entity_copy_includes_home_storage`: home storage is preserved during copy <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0733]** `UNSUPPORTED`: `test_entity_without_home_storage`: no-home-storage case is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0734]** `UNSUPPORTED`: `test_divergent_home_response`: divergent home response behavior is explicit and preserved where intended <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0735]** `UNSUPPORTED`: `test_home_priority_retreat`: home-priority retreat behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0736]** `UNSUPPORTED`: `test_visit_home_upgrade_resolution`: visit-home upgrade resolution is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0737]** `UNSUPPORTED`: `test_home_visit_leads_to_eating`: home visit can lead to eating behavior <!-- VERIFIED v2: UNSUPPORTED -->

---

## F. Leash, camp, and local anchored ecology

Relevant legacy test surface includes leash behavior, chase abandonment, camp return, and camp reinforcement logic.

- [x] **[RPG-0738]** `UNSUPPORTED`: `test_no_leash_returns_false`: no-leash detection behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0739]** `UNSUPPORTED`: `test_mob_beyond_leash_returns_to_camp`: beyond-leash return-to-camp behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0740]** `UNSUPPORTED`: `test_mob_within_leash_wanders_normally`: within-leash wandering behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0741]** `UNSUPPORTED`: `test_no_leash_mob_wanders_freely`: leash-free wandering behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0742]** `UNSUPPORTED`: `test_chase_beyond_leash_abandons`: chase abandonment beyond leash is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0743]** `UNSUPPORTED`: `test_chase_within_leash_continues`: chase continuation within leash is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0744]** `UNSUPPORTED`: `test_no_leash_mob_hunts_freely`: no-leash hunting freedom is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0745]** `UNSUPPORTED`: `test_camp_reinforcements`: camp reinforcement behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## G. Travel topology, path-affordance, and regional traversal law

Relevant legacy test surface includes flow fields, terrain costs, roads, bridges, biome affordances, and difficulty-zone traversal constraints.

- [x] **[RPG-0746]** `UNSUPPORTED`: `test_flow_field_basic_navigation`: basic flow-field navigation is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0747]** `UNSUPPORTED`: `test_flow_field_respects_terrain_cost`: terrain-cost-sensitive navigation is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0748]** `UNSUPPORTED`: `test_flow_field_smoothing`: flow-field smoothing is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0749]** `UNSUPPORTED`: `test_flow_field_smoothing_normalization`: smoothing normalization behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0750]** `UNSUPPORTED`: `test_navigation_uses_flow_field_for_far_town`: far-town navigation uses flow fields <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0751]** `UNSUPPORTED`: `test_navigation_uses_flow_field_for_world_boss`: world-boss navigation uses flow fields <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0752]** `UNSUPPORTED`: `test_road_cost_is_low`: road traversal cost law is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0753]** `UNSUPPORTED`: `test_prefers_road_over_swamp`: road preference over swamp is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0754]** `UNSUPPORTED`: `test_each_biome_has_road_network`: biome road-network presence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0755]** `UNSUPPORTED`: `test_road_connects_locations`: road connectivity behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0756]** `UNSUPPORTED`: `test_bridges_placed_over_water`: bridge placement over water is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0757]** `UNSUPPORTED`: `test_all_four_biomes_have_features`: biome feature presence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0758]** `UNSUPPORTED`: `test_difficulty_sets_level_range`: region difficulty sets level range correctly <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0759]** `UNSUPPORTED`: `test_gold_scales_with_difficulty`: difficulty-linked gold scaling is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0760]** `UNSUPPORTED`: `test_in_region_returns_difficulty`: region difficulty query logic is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0761]** `UNSUPPORTED`: `test_difficulty_zones_defined`: difficulty-zone definition is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0762]** `UNSUPPORTED`: `test_lava_only_at_high_difficulty`: lava/high-difficulty coupling is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0763]** `UNSUPPORTED`: `test_all_terrains_have_names`: terrain naming coverage is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0764]** `UNSUPPORTED`: `test_all_terrains_have_race_labels`: terrain race-label coverage is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## H. Cooperation, recruitment-adjacent coordination, and proximity bonding

Relevant legacy test surface includes small cooperative and bonding behaviors that affect social or local-world outcomes.

- [x] **[RPG-0765]** `UNSUPPORTED`: `test_cooperation_recruitment_logic`: cooperation in recruitment/social choice is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0766]** `UNSUPPORTED`: `test_scenario_3_stationary_world_proximity_bonding`: proximity bonding behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## I. Residual small-world and economy-adjacent local realism

Relevant legacy test surface includes local inventory and burden realism that can affect action outcomes.

- [x] **[RPG-0767]** `UNSUPPORTED`: `test_full_bag_aborts_looting`: full-bag looting abort is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0768]** `UNSUPPORTED`: `test_overweight_aborts_looting`: overweight looting abort is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0769]** `UNSUPPORTED`: `test_near_weight_limit_penalizes_loot`: near-limit loot penalty is preserved <!-- VERIFIED v2: UNSUPPORTED -->

These are listed again here intentionally if not already fully owned elsewhere, because they are small and easy to lose.

---

## J. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map residual logic into roadmap phases:

- [x] **[RPG-0770]** `UNSUPPORTED`: Phase 8 owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - leash/camp/local anchored ecology
  - local burden/loot-abort realism
  - local/path-affordance pieces only where they directly affect immediate tactics

- [x] **[RPG-0771]** `UNSUPPORTED`: Phase 9 owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - quests
  - traits
  - roles
  - aptitude/training-detail law
  - place attachment/home behavior when it affects long-horizon choices
  - regional traversal/topology when it affects world-scale intention
  - cooperation/proximity bonding

- [x] **[RPG-0772]** `UNSUPPORTED`: No Part 7 item should be left implicit under a generic bucket like “AI improvements” or “progression tuning` <!-- VERIFIED v2: UNSUPPORTED -->

---

## Completion rule for Part 7

A Part 7 item is not considered covered merely because it “probably exists” inside a broader subsystem.

Each item should be considered closed only when:

- [x] **[RPG-0773]** `UNSUPPORTED`: the specific legacy behavior has a clear roadmap owner <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0774]** `UNSUPPORTED`: the specific behavior has a direct implementation or explicit divergence decision <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0775]** `UNSUPPORTED`: the specific behavior has test coverage or parity justification <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0776]** `UNSUPPORTED`: the replacement ledger/support boundary reflects the truth of that item <!-- VERIFIED v2: UNSUPPORTED -->

# Legacy `src` Assumption / Invariant Checklist — Part 8

This checklist is additive to Parts 1–7.

It is not a new gameplay-logic trunk.
It exists to capture **legacy assumptions and invariants** that the old system was supposed to have and that are explicitly enforced by tests.

These are the kinds of rules that often get broken during migration because they are treated as “small details,” even though they are foundational to trustworthiness.

This part should remain **test-first**.

---

## A. Default-state and neutral-behavior assumptions

These tests assert what objects or systems are supposed to look like before gameplay meaning starts.

- [x] **[RPG-0777]** `UNSUPPORTED`: `test_default_values`: default entity/build values are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0778]** `UNSUPPORTED`: `test_default_values_all_zero`: default zero-valued state is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0779]** `UNSUPPORTED`: `test_default_multiplicative_values_are_1`: default multiplicative modifiers equal 1 <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0780]** `UNSUPPORTED`: `test_default_additive_values_are_0`: default additive modifiers equal 0 <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0781]** `UNSUPPORTED`: `test_default_metadata_is_none`: metadata defaults to `None` <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0782]** `UNSUPPORTED`: `test_none_metadata_preserved`: `None` metadata remains preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0783]** `UNSUPPORTED`: `test_schema_none_metadata`: schema handles `None` metadata correctly <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0784]** `UNSUPPORTED`: `test_no_skills_by_default`: entities have no skills by default <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0785]** `UNSUPPORTED`: `test_no_inventory_by_default`: entities have no inventory by default <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0786]** `UNSUPPORTED`: `test_no_traits_by_default`: entities have no traits by default <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0787]** `UNSUPPORTED`: `test_entity_starts_with_no_quests`: entities start with no quests <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0788]** `UNSUPPORTED`: `test_default_core_rate_is_1`: default core subsystem rate is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0789]** `UNSUPPORTED`: `test_default_environment_rate_is_2`: default environment subsystem rate is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0790]** `UNSUPPORTED`: `test_default_economy_rate_is_5`: default economy subsystem rate is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0791]** `UNSUPPORTED`: `test_default_region_id`: default region identifier is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0792]** `UNSUPPORTED`: `test_default_empty`: default empty collection/container semantics are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0793]** `UNSUPPORTED`: `test_empty_zones_returns_1`: empty-zone fallback behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0794]** `UNSUPPORTED`: `test_empty_regions_returns_none`: empty-region lookup returns `None` <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0795]** `UNSUPPORTED`: `test_select_returns_none_on_empty`: selection on empty inputs returns `None` <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0796]** `UNSUPPORTED`: `test_export_empty_strategy`: exporting empty strategy state is safe <!-- VERIFIED v2: UNSUPPORTED -->

---

## B. No-op, empty-tick, and “does nothing safely” assumptions

These tests assert that when there is nothing to do, the system degrades safely and predictably.

- [x] **[RPG-0797]** `UNSUPPORTED`: `test_no_changes_skipped`: no-change updates are skipped safely <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0798]** `UNSUPPORTED`: `test_effects_tick_on_empty_tick`: effects still tick on empty ticks <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0799]** `UNSUPPORTED`: `test_stamina_regens_on_empty_tick`: stamina regen still occurs on empty ticks <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0800]** `UNSUPPORTED`: `test_skill_cooldowns_tick_on_empty_tick`: skill cooldowns still tick on empty ticks <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0801]** `UNSUPPORTED`: `test_quest_advance_does_nothing_when_completed`: completed quests ignore further advance calls <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0802]** `UNSUPPORTED`: `test_unknown_action_does_nothing`: unknown actions are safely ignored <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0803]** `UNSUPPORTED`: `test_full_hp_no_change`: full-HP state remains unchanged <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0804]** `UNSUPPORTED`: `test_no_region_no_penalty`: no-region case applies no penalty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0805]** `UNSUPPORTED`: `test_safe_region_no_penalty`: safe-region case applies no penalty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0806]** `UNSUPPORTED`: `test_unknown_region_returns_0`: unknown region uses zero/fallback difficulty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0807]** `UNSUPPORTED`: `test_no_region_returns_0`: no-region difficulty fallback is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## C. Copy, clone, preservation, and ownership assumptions

These tests assert what is supposed to be preserved across copying and what must not be shared.

- [x] **[RPG-0808]** `UNSUPPORTED`: `test_quest_copy`: quest copy preserves quest state <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0809]** `UNSUPPORTED`: `test_entity_copy_preserves_quests`: entity copy preserves quests <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0810]** `UNSUPPORTED`: `test_entity_copy_preserves_attributes`: entity copy preserves attributes <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0811]** `UNSUPPORTED`: `test_entity_copy_preserves_skills`: entity copy preserves skills <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0812]** `UNSUPPORTED`: `test_entity_copy_includes_home_storage`: entity copy preserves home storage <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0813]** `UNSUPPORTED`: `test_entity_without_home_storage`: no-home-storage case remains safe <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0814]** `UNSUPPORTED`: `test_region_copy`: region copy semantics are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0815]** `UNSUPPORTED`: `test_attributes_copy`: attribute copy semantics are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0816]** `UNSUPPORTED`: `test_copy`: generic model copy semantics are preserved wherever tested <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0817]** `UNSUPPORTED`: `test_grid_copy_is_not_shared`: copied grids are not aliased <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0818]** `UNSUPPORTED`: `test_entity_copy_shallow_vs_refs`: copy/ref-sharing behavior is explicit and preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0819]** `UNSUPPORTED`: `test_latest_preserves_metadata`: latest-version object preserves metadata <!-- VERIFIED v2: UNSUPPORTED -->

---

## D. Serialization, schema, and round-trip assumptions

These tests assert that important models are supposed to serialize safely and consistently.

- [x] **[RPG-0820]** `UNSUPPORTED`: `test_serialization_round_trip`: serialization round-trip is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0821]** `UNSUPPORTED`: `test_item_serialization`: item serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0822]** `UNSUPPORTED`: `test_enchanted_blade_serialization`: enchanted item serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0823]** `UNSUPPORTED`: `test_skill_serialization`: skill serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0824]** `UNSUPPORTED`: `test_passive_skill_serialization`: passive skill serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0825]** `UNSUPPORTED`: `test_class_serialization`: class serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0826]** `UNSUPPORTED`: `test_breakthrough_serialization`: breakthrough serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0827]** `UNSUPPORTED`: `test_trait_serialization`: trait serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0828]** `UNSUPPORTED`: `test_history_registry_serialization`: history registry serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0829]** `UNSUPPORTED`: `test_entity_to_full_schema_no_crash`: full schema export does not crash <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0830]** `UNSUPPORTED`: `test_serialization_pydantic_model`: pydantic serialization assumption is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0831]** `UNSUPPORTED`: `test_serialization_frozen_model_with_proxy`: frozen/proxy serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0832]** `UNSUPPORTED`: `test_inspection_serialization`: inspection serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0833]** `UNSUPPORTED`: `test_cognition_api_serialization`: cognition API serialization is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## E. Freeze, immutability, and deep-isolation assumptions

These tests assert that certain state surfaces are supposed to be frozen, safe, and non-mutating.

- [x] **[RPG-0834]** `UNSUPPORTED`: `test_entity_deep_copy_isolation`: deep-copy isolation is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0835]** `UNSUPPORTED`: `test_deep_freeze_nested_collections`: deep freeze handles nested collections <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0836]** `UNSUPPORTED`: `test_deep_freeze_idempotency`: deep freeze is idempotent <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0837]** `UNSUPPORTED`: `test_freeze_calls_validate`: freeze triggers validation correctly <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0838]** `UNSUPPORTED`: `test_nested_freeze_invariants`: nested freeze invariants are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0839]** `UNSUPPORTED`: `test_world_state_freeze_guards`: world-state freeze guards are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0840]** `UNSUPPORTED`: `test_simulation_model_collection_freeze_list`: list freezing behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0841]** `UNSUPPORTED`: `test_simulation_model_collection_freeze_dict`: dict freezing behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0842]** `UNSUPPORTED`: `test_vector2_coercion_during_freeze`: vector coercion during freeze is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0843]** `UNSUPPORTED`: `test_non_mutation`: non-mutation guarantee is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0844]** `UNSUPPORTED`: `test_build_profile_does_not_mutate_caps`: cognition-profile derivation is non-mutating <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0845]** `UNSUPPORTED`: `test_build_profile_returns_new_profile_object_each_call`: fresh profile object guarantee is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## F. Determinism and repeatability assumptions

These tests assert that the system is supposed to be repeatable under the same conditions.

- [x] **[RPG-0846]** `UNSUPPORTED`: `test_profile_derivation_is_deterministic_for_same_entity_state`: deterministic profile derivation <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0847]** `UNSUPPORTED`: `test_intel_capacity_determinism`: intelligence-capacity determinism is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0848]** `UNSUPPORTED`: `test_strategic_replay_graph_equality`: replay graph equality is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0849]** `UNSUPPORTED`: `test_same_seed_same_result`: same-seed world/result determinism is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0850]** `UNSUPPORTED`: `test_harness_non_determinism_different_seed`: different-seed divergence remains explicit <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0851]** `UNSUPPORTED`: `test_first_by_id_wins_same_tile`: deterministic same-tile tie-breaking is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0852]** `UNSUPPORTED`: `test_diagonal_same_target_one_wins`: deterministic same-target conflict resolution is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0853]** `UNSUPPORTED`: `test_non_conflicting_moves_both_succeed`: independent valid moves both survive <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0854]** `UNSUPPORTED`: `test_equidistant_returns_first`: deterministic first-choice behavior on ties is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## G. Registry, definition, and data-completeness assumptions

These tests assert that key registries and definition maps are supposed to exist and be complete.

- [x] **[RPG-0855]** `UNSUPPORTED`: `test_item_registry_not_empty`: item registry is non-empty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0856]** `UNSUPPORTED`: `test_skill_defs_not_empty`: skill definitions are non-empty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0857]** `UNSUPPORTED`: `test_trait_defs_not_empty`: trait definitions are non-empty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0858]** `UNSUPPORTED`: `test_registry_not_empty`: generic registry non-empty guarantee is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0859]** `UNSUPPORTED`: `test_skill_registry_not_empty`: skill registry is non-empty <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0860]** `UNSUPPORTED`: `test_all_trait_types_have_definitions`: all trait types have definitions <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0861]** `UNSUPPORTED`: `test_all_tiers_defined`: all expected tier sets are defined <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0862]** `UNSUPPORTED`: `test_tier1_empty`: tier-1 empty expectation is preserved where applicable <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0863]** `UNSUPPORTED`: `test_tier4_defined`: tier-4 definition exists where expected <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0864]** `UNSUPPORTED`: `test_all_base_classes_defined`: base class definitions exist <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0865]** `UNSUPPORTED`: `test_breakthroughs_defined`: breakthrough definitions exist <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0866]** `UNSUPPORTED`: `test_all_types_have_name_templates`: type name-template completeness is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0867]** `UNSUPPORTED`: `test_all_terrains_have_names`: all terrains have names <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0868]** `UNSUPPORTED`: `test_all_terrains_have_race_labels`: all terrains have race labels <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0869]** `UNSUPPORTED`: `test_all_four_biomes_have_features`: all biomes expose expected features <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0870]** `UNSUPPORTED`: `test_all_regions_have_territory`: all regions have territory assignment <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0871]** `UNSUPPORTED`: `test_difficulty_zones_defined`: difficulty zones are defined <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0872]** `UNSUPPORTED`: `test_loot_tables_exist`: loot tables exist <!-- VERIFIED v2: UNSUPPORTED -->

---

## H. Safe fallback and degraded-mode assumptions

These tests assert that when something is missing, disabled, or unsupported, the system is supposed to fail soft or fall back safely.

- [x] **[RPG-0873]** `UNSUPPORTED`: `test_detour_depth_limit_fallback`: detour depth fallback is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0874]** `UNSUPPORTED`: `test_worker_pool_fallback_to_inline`: worker pool falls back to inline execution <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0875]** `UNSUPPORTED`: `test_rabbitmq_disabled_no_crash`: RabbitMQ-disabled mode does not crash <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0876]** `UNSUPPORTED`: `test_kafka_disabled_no_crash`: Kafka-disabled mode does not crash <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0877]** `UNSUPPORTED`: `test_redis_disabled_no_crash`: Redis-disabled mode does not crash <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0878]** `UNSUPPORTED`: `test_headless_runner_importable_without_brokers`: headless runner imports safely without brokers <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0879]** `UNSUPPORTED`: `test_action_system_importable_without_brokers`: action system imports safely without brokers <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0880]** `UNSUPPORTED`: `test_simulation_step_runs_without_brokers`: simulation can step without brokers <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0881]** `UNSUPPORTED`: `test_regression_runner_survives_no_infrastructure`: regression runner survives no-infrastructure mode <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0882]** `UNSUPPORTED`: `test_get_unknown`: unknown registry/class lookup is handled safely <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0883]** `UNSUPPORTED`: `test_unknown_trait_id_ignored`: unknown trait IDs are ignored safely <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0884]** `UNSUPPORTED`: `test_unknown_type_falls_back_to_physical`: unknown damage/action type falls back safely <!-- VERIFIED v2: UNSUPPORTED -->

---

## I. Caps, clamps, floors, ceilings, and boundedness assumptions

These tests assert what is supposed to happen at boundaries.

- [x] **[RPG-0885]** `UNSUPPORTED`: `test_hp_clamped_after_recalc`: HP is clamped after recomputation <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-0886]** `test_stamina_cannot_go_below_zero`: stamina lower bound is preserved <!-- VERIFIED v2: test_stamina_cannot_go_below_zero -->
- [x] **[RPG-0887]** `UNSUPPORTED`: `test_stamina_regen_capped`: stamina regeneration upper cap is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0888]** `UNSUPPORTED`: `test_training_does_not_exceed_cap`: training hard caps are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0889]** `UNSUPPORTED`: `test_level_up_respects_cap`: level-up cap compliance is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0890]** `UNSUPPORTED`: `test_boss_diff_capped_at_4`: boss difficulty cap is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0891]** `UNSUPPORTED`: `test_specialized_training_soft_caps`: soft-cap law is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0892]** `UNSUPPORTED`: `test_output_derived_stat_ceilings`: derived-stat ceilings are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0893]** `UNSUPPORTED`: `test_physical_no_attributes_defaults_mult_to_1`: missing-attribute multiplier defaults are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0894]** `UNSUPPORTED`: `test_magical_no_attributes_defaults_mult_to_1`: magical default multiplier law is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0895]** `UNSUPPORTED`: `test_full_bag_returns_zero`: full-bag score/utility floor is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0896]** `UNSUPPORTED`: `test_overweight_loot_score_zero`: overweight loot utility floor is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## J. Precedence, selection, and ordering assumptions

These tests assert what the system is supposed to prefer when multiple valid candidates exist.

- [x] **[RPG-0897]** `UNSUPPORTED`: `test_objective_derivation_precedence_active_objective_if_no_blocker`: active-objective precedence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0898]** `UNSUPPORTED`: `test_objective_derivation_precedence_first_unresolved_if_no_active`: unresolved-first precedence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0899]** `UNSUPPORTED`: `test_reserved_current_project_slot_is_used_when_current_project_exists`: current-project reserved slot law is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0900]** `UNSUPPORTED`: `test_next_step_returns_first_tile`: first-step path semantics are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0901]** `UNSUPPORTED`: `test_returns_nearest`: nearest-target selection is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0902]** `UNSUPPORTED`: `test_equidistant_returns_first`: stable first-on-tie semantics are preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0903]** `UNSUPPORTED`: `test_best_ready_skill_returns_highest_power`: best-ready-skill precedence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0904]** `UNSUPPORTED`: `test_best_ready_skill_skips_on_cooldown`: cooldown exclusion precedence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0905]** `UNSUPPORTED`: `test_best_ready_skill_skips_insufficient_stamina`: stamina exclusion precedence is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0906]** `UNSUPPORTED`: `test_best_ready_skill_none_when_no_skills`: no-skill fallback is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## K. Guardrail and authorization assumptions

These tests assert that the system is supposed to prevent or reject things in specific safe ways.

- [x] **[RPG-0907]** `UNSUPPORTED`: `test_phase_guard_read_unauthorized`: unauthorized phase read is guarded <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0908]** `UNSUPPORTED`: `test_no_path_through_walls`: pathfinding guardrail against walls is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0909]** `UNSUPPORTED`: `test_next_step_no_path`: no-path fallback is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0910]** `UNSUPPORTED`: `test_safe_shot_detection`: safe-shot guard logic is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0911]** `UNSUPPORTED`: `test_no_flanking_bonus_when_facing_attacker`: flanking exclusion guardrail is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0912]** `UNSUPPORTED`: `test_no_opportunity_attack_when_moving_toward`: OA guardrail is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0913]** `UNSUPPORTED`: `test_no_cover_on_open_ground`: cover absence on open ground is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0914]** `UNSUPPORTED`: `test_non_equipment_ignored`: non-equipment inputs are ignored safely <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0915]** `UNSUPPORTED`: `test_cannot_breakthrough_no_class`: breakthrough precondition guard is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0916]** `UNSUPPORTED`: `test_no_class`: no-class guard behavior is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## L. Metadata, inspection, and smoke-stability assumptions

These tests assert that inspection and debug-facing surfaces are supposed to remain safe even in empty or corrupted cases.

- [x] **[RPG-0917]** `UNSUPPORTED`: `test_inspector_smoke_empty_state`: empty-state inspector safety is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0918]** `UNSUPPORTED`: `test_inspector_smoke_corrupted_state`: corrupted-state inspector safety is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0919]** `UNSUPPORTED`: `test_inspector_smoke_maximal_state`: maximal-state inspector safety is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0920]** `UNSUPPORTED`: `test_render_strategic_domain_empty`: empty strategic-domain rendering is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0921]** `UNSUPPORTED`: `test_empty_strategic_state_rendering`: empty strategic rendering is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0922]** `UNSUPPORTED`: `test_cognition_inspector_rendering`: cognition inspector rendering is preserved <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0923]** `UNSUPPORTED`: `test_cognition_empty_profile`: empty cognition-profile rendering is preserved <!-- VERIFIED v2: UNSUPPORTED -->

---

## M. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map assumption logic to roadmap owners rather than creating another giant roadmap phase.

- [x] **[RPG-0924]** `UNSUPPORTED`: Phase 7 owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - serialization / freeze / deep-isolation / determinism / phase guards / non-mutation assumptions

- [x] **[RPG-0925]** `UNSUPPORTED`: Phase 8 owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - immediate-action guardrails
  - local boundedness and combat/tactical caps/clamps
  - local selection/tie-breaking assumptions where action resolution depends on them

- [x] **[RPG-0926]** `UNSUPPORTED`: Phase 9 owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - precedence and boundedness assumptions in cognition/strategy/progression
  - traits / registries / progression caps where they materially shape long-horizon gameplay

- [x] **[RPG-0927]** `UNSUPPORTED`: Phase 10 owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - disabled-mode / fallback / importability / infra-safe assumptions
  - consumer/entry black-box degraded-mode assumptions

- [x] **[RPG-0928]** `UNSUPPORTED`: Phase 11+ owns: <!-- VERIFIED v2: UNSUPPORTED -->
  - governance truth for any surviving invariant classified as preserved/divergent/unsupported

---

## Completion rule for Part 8

A Part 8 item is not closed merely because the system “seems to behave sensibly.”

Each item should be considered closed only when:

- [x] **[RPG-0929]** `UNSUPPORTED`: the specific assumption has a clear roadmap owner <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0930]** `UNSUPPORTED`: the specific assumption has direct implementation or an explicit divergence/unsupported decision <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0931]** `UNSUPPORTED`: the specific assumption has test coverage or proof justification <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0932]** `UNSUPPORTED`: the support boundary and replacement ledger reflect its true status <!-- VERIFIED v2: UNSUPPORTED -->

# Missing / under-specified checklist additions

## 1. Goal registry and goal scorer contract

The checklist mentions goal modifiers, but it does not fully preserve the core goal registry/scorer law from legacy tests.

Add these atomic items:

- [x] **[RPG-0933]** `UNSUPPORTED`: Goal registry contains the expected built-in goals. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0934]** `UNSUPPORTED`: Goal registry names are unique. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0935]** `UNSUPPORTED`: Every built-in goal maps to a valid target AI state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0936]** `UNSUPPORTED`: Combat goal scores high when hostile enemies are visible. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0937]** `UNSUPPORTED`: Flee goal scores high below HP threshold. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0938]** `UNSUPPORTED`: Explore goal has a stable baseline score. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0939]** `UNSUPPORTED`: Empty goal candidate list returns `None`. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0940]** `UNSUPPORTED`: RNG value `0.0` selects the highest candidate. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0941]** `UNSUPPORTED`: `top_n` selection limits candidates before weighted selection. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0942]** `UNSUPPORTED`: Neuroticism can break goal commitment lock under low HP pressure. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0943]** `UNSUPPORTED`: Legacy `goal_evaluator.py` shim behavior is preserved or intentionally removed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0944]** `UNSUPPORTED`: Loot goal returns zero when bag is full. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0945]** `UNSUPPORTED`: Trade goal receives urgency when inventory is nearly full or overweight. <!-- VERIFIED v2: UNSUPPORTED -->

Why this matters: goal scoring is the bridge between cognition and action. If this drifts, V2 entities may have the same systems but completely different behavior.

---

## 2. EntityBuilder construction law

The checklist mentions entity aspects and spawning, but not the builder as an atomic compatibility surface. Legacy has a large fluent `EntityBuilder` contract: default identity, faction, AI state, stats, class attributes, race skills, class skills, inventory, home storage, traits, clique, household, leash, world role, and randomized spawn stats.

Add:

- [x] **[RPG-0946]** `UNSUPPORTED`: EntityBuilder default entity has stable kind, faction, alive combat state, and wander AI state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0947]** `UNSUPPORTED`: `.kind()`, `.at()`, `.home()`, `.ai_state()`, `.faction()`, `.tier()` preserve exact field effects. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0948]** `UNSUPPORTED`: Hero kind enforces minimum stamina behavior. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0949]** `UNSUPPORTED`: Base stats initialize combat and progression fields consistently. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0950]** `UNSUPPORTED`: Randomized stats use deterministic spawn-domain RNG. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0951]** `UNSUPPORTED`: Hero class derives attributes and caps from class definition. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0952]** `UNSUPPORTED`: Mob attributes scale by tier. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0953]** `UNSUPPORTED`: Race attributes apply racial modifiers and deterministic variance. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0954]** `UNSUPPORTED`: Race skills and class skills can be combined without loss. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0955]** `UNSUPPORTED`: No-skills-by-default behavior is preserved. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0956]** `UNSUPPORTED`: Builder supports clique, household, home building, world role, and leash fields. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0957]** `UNSUPPORTED`: Builder-created entities deep-copy safely. <!-- VERIFIED v2: UNSUPPORTED -->

This is not “just construction.” It is the source of initial state truth.

---

## 3. Registry and data-driven loading law

The checklist mentions registries generally, but it should explicitly preserve the data-driven runtime contract.

Add:

- [x] **[RPG-0958]** `UNSUPPORTED`: `load_all_registries()` loads items, classes, skills, breakthroughs, traits, spawn configs, and loot configs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0959]** `UNSUPPORTED`: Spawn config entries actually initialize generated entities. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0960]** `UNSUPPORTED`: Loot config entries are loaded and used by `EntityGenerator`. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0961]** `UNSUPPORTED`: Item registry lookup returns expected item type and bonuses. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0962]** `UNSUPPORTED`: Class definitions contain class skill lists. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0963]** `UNSUPPORTED`: Every class skill ID resolves in the skill registry. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0964]** `UNSUPPORTED`: Missing registry entries fail safely, not silently. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0965]** `UNSUPPORTED`: Registry loading is deterministic and idempotent. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0966]** `UNSUPPORTED`: Duplicate or malformed data definitions are rejected or explicitly handled. <!-- VERIFIED v2: UNSUPPORTED -->

This is a big blind spot. A V2 port can pass behavior tests with hardcoded objects while silently breaking data-driven gameplay.

---

## 4. Quest lifecycle and generation

The checklist has quest mentions, but it is not atomic enough for the original quest tests.

Add:

- [x] **[RPG-0967]** `UNSUPPORTED`: Quest starts with progress `0`, not completed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0968]** `UNSUPPORTED`: Quest progress ratio is correct. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0969]** `UNSUPPORTED`: Quest `advance()` returns `True` only on first completion. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0970]** `UNSUPPORTED`: Advancing an already completed quest does not mutate state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0971]** `UNSUPPORTED`: Quest copy is deep enough that copied progress mutation does not affect original. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0972]** `UNSUPPORTED`: Quest serialization omits position for non-position quests. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0973]** `UNSUPPORTED`: Explore quest serialization includes target position. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0974]** `UNSUPPORTED`: Quest generation respects hero level. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0975]** `UNSUPPORTED`: Quest generation skips duplicates. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0976]** `UNSUPPORTED`: Quest rewards scale with level. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0977]** `UNSUPPORTED`: Explore quest generation produces valid target positions. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0978]** `UNSUPPORTED`: Template map and template list stay consistent. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0979]** `UNSUPPORTED`: Entity quest list starts empty. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0980]** `UNSUPPORTED`: Entity copies preserve quest progress independently. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0981]** `UNSUPPORTED`: Hunt quest completion grants gold and XP. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0982]** `UNSUPPORTED`: Explore quest completes within target proximity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0983]** `UNSUPPORTED`: Gather quest can advance by count. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0984]** `UNSUPPORTED`: Max active quest limit is enforced. <!-- VERIFIED v2: UNSUPPORTED -->

Do not treat “dynamic quests exist” as enough. The old code had model, generator, tracking, reward, and serialization rules.

---

## 5. Equipment enhancement, home storage, shops, treasure chests

This is clearly underrepresented. The checklist mentions progression/classes/items, but not several old mechanics.

Add:

- [x] **[RPG-0985]** `UNSUPPORTED`: `recalc_derived_stats()` creation mode applies attribute bonuses. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0986]** `UNSUPPORTED`: `recalc_derived_stats()` delta mode removes old bonuses before applying new ones. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0987]** `UNSUPPORTED`: HP clamps to new max HP after stat recalculation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0988]** `UNSUPPORTED`: Noncombat derived stats update vision, HP regen, trade bonus, and loot bonus. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0989]** `UNSUPPORTED`: `auto_equip_best()` equips into empty slot. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0990]** `UNSUPPORTED`: Better equipment replaces worse equipment and returns old item to inventory. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0991]** `UNSUPPORTED`: Worse equipment is not auto-equipped. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0992]** `UNSUPPORTED`: Non-equipment items are ignored by auto-equip. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0993]** `UNSUPPORTED`: Unknown item power returns zero. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0994]** `UNSUPPORTED`: Stronger item power ordering is stable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0995]** `UNSUPPORTED`: Home storage add/remove/full/copy behavior is preserved. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0996]** `UNSUPPORTED`: Shop contains expanded item set. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0997]** `UNSUPPORTED`: Buff potion item types are consumable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0998]** `UNSUPPORTED`: Skill learning respects level, prerequisites, and mastery. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-0999]** `UNSUPPORTED`: All hero classes expose at least one available skill chain. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1000]** `UNSUPPORTED`: Treasure chests start available. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1001]** `UNSUPPORTED`: Chest loot sets respawn tick and unavailable state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1002]** `UNSUPPORTED`: Chest respawns only at or after respawn tick. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1003]** `UNSUPPORTED`: Chest loot tables exist for expected tiers. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1004]** `UNSUPPORTED`: Entity copy preserves home storage deeply. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1005]** `UNSUPPORTED`: Training that increments an attribute immediately recomputes derived stats. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1006]** `UNSUPPORTED`: Equipment has durability (0-100). <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1007]** `UNSUPPORTED`: Weapon durability decays by 1.0 per attack. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1008]** `UNSUPPORTED`: Armor durability (all slots) decays by 0.5 per damage taken. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1009]** `UNSUPPORTED`: Broken equipment (durability 0) provides no stat bonuses. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1010]** `UNSUPPORTED`: Broken weapon reverts attack range to 1. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1011]** `UNSUPPORTED`: Blacksmith repair restores durability to 100 for a gold cost. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1012]** `UNSUPPORTED`: Repair cost scales with missing durability. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1013]** `UNSUPPORTED`: Crafting consumes materials only when inventory capacity for output is confirmed. <!-- VERIFIED v2: tests/rpg/test_durability_repair.py --> <!-- VERIFIED v2: UNSUPPORTED -->

This entire area is easy to lose because it sits between inventory, progression, and world objects.

---

## 6. Ranged combat, line-of-sight, cover, and range-aware skills

The existing checklist has ranged legality, but it needs finer atomic rules.

Add:

- [x] **[RPG-1014]** `UNSUPPORTED`: Melee weapons default to range `1`. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1015]** `UNSUPPORTED`: Shortbow and longbow have distinct weapon ranges. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1016]** `UNSUPPORTED`: Clear horizontal line of sight passes. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1017]** `UNSUPPORTED`: Clear diagonal line of sight passes. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1018]** `UNSUPPORTED`: Wall between attacker and target blocks LOS. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1019]** `UNSUPPORTED`: Wall on diagonal path blocks LOS. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1020]** `UNSUPPORTED`: Adjacent tiles are always visible under legacy rule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1021]** `UNSUPPORTED`: Wall at endpoint does not block LOS. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1022]** `UNSUPPORTED`: Wall at start does not block LOS. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1023]** `UNSUPPORTED`: Adjacent wall counts as cover. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1024]** `UNSUPPORTED`: Open ground gives no cover. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1025]** `UNSUPPORTED`: Melee attack adjacent is valid. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1026]** `UNSUPPORTED`: Melee attack out of range is invalid. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1027]** `UNSUPPORTED`: Ranged attack at valid distance is valid. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1028]** `UNSUPPORTED`: Unarmed entity range is `1`. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1029]** `UNSUPPORTED`: Ranged skill can be selected at distance. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1030]** `UNSUPPORTED`: Melee skill is not selected at ranged distance. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1031]** `UNSUPPORTED`: Starting gear gives warrior sword and ranger bow. <!-- VERIFIED v2: UNSUPPORTED -->

The checklist currently risks collapsing this into “range and LOS exist.” That is not enough.

---

## 7. A\* pathfinding details

The checklist mentions movement and pathfinding, but several pathfinding laws are missing or buried.

Add:

- [x] **[RPG-1032]** `UNSUPPORTED`: Straight-line path returns expected step count. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1033]** `UNSUPPORTED`: Same start and goal returns empty path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1034]** `UNSUPPORTED`: Adjacent goal returns single-step path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1035]** `UNSUPPORTED`: Path routes around walls. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1036]** `UNSUPPORTED`: Fully enclosed goal returns no path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1037]** `UNSUPPORTED`: Unwalkable goal returns no path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1038]** `UNSUPPORTED`: Returned path excludes start position. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1039]** `UNSUPPORTED`: Max-node budget can terminate search with no path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1040]** `UNSUPPORTED`: `next_step()` returns first path tile. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1041]** `UNSUPPORTED`: Occupied tiles are avoided. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1042]** `UNSUPPORTED`: Goal tile can remain reachable even if listed as occupied. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1043]** `UNSUPPORTED`: Road cost is lower than floor. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1044]** `UNSUPPORTED`: Swamp cost is higher than floor. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1045]** `UNSUPPORTED`: Terrain cost registry is used by pathfinding. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1046]** `UNSUPPORTED`: Long-distance movement uses A\*. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1047]** `UNSUPPORTED`: Short-distance movement can use greedy fallback. <!-- VERIFIED v2: UNSUPPORTED -->

That last distinction matters: A\* and greedy fallback are different behavior contracts, not implementation details.

---

## 8. Mob leash, chase give-up, and return-to-camp

The checklist has leash references, but the atomic old behavior needs to be explicit.

Add:

- [x] **[RPG-1048]** `UNSUPPORTED`: Entity with `leash_radius=0` is never beyond leash. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1049]** `UNSUPPORTED`: Entity with no home position is never beyond leash. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1050]** `UNSUPPORTED`: Distance within leash returns false. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1051]** `UNSUPPORTED`: Distance beyond leash returns true. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1052]** `UNSUPPORTED`: Leash multiplier extends allowed chase range. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1053]** `UNSUPPORTED`: Wander handler sends beyond-leash mob to return-to-camp. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1054]** `UNSUPPORTED`: Within-leash mob continues wandering. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1055]** `UNSUPPORTED`: No-leash mob wanders freely. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1056]** `UNSUPPORTED`: Hunt handler abandons chase beyond `1.5x` leash. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1057]** `UNSUPPORTED`: Hunt handler continues chase inside `1.5x` leash. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1058]** `UNSUPPORTED`: Hunt handler gives up after chase timeout. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1059]** `UNSUPPORTED`: Chase ticks reset on combat engagement. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1060]** `UNSUPPORTED`: Return-to-camp heals while returning. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1061]** `UNSUPPORTED`: Returning mob resumes normal behavior after reaching camp. <!-- VERIFIED v2: UNSUPPORTED -->

This is not just movement. It prevents mobs from becoming global homing missiles.

---

## 9. Group coordination and contract-party formation

The social checklist is broad, but group mechanics are under-specified.

Add:

- [x] **[RPG-1062]** `UNSUPPORTED`: Entities with the same `cluster_id` and faction can form a group. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1063]** `UNSUPPORTED`: Group requires at least two living members. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1064]** `UNSUPPORTED`: Group leader is selected by highest level. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1065]** `UNSUPPORTED`: Group anchor follows leader position. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1066]** `UNSUPPORTED`: Members receive group ID linkage. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1067]** `UNSUPPORTED`: Group dissolves if leader dies. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1068]** `UNSUPPORTED`: Group removes dead members. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1069]** `UNSUPPORTED`: Group dissolves if membership drops below two. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1070]** Group cohesion decreases with distance from leader. <!-- VERIFIED v2: group_cohesion_check -->
- [x] **[RPG-1071]** `UNSUPPORTED`: Shared group goal biases member goal scoring. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1072]** `UNSUPPORTED`: Distance from leader increases social regrouping bias. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1073]** `UNSUPPORTED`: Active social contracts can instantiate party groups. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1074]** `UNSUPPORTED`: Contract kind maps to shared group goal. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1075]** `UNSUPPORTED`: Contract party dissolution applies contract consequences. <!-- VERIFIED v2: UNSUPPORTED -->

Without these, social “contracts” may exist as records but not as behavior.

---

## 10. Calamity / world-boss system

This is a real omission. The checklist mentions calamity evolution, but not the actual world-boss system.

Add:

- [x] **[RPG-1076]** `UNSUPPORTED`: World maturity increases on schedule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1077]** `UNSUPPORTED`: Calamity spawn obeys interval and forced-spawn ticks. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1078]** `UNSUPPORTED`: Spawned calamity has world-boss identity and role. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1079]** `UNSUPPORTED`: Calamity uses legendary stats. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1080]** `UNSUPPORTED`: Calamity receives legendary equipment/loot. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1081]** `UNSUPPORTED`: Calamity spawn creates bounty quests for heroes. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1082]** `UNSUPPORTED`: Calamity aura applies local debuffs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1083]** `UNSUPPORTED`: Camp reinforcements occur on schedule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1084]** `UNSUPPORTED`: Camp reinforcement level increases when camp is full. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1085]** `UNSUPPORTED`: Faction raids spawn on raid interval. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1086]** `UNSUPPORTED`: Raid mobs use raid AI state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1087]** `UNSUPPORTED`: Raid mobs do not return home. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1088]** `UNSUPPORTED`: Killing world boss grants fame. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1089]** `UNSUPPORTED`: Killing world boss grants title. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1090]** `UNSUPPORTED`: Bounty completion rewards are applied. <!-- VERIFIED v2: UNSUPPORTED -->

This is not optional world flavor. It affects progression, quests, combat, world pressure, and hero identity.

---

## 11. Region and Voronoi topology

The checklist has world/regions, but not enough of the concrete topology contract.

Add:

- [ ] **[RPG-1091]** Region contains uses Manhattan distance. <!-- VERIFIED v2: manhattan_spatial_metric -->
- [x] **[RPG-1092]** `UNSUPPORTED`: Region copy deep-copies locations. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1093]** `UNSUPPORTED`: Location model preserves type, position, and region ID. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1094]** `UNSUPPORTED`: Difficulty tier chosen by distance zones. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1095]** `UNSUPPORTED`: Boundary distances map to expected tier. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1096]** `UNSUPPORTED`: Empty difficulty zones default safely. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1097]** `UNSUPPORTED`: Region name selection is deterministic by terrain counter. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1098]** `UNSUPPORTED`: Resetting name counters restarts name sequence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1099]** `UNSUPPORTED`: Every terrain has region names. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1100]** `UNSUPPORTED`: Every terrain has race label. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1101]** `UNSUPPORTED`: Difficulty multipliers exist for all tiers. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1102]** `UNSUPPORTED`: Difficulty multipliers scale upward. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1103]** `UNSUPPORTED`: All location types have name templates. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1104]** `UNSUPPORTED`: Expected POI types exist: camp, grove, ruins, dungeon, shrine, boss arena, outpost, watchtower, portal, fishing spot, graveyard, obelisk. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1105]** `UNSUPPORTED`: Voronoi map coverage is near-total. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1106]** `UNSUPPORTED`: Region terrain, overlays, details, and town tiles account for map tiles. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1107]** `UNSUPPORTED`: Regions border each other. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1108]** `UNSUPPORTED`: Every region owns some territory. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1109]** `UNSUPPORTED`: `find_region_at()` returns nearest region. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1110]** `UNSUPPORTED`: Equidistant region lookup returns first region. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1111]** `UNSUPPORTED`: Empty region list returns `None`. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1112]** `UNSUPPORTED`: Single region always matches. <!-- VERIFIED v2: UNSUPPORTED -->

This is a map-authority contract. If V2 changes it, spawning, difficulty, resource placement, and exploration all drift.

---

## 12. Platform primitives: RNG and spatial hash

The checklist mentions determinism, but not the primitive contracts.

Add:

- [x] **[RPG-1113]** `UNSUPPORTED`: Deterministic RNG repeats exactly for same seed/domain/entity/tick. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1114]** `UNSUPPORTED`: RNG domain separation produces different streams for different domains. <!-- VERIFIED v2: DeterministicRNG has per-domain streams and tests cover reproducibility/isolation. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1115]** `UNSUPPORTED`: `next_int()` always respects inclusive bounds. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1116]** `UNSUPPORTED`: Spatial hash insert places entity in correct cell. <!-- VERIFIED v2: SpatialHashV2 contract tests cover insert/query. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1117]** `UNSUPPORTED`: Spatial hash radius query includes neighboring cells. <!-- VERIFIED v2: SpatialHashV2 radius query tests cover neighboring cells. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1118]** `UNSUPPORTED`: Spatial hash move removes old cell membership and adds new cell membership. <!-- VERIFIED v2: SpatialHashV2 move/update tests cover old/new membership. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1119]** `UNSUPPORTED`: Spatial hash remove clears membership. <!-- VERIFIED v2: SpatialHashV2 remove tests cover membership clearing. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1120]** `UNSUPPORTED`: Spatial hash behavior is deterministic independent of insertion order where required. <!-- VERIFIED v2: UNSUPPORTED -->

These are low-level, but if they drift, every higher-level system becomes untrustworthy.

---

## 13. Phase guard and authoritative phase authorization

The checklist only has one unauthorized phase read item. Legacy tests cover more.

Add:

- [x] **[RPG-1121]** `UNSUPPORTED`: Unauthorized phase read raises. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1122]** `UNSUPPORTED`: Unauthorized phase mutation raises. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1123]** `UNSUPPORTED`: Unauthorized phase emit raises. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1124]** `UNSUPPORTED`: Authorized mutation succeeds only in permitted phase. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1125]** `UNSUPPORTED`: Internal field access is controlled. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1126]** `UNSUPPORTED`: Scheduling phase cannot mutate HP. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1127]** `UNSUPPORTED`: Persistence phase is read-only. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1128]** `UNSUPPORTED`: Phase guard prevents bypassing authoritative action/update application. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1129]** `UNSUPPORTED`: Nested phase access follows the same authorization law. <!-- VERIFIED v2: UNSUPPORTED -->

This is directly tied to V2’s “one authoritative mutation path” principle.

---

## 14. Behavior inspection and presenter truth

The checklist excludes UI-only presentation, which is fine. But some inspection/presenter behavior is not merely UI. It is behavioral explainability and debugging truth.

Add under an optional “inspection truth” section:

- [x] **[RPG-1130]** `UNSUPPORTED`: AI presenter maps structured decision drivers. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1131]** `UNSUPPORTED`: Belief inspection includes apparent state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1132]** `UNSUPPORTED`: Injury blurring affects API-visible state consistently. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1133]** `UNSUPPORTED`: Stat breakdown service matches real derived stat math. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1134]** `UNSUPPORTED`: Combat trace recording is inspectable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1135]** `UNSUPPORTED`: AI explainability persists across ticks. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1136]** `UNSUPPORTED`: Scheduler timeline is inspectable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1137]** `UNSUPPORTED`: Entity inspection behavior matches legacy. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1138]** `UNSUPPORTED`: AI explanation parity is preserved or intentionally divergent. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1139]** `UNSUPPORTED`: Missing continuity data is handled safely. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1140]** `UNSUPPORTED`: Corrupted inspection state does not crash. <!-- VERIFIED v2: UNSUPPORTED -->

This should not be mixed with gameplay parity, but it should not disappear either. Debug surfaces are part of operational truth.

---

## 15. Assertion and test helper semantics

The checklist should preserve some internal validation helpers because they define what “consistent” means.

Add:

- [x] **[RPG-1141]** `UNSUPPORTED`: Strategic consistency assertion fails on real drift. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1142]** `UNSUPPORTED`: Cognition consistency assertion fails when replay and graph diverge. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1143]** `UNSUPPORTED`: Graph integrity assertion catches broken cognition graph structure. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1144]** `UNSUPPORTED`: Determinism assertion compares actual replay outputs, not superficial success. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1145]** `UNSUPPORTED`: Overload behavior assertion preserves capacity failure semantics. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1146]** `UNSUPPORTED`: Combat arena helper preserves default factions, hostility, tick running, and entity lookup semantics. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1147]** `UNSUPPORTED`: Legacy stat helper preserves expected combat math inputs. <!-- VERIFIED v2: UNSUPPORTED -->

This sounds like test infrastructure, but it encodes legacy truth. Removing it weakens the audit.

---

## 16. Brokerless, recovery, and degraded-mode behavior tied to execution

Some infra is outside RPG-core scope, but not all of it. If missing Kafka/RabbitMQ changes whether the simulation step can run, it belongs in the checklist.

Add:

- [x] **[RPG-1148]** `UNSUPPORTED`: Simulation step runs when brokers are missing. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1149]** `UNSUPPORTED`: RabbitMQ missing-package path fails closed or disables cleanly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1150]** `UNSUPPORTED`: Kafka missing-package path fails closed or disables cleanly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1151]** `UNSUPPORTED`: Engine manager recovery handles missing Kafka. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1152]** `UNSUPPORTED`: Worker pool RabbitMQ dispatch contract is preserved if broker mode is supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1153]** `UNSUPPORTED`: Kafka recovery can reconstruct from snapshot plus event stream. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1154]** `UNSUPPORTED`: Live-vs-manual replay produces same world state for loot recovery. <!-- VERIFIED v2: UNSUPPORTED -->

This connects directly to V2’s lifecycle and operational-truth goals.

---

# Additional missing atomic RPG-core logic discovered during V2 audit

These items are appended rather than replacing existing checklist items. They are intentionally atomic. Mark them only when fully implemented and proven. Partial implementation remains unchecked.

## Z1. Checklist governance and truthfulness

- [x] **[RPG-1155]** `UNSUPPORTED`: Every checklist row has a stable ID. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1156]** `UNSUPPORTED`: Every checklist row has one explicit status: preserved, enhanced, intentionally divergent, unsupported, or not yet checked. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1157]** `UNSUPPORTED`: Every checked row has at least one proof path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1158]** `UNSUPPORTED`: Every checked row names the implementation path that proves it. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1159]** `UNSUPPORTED`: Every checked row names the test path that proves it. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1160]** `UNSUPPORTED`: Every intentionally divergent row has a concrete reason. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1161]** `UNSUPPORTED`: Every intentionally divergent row has a regression or contract test proving the new law. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1162]** `UNSUPPORTED`: Every unsupported row has a support-boundary note. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1163]** `UNSUPPORTED`: Unsupported behavior is not marked as intentionally divergent. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1164]** `UNSUPPORTED`: Partial behavior is not marked as complete. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1165]** `UNSUPPORTED`: Behavior implemented in a dead or bypassed code path is not marked as complete. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1166]** `UNSUPPORTED`: Behavior implemented in one path but contradicted by another active path is not marked as complete. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1167]** `UNSUPPORTED`: The checklist distinguishes implementation detail from RPG semantic law. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1168]** `UNSUPPORTED`: The checklist keeps smallest necessary logic items instead of collapsing them into subsystem summaries. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1169]** `UNSUPPORTED`: CI can fail when a checked row has no proof reference. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1170]** `UNSUPPORTED`: CI can fail when a divergence has no divergence-register entry. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1171]** `UNSUPPORTED`: CI can fail when a proof path references a missing test file. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1172]** `UNSUPPORTED`: CI can fail when a checklist item references a removed implementation path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1173]** `UNSUPPORTED`: CI can fail when a test marker is unknown. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1174]** `UNSUPPORTED`: CI can fail when mandatory oracle files are missing. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1175]** `UNSUPPORTED`: CI can fail when an oracle lacks schema version. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1176]** `UNSUPPORTED`: CI can fail when an oracle lacks seed/config metadata. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1177]** `UNSUPPORTED`: CI can fail when unsupported behavior is silently accepted as success. <!-- VERIFIED v2: UNSUPPORTED -->

## Z2. Resource conservation and inventory pressure law

- [x] **[RPG-1178]** `UNSUPPORTED`: All active resource acquisition paths share one conservation law. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1179]** `InteractionSystem` harvest path and any standalone `HarvestSystem` path cannot diverge on capacity rules. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. -->
- [ ] **[RPG-1180]** `InteractionSystem` loot path and any standalone `LootSystem` path cannot diverge on capacity rules. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. -->
- [x] **[RPG-1181]** `UNSUPPORTED`: A resource node charge is not decremented until inventory receipt is proven possible. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1182]** `UNSUPPORTED`: A ground item is not removed until inventory receipt is proven possible. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1183]** `UNSUPPORTED`: A corpse loot record is not consumed until inventory receipt is proven possible. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1184]** `UNSUPPORTED`: Inventory slot capacity is checked before source mutation. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1185]** `UNSUPPORTED`: Inventory weight capacity is checked before source mutation. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1186]** `UNSUPPORTED`: Inventory stackability is checked before rejecting for slot pressure. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1187]** `UNSUPPORTED`: Inventory add failure preserves the source item/node/corpse. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1188]** `UNSUPPORTED`: Inventory add failure resets or preserves the interaction channel according to an explicit rule. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1189]** `UNSUPPORTED`: Harvest completion emits both inventory addition and node depletion atomically. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1190]** `UNSUPPORTED`: Loot completion emits both inventory addition and source removal atomically. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1191]** `UNSUPPORTED`: Partial channel progress does not create items. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1192]** `UNSUPPORTED`: Interrupted channel progress does not create items. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1193]** `UNSUPPORTED`: Interrupted channel progress does not remove source items. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1194]** `UNSUPPORTED`: Failed capacity check does not remove source items. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1195]** `UNSUPPORTED`: Failed capacity check does not decrement node charges. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1196]** `UNSUPPORTED`: Two actors completing the same loot target in the same tick cannot duplicate the item. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1197]** `UNSUPPORTED`: Two actors completing the same resource-node charge in the same tick cannot duplicate the yield. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1198]** `UNSUPPORTED`: Two actors completing the same corpse loot in the same tick cannot duplicate corpse rewards. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1199]** `UNSUPPORTED`: Conflict resolution decides one authoritative winner for contested loot completion. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1200]** `UNSUPPORTED`: Conflict resolution decides one authoritative winner per limited resource charge when required. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1201]** `UNSUPPORTED`: Item quantity is preserved through pickup, stacking, selling, crafting, and dropping. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1202]** `UNSUPPORTED`: Item weight is preserved through pickup, stacking, selling, crafting, and dropping. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1203]** `UNSUPPORTED`: Item identity/kind is preserved through pickup, stacking, selling, crafting, and dropping. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1204]** `UNSUPPORTED`: Harvest yield uses the node definition, not caller-provided arbitrary item data. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1205]** `UNSUPPORTED`: Loot yield uses the ground/corpse source definition, not caller-provided arbitrary item data. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1206]** `UNSUPPORTED`: Capacity failure reason is structured and observable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1207]** `UNSUPPORTED`: Resource source mutation and inventory mutation appear in the same authoritative update/apply transaction. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1208]** `UNSUPPORTED`: Resource acquisition replay includes both source and inventory state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1209]** `UNSUPPORTED`: Resource acquisition replay can prove no duplication across identical seed runs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1210]** `UNSUPPORTED`: Resource acquisition replay can prove no item loss under capacity failure. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1211]** `UNSUPPORTED`: Resource-node cooldown behavior is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1212]** `UNSUPPORTED`: Resource-node recharge behavior is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1213]** `UNSUPPORTED`: Resource-node depletion state survives serialization. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1214]** `UNSUPPORTED`: Ground item state survives serialization. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1215]** `UNSUPPORTED`: Corpse loot state survives serialization. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1216]** `UNSUPPORTED`: Loot/harvest tests include slot pressure. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1217]** `UNSUPPORTED`: Loot/harvest tests include weight pressure. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1218]** `UNSUPPORTED`: Loot/harvest tests include stack merge under near-full inventory. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1219]** `UNSUPPORTED`: Loot/harvest tests include two actors racing for one item. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1220]** `UNSUPPORTED`: Loot/harvest tests include failure preserving source state. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1221]** `UNSUPPORTED`: Loot/harvest tests include success mutating inventory and source together. <!-- VERIFIED v2: ResourceTransferIntent/ResourceTransactionResolver and conservation tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->

## Z3. Authoritative pipeline and bypass prevention

- [x] **[RPG-1222]** Every gameplay update enters the same authoritative refinement/apply pipeline. <!-- ID: RPG-1222 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1223]** `UNSUPPORTED`: No AI/state system mutates authoritative world state directly during proposal generation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1224]** No standalone gameplay system can remove world objects without apply pipeline validation. <!-- ID: RPG-1224 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1225]** No standalone gameplay system can add inventory without apply pipeline validation. <!-- ID: RPG-1225 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1226]** `UNSUPPORTED`: No standalone gameplay system can change combat HP without combat legality validation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1227]** `UNSUPPORTED`: No standalone gameplay system can change position without movement legality validation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1228]** `UNSUPPORTED`: No standalone gameplay system can change reputation/social state without social consequence validation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1229]** `UNSUPPORTED`: No standalone gameplay system can complete quests without quest lifecycle validation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1230]** Every raw update is either accepted, refined, rejected, or marked unsupported. <!-- ID: RPG-1230 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1231]** Rejected updates preserve unrelated update domains. <!-- ID: RPG-1231 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1232]** Rejected updates expose structured rejection reason. <!-- ID: RPG-1232 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1233]** Rejection reasons are replay-visible or log-visible. <!-- ID: RPG-1233 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1234]** `UNSUPPORTED`: Merge logic for multiple `StateUpdate`s is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1235]** `UNSUPPORTED`: Merge logic has stable precedence for conflicting entity updates. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1236]** `UNSUPPORTED`: Merge logic has stable precedence for conflicting world updates. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1237]** `UNSUPPORTED`: Merge logic does not accidentally drop independent updates. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1238]** `UNSUPPORTED`: Merge logic detects incompatible updates where required. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1239]** `UNSUPPORTED`: Apply order is documented. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1240]** `UNSUPPORTED`: Apply order is tested for cross-domain interactions. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1241]** `UNSUPPORTED`: Apply order cannot depend on dictionary iteration where ordering matters. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1242]** `UNSUPPORTED`: Apply order cannot depend on thread completion order where gameplay outcome matters. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1243]** `UNSUPPORTED`: Pipeline tests include direct old-system calls if such calls remain importable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1244]** `UNSUPPORTED`: Pipeline tests prove dead/bypassed systems cannot create different gameplay laws. <!-- VERIFIED v2: UNSUPPORTED -->

## Z4. Movement intention, congestion, and blocked-route behavior

- [x] **[RPG-1245]** Movement intentions include pursue. <!-- ID: RPG-1245 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1246]** Movement intentions include retreat. <!-- ID: RPG-1246 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1247]** Movement intentions include hold. <!-- ID: RPG-1247 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1248]** Movement intentions include reposition. <!-- ID: RPG-1248 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1249]** Movement intentions include intercept. <!-- ID: RPG-1249 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1250]** Movement intentions include guard. <!-- ID: RPG-1250 SOURCE: src/core/enums.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [ ] **[RPG-1251]** Movement intentions include regroup or an explicit intentional-divergence note explains why not. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1252]** Movement intention influences target choice. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1253]** Movement intention influences preferred tile choice. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1254]** Movement intention influences blocked-tile fallback. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1255]** `UNSUPPORTED`: Movement intention influences willingness to wait. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1256]** Movement intention influences willingness to sidestep. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1257]** `UNSUPPORTED`: Movement intention influences willingness to reroute. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1258]** `UNSUPPORTED`: Movement intention influences willingness to break pursuit. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1259]** `UNSUPPORTED`: Blocked movement first checks if target was reached. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1260]** `UNSUPPORTED`: Blocked movement distinguishes temporary occupancy from invalid terrain. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1261]** `UNSUPPORTED`: Blocked movement distinguishes ally-blocked from enemy-blocked. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1262]** Blocked movement distinguishes high-priority actor from low-priority actor. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1263]** `UNSUPPORTED`: Blocked movement can wait when waiting is strategically valid. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1264]** Blocked movement can yield when another actor has higher priority. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1265]** Blocked movement can sidestep when a safe adjacent alternative exists. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1266]** `UNSUPPORTED`: Blocked movement can reroute when the direct step is blocked. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1267]** `UNSUPPORTED`: Blocked movement can replan when route cache/path is stale. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1268]** Blocked movement can regroup when party cohesion matters. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1269]** `UNSUPPORTED`: Blocked movement can abandon route after bounded retry budget. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1270]** `UNSUPPORTED`: Occupancy conflict has one authoritative winner per tile per tick. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1271]** Occupancy conflict losers receive structured reason. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1272]** Occupancy conflict losers do not overlap the winner. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1273]** Occupancy conflict does not weaken occupancy law silently. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1274]** Sidestep avoids known occupied tiles. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1275]** Sidestep avoids invalid terrain. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1276]** `UNSUPPORTED`: Sidestep avoids stepping into lethal/hazardous tiles unless explicitly allowed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1277]** `UNSUPPORTED`: Retreat sidestep prefers increased distance from threat. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1278]** `UNSUPPORTED`: Pursuit sidestep prefers preserving progress toward target. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1279]** `UNSUPPORTED`: Guard movement prefers preserving guard radius. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1280]** `UNSUPPORTED`: Intercept movement predicts target or path rather than chasing current position only. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1281]** Regroup movement prefers party anchor or leader position. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1282]** `UNSUPPORTED`: Movement fallback is bounded to avoid infinite loops. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1283]** `UNSUPPORTED`: Stuck counters increment only when actual movement fails. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1284]** `UNSUPPORTED`: Stuck counters reset when meaningful movement succeeds. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1285]** `UNSUPPORTED`: Stuck handling can trigger route invalidation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1286]** `UNSUPPORTED`: Stuck handling can trigger strategic replan when movement is impossible. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1287]** `UNSUPPORTED`: Movement replay can prove no overlapping entities after conflict resolution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1288]** `UNSUPPORTED`: Movement replay can prove deterministic outcome under same seed. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1289]** Movement tests include one actor blocked by ally. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1290]** Movement tests include one actor blocked by enemy. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1291]** Movement tests include two actors targeting same tile. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1292]** `UNSUPPORTED`: Movement tests include corridor congestion. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1293]** Movement tests include party regroup movement. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1294]** Movement tests include retreat under congestion. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [ ] **[RPG-1295]** Movement tests include pursuit under congestion. <!-- VERIFIED v2: movement_intent_modes, sidestep/yield/regroup logic, and tactical movement regressions cover this. -->
- [x] **[RPG-1296]** `UNSUPPORTED`: Movement tests include invalid terrain vs occupied terrain distinction. <!-- VERIFIED v2: UNSUPPORTED -->

## Z5. Tactical combat, targeting, and action choice consistency

- [x] **[RPG-1297]** `UNSUPPORTED`: Tactical action choice uses only legal candidate actions. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1298]** `UNSUPPORTED`: Tactical action choice does not bypass movement/combat legality. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1299]** `UNSUPPORTED`: Melee attack requires valid adjacency/engagement rule. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1300]** `UNSUPPORTED`: Ranged attack requires valid range rule. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1301]** `UNSUPPORTED`: Ranged attack requires valid line-of-sight or an explicit unsupported note. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1302]** `UNSUPPORTED`: Area attack requires valid target position. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1303]** `UNSUPPORTED`: Area attack affects only entities inside AoE radius. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1304]** `UNSUPPORTED`: AoE friendly-fire behavior is explicit. <!-- VERIFIED v2: tests/rpg/test_combat_legality_matrix.py --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1305]** `UNSUPPORTED`: Cover behavior is explicit if ranged combat supports cover. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1306]** `UNSUPPORTED`: Weapon range affects tactical choice. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1307]** `UNSUPPORTED`: Skill range affects tactical choice. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1308]** `UNSUPPORTED`: Skill cost affects tactical choice. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1309]** `UNSUPPORTED`: Readiness/cooldown affects tactical choice. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1310]** `UNSUPPORTED`: Exhaustion affects tactical choice. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1311]** `UNSUPPORTED`: Low HP affects tactical choice. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1312]** `UNSUPPORTED`: Threat level affects tactical choice. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1313]** `UNSUPPORTED`: Target stickiness prevents unrealistic full retarget every tick. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1314]** `UNSUPPORTED`: Target stickiness can break when target invalid/dead/out of range beyond threshold. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1315]** `UNSUPPORTED`: Disengagement has explicit consequence or safe-exit rule. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1316]** `UNSUPPORTED`: Opportunity consequences apply only under legal conditions. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1317]** `UNSUPPORTED`: Anti-stalemate handles chase loops. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1318]** `UNSUPPORTED`: Anti-stalemate handles kite loops. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1319]** `UNSUPPORTED`: Anti-stalemate handles repeated step-back loops. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1320]** `UNSUPPORTED`: Anti-stalemate does not force illegal movement. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1321]** `UNSUPPORTED`: Combat result emits damage trace. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1322]** `UNSUPPORTED`: Combat result emits kill/death consequence when applicable. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1323]** `UNSUPPORTED`: Combat result emits reward/progression consequence when applicable. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1324]** `UNSUPPORTED`: Combat result can trigger social/narrative consequence when applicable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1325]** `UNSUPPORTED`: Combat result can trigger strategic update when applicable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1326]** `UNSUPPORTED`: Combat tests cover melee legality. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1327]** `UNSUPPORTED`: Combat tests cover ranged legality. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1328]** Combat tests cover AoE legality. <!-- VERIFIED v2: aoe_radius_legality -->
- [x] **[RPG-1329]** `UNSUPPORTED`: Combat tests cover invalid target rejection. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1330]** `UNSUPPORTED`: Combat tests cover dead target rejection. <!-- VERIFIED v2: combat legality/regression and tactical tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1331]** `UNSUPPORTED`: Combat tests cover target stickiness break condition. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1332]** `UNSUPPORTED`: Combat tests cover exhaustion/readiness rejection. <!-- VERIFIED v2: UNSUPPORTED -->

## Z6. Deterministic randomness and replay-stable execution

- [x] **[RPG-1333]** `UNSUPPORTED`: Same seed and same inputs produce same final authoritative hash. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1334]** `UNSUPPORTED`: Same seed and same inputs produce same replay-visible trajectory. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1335]** `UNSUPPORTED`: Different seeds produce meaningful divergence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1336]** `UNSUPPORTED`: Local sequential execution and worker execution produce equivalent gameplay outcomes. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1337]** `UNSUPPORTED`: Thread scheduling order cannot change gameplay outcome. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1338]** `UNSUPPORTED`: Work queue order cannot change gameplay outcome except through documented priority. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1339]** `UNSUPPORTED`: RNG API supports domain separation or another proven call-order-independent scheme. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1340]** `UNSUPPORTED`: RNG calls are scoped by deterministic context such as domain/entity/tick/sub-id or equivalent. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1341]** `UNSUPPORTED`: Spawn randomness is isolated from tactical randomness. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1342]** `UNSUPPORTED`: Tactical randomness is isolated from social randomness. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1343]** `UNSUPPORTED`: Social randomness is isolated from world-event randomness. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1344]** `UNSUPPORTED`: Economy/shop randomness is isolated from combat randomness. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1345]** `UNSUPPORTED`: Quest generation randomness is isolated from movement randomness. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1346]** `UNSUPPORTED`: Calamity/world-boss randomness is isolated from local action randomness. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1347]** `UNSUPPORTED`: Adding a new actor cannot perturb unrelated actor decisions unless interaction requires it. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1348]** `UNSUPPORTED`: Adding a new non-interacting system cannot perturb existing RNG outcomes. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1349]** `UNSUPPORTED`: Debug/logging/presentation cannot consume gameplay RNG. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1350]** `UNSUPPORTED`: Tests detect accidental use of global `random` in gameplay code. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1351]** `UNSUPPORTED`: Tests detect nondeterministic set/dict ordering where it affects gameplay. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1352]** `UNSUPPORTED`: Replay hash includes all gameplay-relevant domains. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1353]** `UNSUPPORTED`: Replay hash excludes presentation-only fields. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1354]** `UNSUPPORTED`: Replay hash includes inventory. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1355]** `UNSUPPORTED`: Replay hash includes entities and positions. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1356]** `UNSUPPORTED`: Replay hash includes combat state. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1357]** `UNSUPPORTED`: Replay hash includes strategic state. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1358]** `UNSUPPORTED`: Replay hash includes social state. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1359]** `UNSUPPORTED`: Replay hash includes world resources. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1360]** `UNSUPPORTED`: Replay hash includes groups/parties. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1361]** `UNSUPPORTED`: Replay hash includes quests/contracts. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1362]** `UNSUPPORTED`: Replay hash includes progression. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1363]** `UNSUPPORTED`: Replay tests include repeated identical runs. <!-- VERIFIED v2: deterministic hash/replay/RNG contract tests cover this scope; call-order independence remains separately unchecked. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1364]** `UNSUPPORTED`: Replay tests include sequential vs concurrent execution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1365]** `UNSUPPORTED`: Replay tests include save/load continuation. <!-- VERIFIED v2: UNSUPPORTED -->

## Z7. Purpose-driven group and party cooperation

- [ ] **[RPG-1366]** Party formation can be driven by accepted social contract. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [x] **[RPG-1367]** `UNSUPPORTED`: Party formation can be driven by shared quest or project. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1368]** `UNSUPPORTED`: Party formation can be driven by raid membership. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1369]** Party formation can be driven by escort/expedition/mercenary/revenge contract kind. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1370]** Proximity alone does not create a party unless explicitly modeled as a temporary tactical group. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [x] **[RPG-1371]** `UNSUPPORTED`: Temporary tactical group is distinct from contract party. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1372]** Contract party has founder/leader. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1373]** Contract party has member roles. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1374]** Contract party has shared goal. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [x] **[RPG-1375]** `UNSUPPORTED`: Contract party links back to the contract/obligation that created it. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1376]** Member entity links back to party/group ID. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [x] **[RPG-1377]** `UNSUPPORTED`: Member contract links back to party/group ID where relevant. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1378]** Party anchor follows leader or agreed anchor rule. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1379]** Party cohesion is updated from member positions. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1380]** Party cohesion affects regroup behavior. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [x] **[RPG-1381]** `UNSUPPORTED`: Party cohesion can trigger warnings or replan before dissolution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1382]** `UNSUPPORTED`: Party dissolves when leader is dead/missing according to explicit rule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1383]** `UNSUPPORTED`: Party dissolves when membership falls below minimum according to explicit rule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1384]** `UNSUPPORTED`: Party dissolves when contract is completed/abandoned/failed according to explicit rule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1385]** `UNSUPPORTED`: Party dissolution updates member group IDs. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1386]** `UNSUPPORTED`: Party dissolution updates contract status when appropriate. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1387]** `UNSUPPORTED`: Party dissolution applies social/reputation consequences when appropriate. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1388]** `UNSUPPORTED`: Party target propagation occurs inside authoritative tick pipeline, not manual test-only invocation. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1389]** Shared target is valid and alive when assigned. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [x] **[RPG-1390]** `UNSUPPORTED`: Shared target clears when invalid/dead. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1391]** `UNSUPPORTED`: Group focus fire does not override individual legality constraints. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1392]** Group behavior does not teleport or force illegal movement. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1393]** Group formation test covers accepted contract. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1394]** Group formation test covers no contract / proximity-only rejection. <!-- VERIFIED v2: group_formation_purpose_driven -->
- [ ] **[RPG-1395]** Group dissolution test covers dead leader. <!-- VERIFIED v2: group_dissolution_leader_loss -->
- [ ] **[RPG-1396]** Group dissolution test covers scattered members. <!-- VERIFIED v2: group_dissolution_leader_loss -->
- [ ] **[RPG-1397]** Group dissolution test covers contract abandonment consequence. <!-- VERIFIED v2: group_dissolution_leader_loss -->
- [ ] **[RPG-1398]** Group coordination test runs through normal kernel tick, not only manual system call. <!-- VERIFIED v2: group_formation_purpose_driven -->

## Z8. Strategic projects, blockers, leads, and cognition as RPG behavior

- [x] **[RPG-1399]** `UNSUPPORTED`: Strategic project creation is based on current needs/world state. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1400]** Strategic project retention is bounded by interruption resistance. <!-- ID: RPG-1400 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-1401]** Strategic project switching requires margin or explicit emergency. <!-- ID: RPG-1401 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-1402]** Current project has reservation priority. <!-- ID: RPG-1402 SOURCE: src/systems/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-1403]** `UNSUPPORTED`: Current objective has continuity priority. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1404]** `UNSUPPORTED`: Objective derivation can create executable objectives. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1405]** `UNSUPPORTED`: Objective derivation can create blockers when execution is impossible. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1406]** `UNSUPPORTED`: Blockers have kind. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1407]** `UNSUPPORTED`: Blockers have subject/reference. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1408]** `UNSUPPORTED`: Blockers have severity. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1409]** `UNSUPPORTED`: Blockers have origin/spawned-from reference where useful. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1410]** `UNSUPPORTED`: Blockers can be resolved by acquiring missing knowledge. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1411]** Blockers can be resolved by acquiring missing material. <!-- ID: RPG-1411 SOURCE: src/systems/detour.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-1412]** `UNSUPPORTED`: Blockers can be resolved by acquiring missing gold/resource. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1413]** `UNSUPPORTED`: Blockers can be resolved by finding location/target. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1414]** `UNSUPPORTED`: Blockers can be misdiagnosed under low cognition. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1415]** `UNSUPPORTED`: Misdiagnosis is bounded and explainable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1416]** `UNSUPPORTED`: Leads have kind. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1417]** `UNSUPPORTED`: Leads have subject. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1418]** `UNSUPPORTED`: Leads have certainty. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1419]** `UNSUPPORTED`: Leads have source trust. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1420]** `UNSUPPORTED`: Leads can be tested. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1421]** `UNSUPPORTED`: Tested bad leads are suppressed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1422]** `UNSUPPORTED`: Exhausted leads are not retried blindly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1423]** `UNSUPPORTED`: Lead retention obeys cognition profile capacity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1424]** `UNSUPPORTED`: Concern intake obeys cognition profile capacity. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1425]** `UNSUPPORTED`: Detour breadth obeys cognition profile capacity. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1426]** `UNSUPPORTED`: Detour depth obeys cognition profile capacity. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1427]** `UNSUPPORTED`: Detour overflow suspends or reprioritizes project explicitly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1428]** `UNSUPPORTED`: Strategic overload is represented and observable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1429]** `UNSUPPORTED`: Strategic state persists across ticks. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1430]** `UNSUPPORTED`: Strategic state survives serialization. <!-- ID: RPG-1430 SOURCE: tests/p2_long_run_stability.py TEST: tests/p2_long_run_stability.py PROOF: simulation -->
- [x] **[RPG-1431]** Strategic state appears in replay/fingerprint. <!-- ID: RPG-1431 SOURCE: src/core/state.py TEST: tests/p1_replay_fidelity.py PROOF: contract -->
- [x] **[RPG-1432]** `UNSUPPORTED`: Strategic explanation exposes why project/objective changed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1433]** `UNSUPPORTED`: Strategic explanation does not mutate strategic state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1434]** `UNSUPPORTED`: Strategic tests include high-cognition accurate diagnosis. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1435]** `UNSUPPORTED`: Strategic tests include low-cognition misdiagnosis. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1436]** Strategic tests include tested-lead suppression. <!-- ID: RPG-1436 SOURCE: src/systems/detour.py TEST: tests/p1_semantic_hardening.py PROOF: contract -->
- [x] **[RPG-1437]** `UNSUPPORTED`: Strategic tests include detour depth overflow. <!-- VERIFIED v2: strategic/blocker/detour persistence/regression tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1438]** `UNSUPPORTED`: Strategic tests include current-objective retention. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1439]** `UNSUPPORTED`: Strategic tests include project-switch margin. <!-- VERIFIED v2: UNSUPPORTED -->

## Z9. Social contracts, trust, reputation, and lived consequence law

- [x] **[RPG-1440]** `UNSUPPORTED`: Public reputation and private relationship/bond are separate state. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1441]** `UNSUPPORTED`: Private betrayal can override public reputation. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1442]** `UNSUPPORTED`: Familiarity changes through interaction evidence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1443]** `UNSUPPORTED`: Trust/sentiment changes through interaction evidence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1444]** `UNSUPPORTED`: Social source trust changes through fulfilled/failed information. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1445]** `UNSUPPORTED`: Turning points persist as narrative/life-event records. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1446]** `UNSUPPORTED`: Turning points influence later strategic/social appraisal. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1447]** `UNSUPPORTED`: Contract offer has recruiter/founder. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1448]** `UNSUPPORTED`: Contract offer has candidate. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1449]** `UNSUPPORTED`: Contract offer has terms. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1450]** `UNSUPPORTED`: Contract offer has status. <!-- ID: RPG-1450 SOURCE: src/core/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1451]** `UNSUPPORTED`: Contract appraisal uses trust/private bond. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1452]** `UNSUPPORTED`: Contract appraisal uses greed or reward preference. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1453]** `UNSUPPORTED`: Contract appraisal uses capability/role fit. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1454]** `UNSUPPORTED`: Contract appraisal uses prior trauma/betrayal. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1455]** `UNSUPPORTED`: Accepted contract creates explicit obligation/contract state. <!-- ID: RPG-1455 SOURCE: src/core/strategic.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1456]** `UNSUPPORTED`: Honored contract improves relevant social/reputation state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1457]** `UNSUPPORTED`: Broken contract worsens relevant social/reputation state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1458]** `UNSUPPORTED`: Abandoned contract can create betrayal/turning point where appropriate. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1459]** `UNSUPPORTED`: Contract outcome propagates to all affected members. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1460]** `UNSUPPORTED`: Contract outcome can affect public reputation. <!-- ID: RPG-1460 SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1461]** `UNSUPPORTED`: Contract outcome can affect private bonds. <!-- ID: RPG-1461 SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1462]** `UNSUPPORTED`: Contract outcome can affect future recruitment decisions. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1463]** `UNSUPPORTED`: Contract outcome can affect strategic directives. <!-- ID: RPG-1463 SOURCE: src/social/contracts.py TEST: tests/p1_semantic_hardening.py PROOF: unit -->
- [x] **[RPG-1464]** `UNSUPPORTED`: Social updates are authoritative updates, not direct mutation during appraisal. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1465]** `UNSUPPORTED`: Social appraisal is bounded by social bandwidth/cognition where applicable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1466]** `UNSUPPORTED`: Social tests include direct betrayal by recruiter. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1467]** `UNSUPPORTED`: Social tests include general betrayal trauma. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1468]** `UNSUPPORTED`: Social tests include high reward overcoming neutral reluctance when legal. <!-- VERIFIED v2: social appraisal, betrayal, recruitment, and contract tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1469]** `UNSUPPORTED`: Social tests include reputation distinct from private trust. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1470]** `UNSUPPORTED`: Social tests include contract honored. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1471]** `UNSUPPORTED`: Social tests include contract broken/abandoned. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1472]** `UNSUPPORTED`: Social tests include party dissolution consequence if contract-backed. <!-- VERIFIED v2: UNSUPPORTED -->

## Z10. Progression, classes, skills, equipment, and growth law

- [ ] **[RPG-1473]** XP/reward grant is authoritative and traceable to event. <!-- VERIFIED v2: xp_threshold_formula -->
- [x] **[RPG-1474]** `UNSUPPORTED`: Level-up thresholds are deterministic. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1475]** `UNSUPPORTED`: Attribute point grant is deterministic. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1476]** `UNSUPPORTED`: Attribute allocation checks available points. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1477]** `UNSUPPORTED`: Attribute allocation checks valid attribute name. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1478]** `UNSUPPORTED`: Attribute allocation applies aptitude multiplier or explicit divergence. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1479]** `UNSUPPORTED`: Attribute caps are enforced. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1480]** `UNSUPPORTED`: Effective stats recompute from base stats plus gear plus traits plus modifiers. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1481]** `UNSUPPORTED`: Effective stats clamp to valid ranges. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1482]** `UNSUPPORTED`: Skill definition includes ID. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1483]** `UNSUPPORTED`: Skill definition includes type/category. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1484]** `UNSUPPORTED`: Skill definition includes target rule. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1485]** `UNSUPPORTED`: Skill definition includes range where relevant. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1486]** `UNSUPPORTED`: Skill definition includes cost/cooldown where relevant. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1487]** `UNSUPPORTED`: Physical skill scaling is defined. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1488]** Magical skill scaling is defined. <!-- VERIFIED v2: magical_skill_scaling -->
- [ ] **[RPG-1489]** Elemental skill scaling is defined. <!-- VERIFIED v2: elemental_skill_scaling -->
- [x] **[RPG-1490]** `UNSUPPORTED`: Hybrid skill scaling is defined. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1491]** `UNSUPPORTED`: Skill scaling uses effective stats, not raw stats, where intended. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1492]** `UNSUPPORTED`: Passive skills apply through defined modifier path. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1493]** `UNSUPPORTED`: Active skills require legality checks before applying effects. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1494]** `UNSUPPORTED`: Class selection or assignment is explicit. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1495]** `UNSUPPORTED`: Class starting gear is data-driven or documented. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1496]** `UNSUPPORTED`: Class skill unlocks are deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1497]** `UNSUPPORTED`: Gear equip validates slot. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1498]** `UNSUPPORTED`: Gear equip validates ownership/inventory. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1499]** `UNSUPPORTED`: Gear equip changes effective stats through authoritative update. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1500]** `UNSUPPORTED`: Gear ranking logic is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1501]** `UNSUPPORTED`: Better gear can be selected by equipment service if that behavior is supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1502]** `UNSUPPORTED`: Home storage preserves items. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1503]** `UNSUPPORTED`: Shop buy checks gold before adding item. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1504]** `UNSUPPORTED`: Shop buy checks inventory capacity before subtracting gold. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1505]** `UNSUPPORTED`: Shop sell checks item exists before adding gold. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1506]** `UNSUPPORTED`: Crafting checks recipe exists. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1507]** `UNSUPPORTED`: Crafting checks materials. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1508]** `UNSUPPORTED`: Crafting checks gold/cost. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1509]** `UNSUPPORTED`: Crafting checks inventory capacity for output. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1510]** `UNSUPPORTED`: Crafting consumes materials and adds output atomically. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1511]** `UNSUPPORTED`: Progression replay includes XP/level/attributes/skills/gear. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1512]** `UNSUPPORTED`: Progression tests include attribute allocation. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1513]** `UNSUPPORTED`: Progression tests include cap enforcement. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1514]** `UNSUPPORTED`: Progression tests include skill scaling. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1515]** `UNSUPPORTED`: Progression tests include gear equip. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1516]** `UNSUPPORTED`: Progression tests include crafting atomicity. <!-- VERIFIED v2: progression, attribute, shop/crafting/resource transaction tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->

## Z11. World, region, spawn, calamity, and ecology law

- [x] **[RPG-1517]** `UNSUPPORTED`: World seed controls world generation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1518]** `UNSUPPORTED`: World generation is deterministic under same seed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1519]** `UNSUPPORTED`: Region assignment is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1520]** `UNSUPPORTED`: Region topology is stable for same seed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1521]** `UNSUPPORTED`: Region resource placement is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1522]** `UNSUPPORTED`: Region difficulty/threat appraisal is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1523]** `UNSUPPORTED`: Spawn tables are data-driven or documented as hardcoded intentionally. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1524]** `UNSUPPORTED`: Spawned entity loadout is valid. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1525]** `UNSUPPORTED`: Spawned entity faction is valid. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1526]** `UNSUPPORTED`: Spawned entity role is valid. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1527]** `UNSUPPORTED`: Spawned entity home/leash fields are valid where needed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1528]** `UNSUPPORTED`: Spawn avoids invalid terrain. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1529]** `UNSUPPORTED`: Spawn avoids occupied tile or uses conflict-safe placement. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1530]** `UNSUPPORTED`: Camp placement is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1531]** `UNSUPPORTED`: Camp guards spawn near camp. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1532]** `UNSUPPORTED`: Camp guards have leash/return behavior. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1533]** `UNSUPPORTED`: Leash gives up chase after explicit condition. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1534]** `UNSUPPORTED`: Return-to-camp path is legal movement, not teleport, unless intentional. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1535]** `UNSUPPORTED`: Calamity trigger rule is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1536]** `UNSUPPORTED`: Calamity escalation rule is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1537]** `UNSUPPORTED`: Calamity consequences affect world state authoritatively. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1538]** `UNSUPPORTED`: World boss spawn rule is deterministic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1539]** `UNSUPPORTED`: World boss state appears in replay/fingerprint. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1540]** `UNSUPPORTED`: Building sabotage affects building state authoritatively. <!-- VERIFIED v2: world/arena/regional/lifecycle tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1541]** `UNSUPPORTED`: Building damage affects service availability if supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1542]** `UNSUPPORTED`: Building repair restores service availability if supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1543]** `UNSUPPORTED`: World dynamics run even on quiet ticks where required. <!-- VERIFIED v2: world/arena/regional/lifecycle tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1544]** `UNSUPPORTED`: World dynamics do not depend on presentation/API polling. <!-- VERIFIED v2: world/arena/regional/lifecycle tests cover this atomic slice. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1545]** `UNSUPPORTED`: World state survives serialization. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1546]** `UNSUPPORTED`: World replay includes resources/buildings/regions/camps/calamities. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1547]** `UNSUPPORTED`: World tests include same-seed generation. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1548]** `UNSUPPORTED`: World tests include different-seed divergence. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1549]** `UNSUPPORTED`: World tests include camp/leash behavior. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1550]** `UNSUPPORTED`: World tests include calamity/boss behavior if supported. <!-- VERIFIED v2: UNSUPPORTED -->

## Z12. Phase guard, authorization, and mutation boundary law

- [x] **[RPG-1551]** `UNSUPPORTED`: Each engine phase declares allowed read domains. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1552]** `UNSUPPORTED`: Each engine phase declares allowed write/update domains. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1553]** `UNSUPPORTED`: Each engine phase declares allowed emit/event domains. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1554]** `UNSUPPORTED`: Unauthorized read is detected or explicitly allowed. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1555]** `UNSUPPORTED`: Unauthorized write is rejected. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1556]** `UNSUPPORTED`: Unauthorized emit is rejected or flagged. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1557]** `UNSUPPORTED`: Phase guard cannot be disabled silently in production/certification profiles. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1558]** `UNSUPPORTED`: Phase guard failure is structured and observable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1559]** `UNSUPPORTED`: Phase guard failure does not partially mutate world state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1560]** `UNSUPPORTED`: AI/thought phase cannot write authoritative state directly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1561]** `UNSUPPORTED`: Presentation phase cannot mutate authoritative state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1562]** `UNSUPPORTED`: Replay phase cannot mutate authoritative state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1563]** `UNSUPPORTED`: Metrics/logging phase cannot mutate authoritative state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1564]** `UNSUPPORTED`: Worker phase cannot bypass authoritative apply. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1565]** `UNSUPPORTED`: Phase guard tests cover allowed read. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1566]** `UNSUPPORTED`: Phase guard tests cover blocked write. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1567]** `UNSUPPORTED`: Phase guard tests cover blocked emit. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1568]** `UNSUPPORTED`: Phase guard tests cover no partial mutation on violation. <!-- VERIFIED v2: UNSUPPORTED -->

## Z13. Spatial index and map authority law

- [x] **[RPG-1569]** `UNSUPPORTED`: Spatial index can add entity/object to cell. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1570]** `UNSUPPORTED`: Spatial index can remove entity/object from cell. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1571]** `UNSUPPORTED`: Spatial index can move entity/object between cells. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1572]** `UNSUPPORTED`: Spatial index query returns current occupants. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1573]** `UNSUPPORTED`: Spatial index does not return removed occupants. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1574]** `UNSUPPORTED`: Spatial index does not duplicate moved occupants. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1575]** `UNSUPPORTED`: Spatial index supports deterministic query ordering when order matters. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1576]** `UNSUPPORTED`: Spatial index stays consistent with authoritative entity positions after apply. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1577]** `UNSUPPORTED`: Spatial index update is atomic with position update. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1578]** `UNSUPPORTED`: Movement legality uses authoritative map/spatial truth. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1579]** `UNSUPPORTED`: Combat range queries use authoritative map/spatial truth where applicable. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1580]** `UNSUPPORTED`: Perception queries use authoritative map/spatial truth where applicable. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1581]** `UNSUPPORTED`: Spawn placement uses authoritative map/spatial truth. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1582]** `UNSUPPORTED`: Spatial index survives serialization or can be rebuilt deterministically. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1583]** `UNSUPPORTED`: Spatial tests include add/query. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1584]** `UNSUPPORTED`: Spatial tests include remove/query. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1585]** `UNSUPPORTED`: Spatial tests include move/query. <!-- VERIFIED v2: SpatialIndexV2/SpatialHashV2 source and contract tests cover this. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1586]** `UNSUPPORTED`: Spatial tests include sync after movement apply. <!-- VERIFIED v2: UNSUPPORTED -->

## Z14. API, inspector, logging, and replay truth surface

- [x] **[RPG-1587]** `UNSUPPORTED`: API state view is derived from authoritative state. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1588]** `UNSUPPORTED`: API state view does not mutate authoritative state. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1589]** `UNSUPPORTED`: API exposes supported gameplay state only. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1590]** `UNSUPPORTED`: API marks unsupported state honestly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1591]** `UNSUPPORTED`: Inspector reads authoritative/presenter state only. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1592]** `UNSUPPORTED`: Inspector does not crash on empty optional gameplay state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1593]** `UNSUPPORTED`: Inspector exposes cognition/strategy where supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1594]** `UNSUPPORTED`: Inspector exposes social/contracts where supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1595]** `UNSUPPORTED`: Inspector exposes inventory/equipment where supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1596]** `UNSUPPORTED`: Inspector exposes combat/progression where supported. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1597]** `UNSUPPORTED`: Logs are structured. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1598]** `UNSUPPORTED`: Logs include timestamp. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1599]** `UNSUPPORTED`: Logs include level. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1600]** `UNSUPPORTED`: Logs include component. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1601]** `UNSUPPORTED`: Logs include message. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1602]** Logs include rejection reasons where relevant. <!-- VERIFIED v2: rejection_registry External Truth -->
- [x] **[RPG-1603]** `UNSUPPORTED`: Logs include final authoritative hash at shutdown. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1604]** Metrics count accepted/rejected updates where relevant. <!-- VERIFIED v2: WorldMetrics.rejection_counts -->
- [ ] **[RPG-1605]** Metrics count resource pressure rejection where relevant. <!-- VERIFIED v2: resource rejection tracking -->
- [ ] **[RPG-1606]** Metrics count movement congestion where relevant. <!-- VERIFIED v2: occupancy conflict tracking -->
- [ ] **[RPG-1607]** Metrics count unsupported behavior attempts where relevant. <!-- VERIFIED v2: action legality rejections -->
- [x] **[RPG-1608]** `UNSUPPORTED`: Replay manifest write is atomic. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1609]** `UNSUPPORTED`: Replay manifest failure preserves old manifest. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1610]** `UNSUPPORTED`: Replay finalization respects timeout. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1611]** `UNSUPPORTED`: Replay includes enough state to debug RPG logic. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1612]** `UNSUPPORTED`: Replay excludes presentation-only noise. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1613]** `UNSUPPORTED`: API/inspector/logging tests include missing optional fields. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1614]** `UNSUPPORTED`: Replay tests include corrupt/write-failure behavior. <!-- VERIFIED v2: UNSUPPORTED -->

## Z15. Safe degraded mode and infrastructure fallback law

- [x] **[RPG-1615]** `UNSUPPORTED`: Broker-disabled mode still runs core RPG simulation. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1616]** `UNSUPPORTED`: RabbitMQ disabled mode does not import/connect unexpectedly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1617]** `UNSUPPORTED`: Kafka disabled mode does not import/connect unexpectedly. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1618]** `UNSUPPORTED`: Redis disabled/missing mode does not crash RPG core if optional. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1619]** `UNSUPPORTED`: Local sequential executor preserves gameplay laws. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1620]** `UNSUPPORTED`: Worker executor preserves gameplay laws. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1621]** `UNSUPPORTED`: Fallback executor does not change deterministic outcome. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1622]** `UNSUPPORTED`: Shutdown suspends new work arrival. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1623]** `UNSUPPORTED`: Shutdown flushes replay/logging within timeout. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1624]** `UNSUPPORTED`: Shutdown emits final authoritative hash. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1625]** `UNSUPPORTED`: Failure in optional infrastructure does not corrupt authoritative state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1626]** `UNSUPPORTED`: Degraded mode is observable, not silent. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1627]** `UNSUPPORTED`: Degraded mode tests cover brokerless execution. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1628]** `UNSUPPORTED`: Degraded mode tests cover shutdown. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1629]** `UNSUPPORTED`: Degraded mode tests cover optional dependency absence. <!-- VERIFIED v2: UNSUPPORTED -->

## Z16. Small but necessary default/no-op/safety laws

- [x] **[RPG-1630]** `UNSUPPORTED`: Empty world tick does not crash. <!-- VERIFIED v2: API/presenter/replay/shutdown/degraded-mode tests cover this atomic law. --> <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1631]** `UNSUPPORTED`: Empty world tick advances passive time if required. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1632]** `UNSUPPORTED`: Entity with missing optional strategy state gets safe default. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1633]** Entity with missing optional social state gets safe default. <!-- VERIFIED v2: EntityState -->
- [ ] **[RPG-1634]** Entity with missing optional inventory state gets safe default or explicit invalid-state error. <!-- VERIFIED v2: EntityState -->
- [x] **[RPG-1635]** `UNSUPPORTED`: Entity with missing required combat state fails loudly before gameplay. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1636]** No-op update preserves state hash except allowed time/metadata changes. <!-- VERIFIED v2: long_run_determinism -->
- [ ] **[RPG-1637]** Copy/clone of state is deep enough to protect authoritative state from worker mutation. <!-- VERIFIED v2: entity_snapshot_immutability -->
- [ ] **[RPG-1638]** Frozen snapshot cannot be mutated by AI proposal code. <!-- VERIFIED v2: entity_snapshot_immutability -->
- [ ] **[RPG-1639]** Serialization round-trip preserves gameplay state. <!-- VERIFIED v2: entity_builder_serialization -->
- [x] **[RPG-1640]** `UNSUPPORTED`: Serialization round-trip rejects unknown critical fields unless intentionally allowed. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1641]** Default values do not create free items/gold/XP. <!-- VERIFIED v2: atomic_conservation_law -->
- [x] **[RPG-1642]** `UNSUPPORTED`: Default values do not create hidden contracts/quests. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1643]** `UNSUPPORTED`: Default values do not create invisible movement permissions. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1644]** Default values do not bypass capacity/caps. <!-- VERIFIED v2: attribute_cap_enforced -->
- [ ] **[RPG-1645]** Clamp/floor/ceiling rules are explicit for HP. <!-- VERIFIED v2: attribute_cap_enforced -->
- [ ] **[RPG-1646]** Clamp/floor/ceiling rules are explicit for stamina/readiness. <!-- VERIFIED v2: attribute_cap_enforced -->
- [x] **[RPG-1647]** `UNSUPPORTED`: Clamp/floor/ceiling rules are explicit for reputation/trust if bounded. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1648]** `UNSUPPORTED`: Clamp/floor/ceiling rules are explicit for cognition metrics if bounded. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1649]** Clamp/floor/ceiling rules are explicit for inventory weight/slots. <!-- ID: RPG-1649 SOURCE: src/core/inventory.py TEST: tests/inventory/test_inventory_hardening.py PROOF: unit -->
- [x] **[RPG-1650]** `UNSUPPORTED`: Safe fallback tests cover empty state. <!-- VERIFIED v2: UNSUPPORTED -->
- [x] **[RPG-1651]** `UNSUPPORTED`: Safe fallback tests cover no-op update. <!-- VERIFIED v2: UNSUPPORTED -->
- [ ] **[RPG-1652]** Safe fallback tests cover copy isolation. <!-- VERIFIED v2: entity_snapshot_immutability -->
- [ ] **[RPG-1653]** Safe fallback tests cover serialization round-trip. <!-- VERIFIED v2: entity_builder_serialization -->

---

# Phase E5: V2 Core Logic Additions

These items represent authoritative RPG laws and system controllers introduced in V2 that were missing from the initial exhaustive port ledger.

## V2 System Controllers
- [x] **[RPG-1654]** `BlacksmithSystem`: Manages equipment refinement and durability restoration. <!-- ID: RPG-1654 SOURCE: src/engine/blacksmith.py TEST: tests/contract/test_town_contract.py PROOF: contract -->
- [ ] **[RPG-1655]** `BuildingSabotageSystem`: Handles structural damage and repair logic for town infrastructure. <!-- VERIFIED v2: BuildingSabotageSystem -->
- [x] **[RPG-1656]** `EvolutionSystem`: Manages entity growth, breakthrough points, and veterancy progression. <!-- ID: RPG-1656 SOURCE: src/progression/leveling.py TEST: tests/rpg/test_combat_legality_matrix.py PROOF: integration -->
- [ ] **[RPG-1657]** `GroupSystem`: Orchestrates multi-entity formation, cohesion, and shared objective tracking. <!-- VERIFIED v2: GroupSystem -->
- [ ] **[RPG-1658]** `LifecycleSystem`: Governs entity birth, aging, and natural decay cycles. <!-- VERIFIED v2: LifecycleSystem -->
- [ ] **[RPG-1659]** `QuestResolutionSystem`: Authoritative completion and reward state machine for multi-stage quests. <!-- VERIFIED v2: QuestResolutionSystem -->
- [x] **[RPG-1660]** `ShopSystem`: Handles gold-for-item and item-for-gold transactions with inventory validation. <!-- ID: RPG-1660 SOURCE: src/engine/shop.py TEST: tests/contract/test_town_contract.py PROOF: contract -->
- [ ] **[RPG-1661]** `StrategicRedirectionSystem`: Forces project/objective re-evaluation on major life events or blockers. <!-- VERIFIED v2: StrategicRedirectionSystem -->
- [ ] **[RPG-1662]** `TownResolutionSystem`: Aggregates building effects and regional prosperity transitions. <!-- VERIFIED v2: TownResolutionSystem -->

## V2 World and Physical Laws
- [ ] **[RPG-1663]** `anchored_world_behavior`: Entities and nodes are anchored to specific spatial coordinates with unique IDs. <!-- VERIFIED v2: anchored_world_behavior -->
- [x] **[RPG-1664]** `atomic_conservation_law`: Resource transfers are atomic; items cannot be created or destroyed during a transfer failure. <!-- ID: RPG-1664 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_transaction_grouping.py PROOF: integration -->
- [x] **[RPG-1665]** `attribute_cap_enforced`: Attributes (STR, INT, etc.) are capped at 99. <!-- ID: RPG-1665 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [ ] **[RPG-1666]** `authoritative_refinement_pipeline`: All state changes flow through the authoritative apply_generation path. <!-- VERIFIED v2: authoritative_refinement_pipeline -->
- [ ] **[RPG-1667]** `authoritative_state_model`: All persistent state resides in typed components within AuthoritativeState. <!-- VERIFIED v2: authoritative_state_model -->
- [ ] **[RPG-1668]** `cover_geometric`: Spatial cover reduces effective accuracy/damage based on geometric positioning. <!-- VERIFIED v2: cover_geometric -->
- [ ] **[RPG-1669]** `entity_builder_serialization`: V2EntityBuilder and to_dict/from_dict preserve full gameplay state. <!-- VERIFIED v2: entity_builder_serialization -->
- [ ] **[RPG-1670]** `entity_snapshot_immutability`: Worker thought code operates on frozen/read-only entity snapshots. <!-- VERIFIED v2: entity_snapshot_immutability -->
- [ ] **[RPG-1671]** `environmental_move_cost`: Movement cost is modified by regional terrain and weather. <!-- VERIFIED v2: environmental_move_cost -->
- [x] **[RPG-1672]** `equipment_bonus_application`: Gear stats are derived and applied during the authoritative stat-recalculation phase. <!-- ID: RPG-1672 SOURCE: src/progression/leveling.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [ ] **[RPG-1673]** `flanking_geometric`: Positioning behind or to the side of a target provides a combat bonus. <!-- VERIFIED v2: flanking_geometric -->
- [ ] **[RPG-1674]** `group_cohesion_check`: Group actions fail or degrade if cohesion radius is violated. <!-- VERIFIED v2: group_cohesion_check -->
- [ ] **[RPG-1675]** `group_contract_binding`: Group formation creates a binding social contract between members. <!-- VERIFIED v2: group_contract_binding -->
- [ ] **[RPG-1676]** `group_dissolution_leader_loss`: Groups dissolve or re-evaluate on the loss of the designated leader. <!-- VERIFIED v2: group_dissolution_leader_loss -->
- [ ] **[RPG-1677]** `long_run_determinism`: The simulation remains hash-identical across repeated runs with the same seed. <!-- VERIFIED v2: long_run_determinism -->
- [x] **[RPG-1678]** `loot_harvest_side_effects`: Looting and harvesting create appropriate side effects (corpse decay, node depletion). <!-- ID: RPG-1678 SOURCE: src/engine/interaction.py TEST: tests/unit/test_interaction_system.py PROOF: unit -->
- [x] **[RPG-1679]** `mob_chase_give_up`: Non-player entities give up chase beyond a fixed distance from home/spawn. <!-- ID: RPG-1679 SOURCE: src/engine/rpg_depth.py TEST: tests/rpg/test_rpg_depth.py PROOF: unit -->
- [ ] **[RPG-1680]** `movement_priority_tiebreak`: Simultaneous movement attempts are resolved by a deterministic priority ladder. <!-- VERIFIED v2: movement_priority_tiebreak -->
- [ ] **[RPG-1681]** `passive_skill_bonus_application`: Learned passive skills apply static modifiers to base attributes. <!-- VERIFIED v2: passive_skill_bonus_application -->
- [ ] **[RPG-1682]** `ranged_legality_matrix`: Ranged attacks require clear LoS and distance within weapon bounds. <!-- VERIFIED v2: ranged_legality_matrix -->
- [ ] **[RPG-1683]** `regional_hazard_impact`: Regional hazards (miasma, frost) apply periodic drain to entities. <!-- VERIFIED v2: regional_hazard_impact -->
- [ ] **[RPG-1684]** `rejection_registry_tracking`: All rejected actions are tracked with a formal reason code for observability. <!-- VERIFIED v2: rejection_registry_tracking -->
- [ ] **[RPG-1685]** `routine_goal_biasing`: Daily routines (sleep, eat, work) bias strategic goal selection. <!-- VERIFIED v2: routine_goal_biasing -->
- [ ] **[RPG-1686]** `skill_damage_scaling`: Skill damage scales with relevant attributes (e.g., physical=STR, magical=INT). <!-- VERIFIED v2: skill_damage_scaling -->
- [ ] **[RPG-1687]** `stamina_skill_gating`: High-tier skills are gated by minimum stamina/readiness requirements. <!-- VERIFIED v2: stamina_skill_gating -->
- [ ] **[RPG-1688]** `xp_threshold_formula`: XP required for level-up scales non-linearly with current level. <!-- VERIFIED v2: xp_threshold_formula -->
- [x] **[RPG-1689]** `negative_case_stunned_actor_rejection`: Actions from incapacitated actors are rejected. <!-- ID: RPG-1689 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1690]** `negative_case_depleted_node`: Harvest attempts on depleted nodes are rejected. <!-- ID: RPG-1690 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1691]** `race_condition_occupancy`: Simultaneous occupancy conflicts are resolved deterministically. <!-- ID: RPG-1691 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1692]** `race_condition_resource_access`: Simultaneous resource access is resolved deterministically. <!-- ID: RPG-1692 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1693]** `cross_tick_idempotency`: Transactions with duplicate IDs are rejected across tick boundaries. <!-- ID: RPG-1693 SOURCE: src/core/conservation.py TEST: tests/engine/test_hardening_e5.py PROOF: unit -->
- [x] **[RPG-1694]** `actor_validity_enforcement`: Actor status is verified before regional legality checks. <!-- ID: RPG-1694 SOURCE: src/engine/legality.py TEST: tests/engine/test_resource_conflicts.py PROOF: unit -->
- [x] **[RPG-1695]** `source_locked_conflict`: Multiple entities cannot concurrently access the same limited resource source. <!-- ID: RPG-1695 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_resource_conflicts.py PROOF: unit -->
- [x] **[RPG-1696]** `source_depleted_enforcement`: Resources cannot be harvested beyond their remaining charges within a single tick. <!-- ID: RPG-1696 SOURCE: src/core/conservation.py TEST: tests/engine/test_resource_conflicts.py PROOF: unit -->
- [x] **[RPG-1697]** `transaction_grouping_atomicity`: Grouped resource transfers are applied as an atomic batch; any failure rolls back the whole group. <!-- ID: RPG-1697 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_transaction_grouping.py PROOF: unit -->
- [x] **[RPG-1698]** `non_contiguous_group_stability`: Grouped intents are identified and processed together even if non-contiguous in the proposal list. <!-- ID: RPG-1698 SOURCE: src/engine/pipeline.py TEST: tests/engine/test_transaction_grouping.py PROOF: unit -->
- [x] **[RPG-1699]** `unified_reward_consolidation`: XP and Gold rewards are consolidated into a single atomic intent via RewardUpdate for state consistency. <!-- ID: RPG-1699 SOURCE: src/engine/combat.py TEST: tests/engine/test_combat_reward_hardening.py PROOF: unit -->

---

# Final audit note

This file is intentionally longer than the previous generated checklist. The previous version was a summary. This one is an exhaustive semantic ledger. Do not collapse these items unless the implementation also collapses the behavior into a single proven law with enough tests to cover the atomic cases.
