<!-- Included RPG-core test count: 413; included source subsystem groups: 7 -->

# Original `src` RPG-core Atomic Logic Checklist

This document is a port-audit checklist derived from the uploaded original `src` and `tests` snapshots.
Use it as a replacement ledger against `src_v2`. Each item should be marked as one of: preserved, intentionally divergent, unsupported, or not yet checked.

## Scope

- Included: RPG-core gameplay, combat/movement, AI/tactical/strategic logic, social/contract consequences, inventory/resource/town loops, progression, world/snapshot/determinism rules that materially affect gameplay semantics.
- Excluded from this checklist: API transport, broker plumbing, UI-only presentation, docs-only integrity, benchmark-only plumbing, and non-gameplay release scaffolding.
- Source baseline: original `src` code paths and original `tests` modules from the uploaded snapshots.

## How to use this checklist

For every checklist line below, compare `src_v2` against original `src` and record:

- evidence in original `src`
- evidence in `src_v2`
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
- [x] Action proposals are typed intents, not direct world mutation.
- [x] Every gameplay side effect is represented as a typed update bucket (mind, perception, navigation, progression, identity, routine, interaction, spatial, building, social, social-event, reputation, strategic, world, combat-trace).
- [x] Legacy reason strings and targets are coerced into structured authoritative reason/target models.
- [x] World mutation happens after proposal generation, not inside worker thought code.
- [x] Action application supports partial rejection without corrupting unrelated update domains.
- [x] Conflict resolution preserves one authoritative outcome per tick.
- [x] Worker decision-making is decoupled from authoritative application.
- [x] Replay and observability consume authoritative results rather than defining them.

original evidence: `actions/`, `engine/world_loop.py`
`src_v2` evidence: `src_v2/core/updates.py`, `src_v2/engine/kernel.py` (RESOLUTION phase), `src_v2/engine/apply.py`
divergence note: v2 strictly enforces the 6-phase authoritative loop (M7 Law) to prevent hidden mutation leaks.
proof path: `tests_v2/engine/test_authoritative_apply.py`

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
- [x] Manhattan distance is the shared spatial metric for movement and combat range where claimed.
- [x] Cardinal/tile movement and occupancy legality are explicit.
- [x] Occupied-tile movement is rejected or redirected rather than silently overlapped.
- [x] Melee legality depends on adjacency/engagement rules, not raw damage stats.
- [x] Ranged legality depends on range and line-of-sight rules.
- [x] AoE legality is split into impact-center legality and radius application.
- [x] World-time progression is distinct from readiness-based action cadence.
- [x] Quiet ticks still advance passive world consequences.
- [x] Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules.
- [x] Anti-stalemate logic handles repeated chase/kite/step-back loops.
- [x] Movement intentions exist as semantic modes (pursue, retreat, hold, reposition, intercept, guard, regroup).
- [x] Congestion is handled through waiting/yielding/sidestepping/rerouting before weakening occupancy.
- [x] Tactical choice is a bounded choice among legal actions, not a geometry exploit.

original evidence: `actions/combat.py`, `actions/move.py`, `core/logic/movement_model.py`
`src_v2` evidence: `src_v2/engine/movement.py`, `src_v2/engine/interaction.py`, `src_v2/systems/redirection.py`
divergence note: v2 utilizes a centralized `MovementSystem` and `InteractionSystem` to resolve spatial and legality conflicts within the authoritative tick loop.
proof path: `tests_v2/parity/test_movement_parity.py`

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
- [x] Looting is a channeled state with progress, interruption, and completion semantics.
- [x] Harvesting is a channeled state tied to nearby resource-node legality and harvest duration.
- [x] Loot/harvest can abort because of inventory slot pressure.
- [x] Loot/harvest can abort because of inventory weight pressure.
- [x] Inventory state tracks both slots and weight/carry burden.
- [x] Ground items, node yields, and inventory additions/removals are authoritative side effects.
- [x] Town return is a real gameplay state, not a cosmetic teleport.
- [x] Shop visits resolve bounded buy/sell behavior using inventory/gold truth.
- [x] Blacksmith visits resolve recipe/crafting/material-gating behavior.
- [x] Guild visits produce intel, quests, and material/resource hints. [RETIRED - InteractionSystem ownership]
- [x] Inn/home/class-hall visits have distinct progression or recovery semantics.
- [x] Explicit gameplay effects for entering/using specific buildings. [RETIRED - InteractionSystem ownership]

original evidence: `core/buildings.py`, `core/gameplay/items/`, `ai/states/town.py`
`src_v2` evidence: `src_v2/engine/town_resolution.py`, `src_v2/engine/shop.py`, `src_v2/engine/blacksmith.py`, `src_v2/engine/interaction.py`
divergence note: v2 converges building interactions into specialized resolution systems that enforce resource truth and material gating.
proof path: `tests_v2/parity/test_town_resolution_parity.py`, `tests_v2/parity/test_resource_interaction_parity.py`

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
- [x] Strategic state is first-class and survives across ticks (directives, projects, objectives, concerns, blockers, obligations, contracts, offers, leads, candidate zones, hypotheses).
- [x] Current project/objective continuity is explicit and bounded.
- [x] Project switching uses interruption resistance / margin logic, not full rescore every tick.
- [x] Current project gets reservation/retention priority inside bounded strategic slices.
- [x] Blockers are inferred from project/objective state and can be accurate or misdiagnosed under bounded cognition.
- [x] Leads are retained under profile-specific bandwidth limits.
- [x] Concerns are retained under profile-specific intake limits.
- [x] Detours are suggested from blockers and leads within breadth/depth limits.
- [x] Rejected/tested leads are suppressed to avoid blind retries.
- [x] Strategic overload is visible through bounded capacity metrics.
- [x] Event interpretation can mutate directives, projects, concerns, and source trust.
- [x] Knowledge remains uncertain (leads/candidate zones/hypotheses) until resolved.
- [x] Cognition graph export exposes persisted strategic state without becoming the source of truth.

original evidence: `ai/strategy/`, `core/logic/strategic_consequence_service.py`
`src_v2` evidence: `src_v2/systems/strategic.py`, `src_v2/systems/event_interpreter.py`, `src_v2/systems/detour.py`, `src_v2/systems/belief.py`, `src_v2/systems/cognition_export.py`
diverge note: v2 Phase 9 implements full interruption resistance, bandwidth enforcement, detour suggestion, event interpretation, belief cycle, and cognition graph export.
proof path: `tests_v2/strategic/`, `tests_v2/cognition/`

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
- [x] Private betrayal history can override public recruiter reputation.
- [x] Social learning updates familiarity/trust-like bonds from interaction evidence.
- [x] Social contracts and obligations are explicit strategic objects, not flavor text.
- [x] Breaking or honoring contracts has persistent consequences.
- [x] Public reputation is distinct from private narrative meaning.
- [x] Turning points and interpreted life events feed future strategic and social behavior.
- [x] Party/group cooperation is purpose-driven, not just proximity clustering.
- [x] Recruitment evaluates trust, debt, greed, capability fit, and prior trauma.

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
- [x] Attributes have domain ownership and scaling semantics.
- [x] Class choice affects starting gear, skills, and progression paths.
- [x] Skill scaling and breakthroughs are explicit progression systems.
- [x] Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates.
- [x] Items obey contract rules (type, weight, equipment legality, consumable semantics).
- [x] NPC/hero contracts define role/class/gear boundaries.
- [x] Specialization and milestone progression can mutate capability ceilings.
- [x] RPG math and synergy rules are tested as stable contracts, not intuition.

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
- [x] World generation is deterministic under seed and domain-specific RNG use.
- [x] Town, sanctuary, camps, buildings, corpses, and entities are authoritative world objects.
- [x] Entity snapshots are immutable enough for worker reasoning and deterministic replay.
- [x] No hidden mutation leaks occur from snapshot or AI evaluation paths.
- [x] Deterministic replay/delta behavior is preserved across runs with same seed.
- [x] Regional hazards, calamities, local scars, and world consequences can feed gameplay and strategy.
- [x] Entity builder and serialization preserve gameplay-relevant state safely.
- [x] Engine phase order preserves gameplay semantics and subsystem tick integrity.

## B. Test-derived atomic checklist (every included RPG-core test)

Each checkbox below is derived from one original test. Keep the original test name in the ledger so `src_v2` comparison stays auditable.

### Combat / movement rulebook & combat-time

#### `ai/test_tactical_milestone_4.py`

- [x] `test_reactive_cover_seeking`: Reactive cover seeking — Verify that actor seeks cover only when a ranged threat is visible..
- [x] `test_chokepoint_holding`: Chokepoint holding — Verify that actor identifies and holds a 1-tile gap..
- [x] `test_cardinal_opposite_bracketing`: Cardinal opposite bracketing — Verify that two allies bracket a target from opposite sides..
- [x] `test_tactical_mode_integration_handler`: Tactical mode integration handler — Verify that CombatHandler respects the tactical target_pos..

#### `arena/test_arena_harness_contract.py`

- [x] `test_arena_structural_determinism`: Arena structural determinism — Verify that the arena produced structurally identical ScenarioReports for the same seed. This validates that the simulation and its reporting layer use stable, deterministic logic. Note: This checks structural equality via Pydantic model_dump, not canonical byte-identical streams. [Milestone 7 Hardening].
- [x] `test_arena_stop_condition_wipe`: Arena stop condition wipe — Verify that the arena correctly detects when one side is eliminated..
- [x] `test_arena_stop_condition_timeout`: Arena stop condition timeout — Verify that the arena respects the max_ticks limit..
- [x] `test_arena_stop_condition_stall`: Arena stop condition stall — Verify that the arena correctly detects lack of activity (STALL) as a telemetry report..
- [x] `test_mutation_tripwire_during_decision`: Mutation tripwire during decision — Verify that any attempt to mutate entities during the decision phase raises a RuntimeError..

#### `arena/test_arena_minimal.py`

- [x] `test_minimal_tick`: Minimal tick — Verify that we can run even 1 tick without hanging..

#### `arena/test_arena_watchdog.py`

- [x] `test_watchdog_aborts_on_hang`: Watchdog aborts on hang — Verify that a tick hanging for > watchdog_timeout is aborted..
- [x] `test_watchdog_allows_fast_ticks`: Watchdog allows fast ticks — Verify that normal fast ticks are NOT aborted..

#### `arena/test_core_scenario_regression.py`

- [x] `test_regression_melee_mirror`: Regression melee mirror — Scenario 1v1-01: Symmetry Check..
- [x] `test_regression_kiting_open`: Regression kiting open — Scenario 1v1-02: Ranged vs Melee Open Field..
- [x] `test_regression_elite_vs_swarm`: Regression elite vs swarm — Scenario 1vm-01: Elite vs Swarm..

#### `arena/test_observability_audit.py`

- [x] `test_rejection_audit_aggregation`: Rejection audit aggregation — Verify that authoritative rejections are captured in ScenarioReport. [Milestone 7].
- [x] `test_out_of_range_rejection`: Out of range rejection — Verify that combat out-of-range is explicitly rejected with structured reason. [Milestone 7].

#### `arena/test_resource_isolation.py`

- [x] `test_resource_isolation_bounded_growth`: Resource isolation bounded growth — Verify that memory does not show a strong linear leak over many iterations..

#### `combat/test_anti_stalemate.py`

- [x] `test_stalemate_detection`: Stalemate detection.
- [x] `test_stalemate_loop_breaker_boosts_flee`: Stalemate loop breaker boosts flee.

#### `combat/test_anti_stalemate_milestone_2.py`

- [x] `test_stalemate_detection_and_breaker`: Stalemate detection and breaker — Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker..

#### `combat/test_combat_context_milestone_2.py`

- [x] `test_high_ground_bonus`: High ground bonus — Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR..
- [x] `test_flanking_bonus`: Flanking bonus — Verify Flanking bonus applies when defender is bracketed north/south..
- [x] `test_moved_penalty`: Moved penalty — Verify Moved Recently penalty applies when attacker has moved this tick..
- [x] `test_ranged_cover_bonus`: Ranged cover bonus — Verify Cover bonus applies against ranged attacks when adjacent to WALL..

#### `combat/test_combat_movement_rulebook.py`

- [x] `test_manhattan_distance`: Manhattan distance — Verify Manhattan distance calculation..
- [x] `test_orthogonal_adjacency`: Orthogonal adjacency — Verify that only orthogonal tiles are adjacent..
- [x] `test_check_range`: Check range — Verify range enforcement..
- [x] `test_check_occupancy`: Check occupancy — Verify 1-unit-per-tile occupancy rule..
- [x] `test_aoe_legality`: Aoe legality — Verify AoE impact constraints..
- [x] `test_aoe_splash_radius`: Aoe splash radius — Verify entities affected by splash radius..
- [x] `test_get_occupant_id`: Get occupant id — Verify occupant lookup..
- [x] `test_check_targeting_legality`: Check targeting legality — Verify consolidated targeting rules (Range + LOS)..

#### `combat/test_engagement_contract.py`

- [x] `test_engagement_detection`: Engagement detection.
- [x] `test_engagement_clears_on_separation`: Engagement clears on separation.
- [x] `test_engagement_respects_hostility`: Engagement respects hostility.

#### `combat/test_opportunity_attacks.py`

- [x] `test_oa_triggered_on_disengagement`: Oa triggered on disengagement.
- [x] `test_oa_not_triggered_if_staying_engaged_with_same_attacker`: Oa not triggered if staying engaged with same attacker.

#### `combat/test_target_stickiness.py`

- [x] `test_target_stickiness_bias`: Target stickiness bias.

#### `combat/test_world_time_progression.py`

- [x] `test_passive_progression_on_quiet_tick`: Passive progression on quiet tick — Verify that biological decay and lifecycle systems run even if entity doesn't act..
- [x] `test_hero_lifecycle_on_quiet_tick`: Hero lifecycle on quiet tick — Verify that HeroLifecycle (e.g. proximity bonding) runs even if no entity acts..

#### `engine/test_quiet_tick_integrity.py`

- [x] `test_scenario_1_dead_world_progression`: Scenario 1 dead world progression — Scenario 1: No living entities. Verify tick still increments and systems advance..
- [x] `test_scenario_2_sleeping_world_biological_decay`: Scenario 2 sleeping world biological decay — Scenario 2: All entities have high next_act_at. Verify biological decay hits..
- [x] `test_scenario_3_stationary_world_proximity_bonding`: Scenario 3 stationary world proximity bonding — Scenario 3: Two heroes are stationary. Verify bonding occurs via HeroLifecycleSystem..
- [x] `test_scenario_4_subsystem_advancement`: Scenario 4 subsystem advancement — Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply..

#### `integration/ai/test_wind_pillar_navigation.py`

- [x] `test_navigation_uses_flow_field_for_far_town`: Navigation uses flow field for far town.
- [x] `test_navigation_uses_astar_for_near_target`: Navigation uses astar for near target.
- [x] `test_navigation_uses_flow_field_for_world_boss`: Navigation uses flow field for world boss.

#### `test_party_tactics.py`

- [x] `test_vanguard_biases`: Vanguard biases.
- [x] `test_support_biases`: Support biases.
- [x] `test_protector_biases`: Protector biases.

#### `unit/ai/test_skirmish.py`

- [x] `test_skirmish_boosts_move_for_ranged`: Skirmish boosts move for ranged.
- [x] `test_skirmish_does_not_boost_melee`: Skirmish does not boost melee.

#### `unit/ai/test_tactical_behavior_contract.py`

- [x] `test_melee_striker_closes_distance`: Melee striker closes distance.
- [x] `test_ranged_skirmisher_kites_when_close`: Ranged skirmisher kites when close.
- [x] `test_ranged_skirmisher_maintains_distance`: Ranged skirmisher maintains distance.
- [x] `test_safe_shot_detection`: Safe shot detection.
- [x] `test_tactical_retreat_at_low_hp`: Tactical retreat at low hp.
- [x] `test_group_spacing_preservation`: Group spacing preservation.

#### `unit/core/logic/test_movement_model.py`

- [x] `test_movement_model_basic_path`: Movement model basic path.
- [x] `test_movement_model_yielding_priority`: Movement model yielding priority.
- [x] `test_movement_model_stuck_threshold`: Movement model stuck threshold.

### Resource interaction / inventory / town loop

#### `integration/gameplay/test_toughness_decay.py`

- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP..
- [x] `test_stat_decay_inactivity`: Stat decay inactivity — Verify that stat decay can be triggered..
- [x] `test_toughness_hardening_integration`: Toughness hardening integration — Integration test for the restored hardening logic in CombatAction..

#### `test_building_unification.py`

- [x] `test_actor`: Actor.
- [x] `test_visit_guild_no_legacy_goals`: Visit guild no legacy goals — Verify that visiting the guild produces StrategicUpdate and PerceptionUpdate, but no string goals..
- [x] `test_visit_blacksmith_blocker_emission`: Visit blacksmith blocker emission — Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state..
- [x] `test_visit_class_hall_resolution`: Visit class hall resolution — Verify that learning a skill emits a strategic resolution for the corresponding capability blocker..
- [x] `test_visit_blacksmith_crafting_resolution`: Visit blacksmith crafting resolution — Verify that crafting an item emits a strategic resolution for the material blocker..
- [x] `test_visit_home_upgrade_resolution`: Visit home upgrade resolution — Verify that home storage upgrade emits a strategic resolution for home maintenance..
- [x] `test_detour_suggestion_lifecycle_awareness`: Detour suggestion lifecycle awareness — Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones..

#### `unit/ai/test_routine_cycle.py`

- [x] `test_biological_decay_authoritative`: Biological decay authoritative.
- [x] `test_sleep_goal_utility_at_night`: Sleep goal utility at night.
- [x] `test_nocturnal_predator_bonus`: Nocturnal predator bonus.

#### `unit/ai/test_routine_needs.py`

- [x] `test_biological_utility_biasing`: Biological utility biasing.
- [x] `test_inn_visit_leads_to_sleeping`: Inn visit leads to sleeping.
- [x] `test_home_visit_leads_to_eating`: Home visit leads to eating.
- [x] `test_sleeping_recovery_cycle`: Sleeping recovery cycle.

#### `unit/core/gameplay/test_item_contracts.py`

- [x] `test_weapon_ranges_integrity`: Weapon ranges integrity — Verify that specific weapons have their intended ranges in the registry..
- [x] `test_weapon_power_integrity`: Weapon power integrity — Verify that core progression weapons have their primary power correctly set..
- [x] `test_registry_identity_integrity`: Registry identity integrity — Ensure all core items are successfully loaded and have consistent IDs..

#### `unit/systems/test_difficulty_scaling.py`

- [x] `test_tier1_is_baseline`: Tier1 is baseline.
- [x] `test_tier4_has_higher_stats_than_tier1`: Tier4 has higher stats than tier1 — Same seed, same enemy tier - tier 4 difficulty should have higher HP/ATK..
- [x] `test_tier4_hp_significantly_higher`: Tier4 hp significantly higher — Tier 4 HP multiplier is 4.0x on base stats; with flat bonuses from traits/attributes the effective ratio will be lower but still substantial..
- [x] `test_difficulty_sets_level_range`: Difficulty sets level range — Entities in tier 3 should have level in [5, 10]..
- [x] `test_gold_scales_with_difficulty`: Gold scales with difficulty — Tier 4 gold multiplier is 4.0x..
- [x] `test_race_tier4_stronger_than_tier1`: Race tier4 stronger than tier1.
- [x] `test_race_difficulty_tier_set`: Race difficulty tier set.
- [x] `test_race_level_in_range`: Race level in range.
- [x] `test_all_races_scale`: All races scale — All four races should scale with difficulty..
- [x] `test_boss_diff_capped_at_4`: Boss diff capped at 4.
- [x] `test_boss_diff_adds_one`: Boss diff adds one.
- [x] `test_spawn_default_is_tier1`: Spawn default is tier1.
- [x] `test_spawn_race_default_is_tier1`: Spawn race default is tier1.

#### `unit/systems/test_toughness_decay.py`

- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP..
- [x] `test_stat_decay_inactivity`: Stat decay inactivity — Verify that idling for 1000+ ticks triggers stat decay..
