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
- [ ] Every gameplay side effect is represented as a typed update bucket (mind, perception, navigation, progression, identity, routine, interaction, spatial, building, social, social-event, reputation, strategic, world, combat-trace).
- [ ] Legacy reason strings and targets are coerced into structured authoritative reason/target models.
- [x] World mutation happens after proposal generation, not inside worker thought code.
- [x] Action application supports partial rejection without corrupting unrelated update domains.
- [x] Conflict resolution preserves one authoritative outcome per tick.
- [x] Worker decision-making is decoupled from authoritative application.
- [x] Replay and observability consume authoritative results rather than defining them.

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
- [ ] AoE legality is split into impact-center legality and radius application.
- [ ] World-time progression is distinct from readiness-based action cadence.
- [x] Quiet ticks still advance passive world consequences.
- [x] Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules.
- [x] Anti-stalemate logic handles repeated chase/kite/step-back loops.
- [ ] Movement intentions exist as semantic modes (pursue, retreat, hold, reposition, intercept, guard, regroup).
- [ ] Congestion is handled through waiting/yielding/sidestepping/rerouting before weakening occupancy.
- [x] Tactical choice is a bounded choice among legal actions, not a geometry exploit.

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
- [ ] Guild visits produce intel, quests, and material/resource hints.
- [x] Inn/home/class-hall visits have distinct progression or recovery semantics.
- [x] Building interactions are explicit gameplay slices, not generic proximity triggers.

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
- [ ] Current project gets reservation/retention priority inside bounded strategic slices.
- [x] Blockers are inferred from project/objective state and can be accurate or misdiagnosed under bounded cognition.
- [x] Leads are retained under profile-specific bandwidth limits.
- [x] Concerns are retained under profile-specific intake limits.
- [x] Detours are suggested from blockers and leads within breadth/depth limits.
- [x] Rejected/tested leads are suppressed to avoid blind retries.
- [ ] Strategic overload is visible through bounded capacity metrics.
- [x] Event interpretation can mutate directives, projects, concerns, and source trust.
- [x] Knowledge remains uncertain (leads/candidate zones/hypotheses) until resolved.
- [x] Cognition graph export exposes persisted strategic state without becoming the source of truth.

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
- [ ] Party/group cooperation is purpose-driven, not just proximity clustering.
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
- [ ] Class choice affects starting gear, skills, and progression paths.
- [ ] Skill scaling and breakthroughs are explicit progression systems.
- [x] Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates.
- [ ] Items obey contract rules (type, weight, equipment legality, consumable semantics).
- [ ] NPC/hero contracts define role/class/gear boundaries.
- [ ] Specialization and milestone progression can mutate capability ceilings.
- [ ] RPG math and synergy rules are tested as stable contracts, not intuition.

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
- [ ] Town, sanctuary, camps, buildings, corpses, and entities are authoritative world objects.
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

- [ ] `test_reactive_cover_seeking`: Reactive cover seeking — Verify that actor seeks cover only when a ranged threat is visible..
- [ ] `test_chokepoint_holding`: Chokepoint holding — Verify that actor identifies and holds a 1-tile gap..
- [ ] `test_cardinal_opposite_bracketing`: Cardinal opposite bracketing — Verify that two allies bracket a target from opposite sides..
- [ ] `test_tactical_mode_integration_handler`: Tactical mode integration handler — Verify that CombatHandler respects the tactical target_pos..

#### `arena/test_arena_harness_contract.py`

- [ ] `test_arena_structural_determinism`: Arena structural determinism — Verify that the arena produced structurally identical ScenarioReports for the same seed. This validates that the simulation and its reporting layer use stable, deterministic logic. Note: This checks structural equality via Pydantic model_dump, not canonical byte-identical streams. [Milestone 7 Hardening].
- [ ] `test_arena_stop_condition_wipe`: Arena stop condition wipe — Verify that the arena correctly detects when one side is eliminated..
- [ ] `test_arena_stop_condition_timeout`: Arena stop condition timeout — Verify that the arena respects the max_ticks limit..
- [x] `test_arena_stop_condition_stall`: Arena stop condition stall — Verify that the arena correctly detects lack of activity (STALL) as a telemetry report..
- [ ] `test_mutation_tripwire_during_decision`: Mutation tripwire during decision — Verify that any attempt to mutate entities during the decision phase raises a RuntimeError..

#### `arena/test_arena_minimal.py`

- [ ] `test_minimal_tick`: Minimal tick — Verify that we can run even 1 tick without hanging..

#### `arena/test_arena_watchdog.py`

- [ ] `test_watchdog_aborts_on_hang`: Watchdog aborts on hang — Verify that a tick hanging for > watchdog_timeout is aborted..
- [ ] `test_watchdog_allows_fast_ticks`: Watchdog allows fast ticks — Verify that normal fast ticks are NOT aborted..

#### `arena/test_core_scenario_regression.py`

- [ ] `test_regression_melee_mirror`: Regression melee mirror — Scenario 1v1-01: Symmetry Check..
- [ ] `test_regression_kiting_open`: Regression kiting open — Scenario 1v1-02: Ranged vs Melee Open Field..
- [ ] `test_regression_elite_vs_swarm`: Regression elite vs swarm — Scenario 1vm-01: Elite vs Swarm..

#### `arena/test_observability_audit.py`

- [ ] `test_rejection_audit_aggregation`: Rejection audit aggregation — Verify that authoritative rejections are captured in ScenarioReport. [Milestone 7].
- [ ] `test_out_of_range_rejection`: Out of range rejection — Verify that combat out-of-range is explicitly rejected with structured reason. [Milestone 7].

#### `arena/test_resource_isolation.py`

- [ ] `test_resource_isolation_bounded_growth`: Resource isolation bounded growth — Verify that memory does not show a strong linear leak over many iterations..

#### `combat/test_anti_stalemate.py`

- [x] `test_stalemate_detection`: Stalemate detection.
- [x] `test_stalemate_loop_breaker_boosts_flee`: Stalemate loop breaker boosts flee.

#### `combat/test_anti_stalemate_milestone_2.py`

- [x] `test_stalemate_detection_and_breaker`: Stalemate detection and breaker — Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker..

#### `combat/test_combat_context_milestone_2.py`

- [x] `test_high_ground_bonus`: High ground bonus — Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR..
- [x] `test_flanking_bonus`: Flanking bonus — Verify Flanking bonus applies when defender is bracketed north/south..
- [ ] `test_moved_penalty`: Moved penalty — Verify Moved Recently penalty applies when attacker has moved this tick..
- [ ] `test_ranged_cover_bonus`: Ranged cover bonus — Verify Cover bonus applies against ranged attacks when adjacent to WALL..

#### `combat/test_combat_movement_rulebook.py`

- [x] `test_manhattan_distance`: Manhattan distance — Verify Manhattan distance calculation..
- [x] `test_orthogonal_adjacency`: Orthogonal adjacency — Verify that only orthogonal tiles are adjacent..
- [x] `test_check_range`: Check range — Verify range enforcement..
- [x] `test_check_occupancy`: Check occupancy — Verify 1-unit-per-tile occupancy rule..
- [ ] `test_aoe_legality`: Aoe legality — Verify AoE impact constraints..
- [ ] `test_aoe_splash_radius`: Aoe splash radius — Verify entities affected by splash radius..
- [ ] `test_get_occupant_id`: Get occupant id — Verify occupant lookup..
- [x] `test_check_targeting_legality`: Check targeting legality — Verify consolidated targeting rules (Range + LOS)..

#### `combat/test_engagement_contract.py`

- [x] `test_engagement_detection`: Engagement detection.
- [x] `test_engagement_clears_on_separation`: Engagement clears on separation.
- [x] `test_engagement_respects_hostility`: Engagement respects hostility.

#### `combat/test_opportunity_attacks.py`

- [x] `test_oa_triggered_on_disengagement`: Oa triggered on disengagement.
- [ ] `test_oa_not_triggered_if_staying_engaged_with_same_attacker`: Oa not triggered if staying engaged with same attacker.

#### `combat/test_target_stickiness.py`

- [x] `test_target_stickiness_bias`: Target stickiness bias.

#### `combat/test_world_time_progression.py`

- [ ] `test_passive_progression_on_quiet_tick`: Passive progression on quiet tick — Verify that biological decay and lifecycle systems run even if entity doesn't act..
- [ ] `test_hero_lifecycle_on_quiet_tick`: Hero lifecycle on quiet tick — Verify that HeroLifecycle (e.g. proximity bonding) runs even if no entity acts..

#### `engine/test_quiet_tick_integrity.py`

- [x] `test_scenario_1_dead_world_progression`: Scenario 1 dead world progression — Scenario 1: No living entities. Verify tick still increments and systems advance..
- [x] `test_scenario_2_sleeping_world_biological_decay`: Scenario 2 sleeping world biological decay — Scenario 2: All entities have high next_act_at. Verify biological decay hits..
- [ ] `test_scenario_3_stationary_world_proximity_bonding`: Scenario 3 stationary world proximity bonding — Scenario 3: Two heroes are stationary. Verify bonding occurs via HeroLifecycleSystem..
- [x] `test_scenario_4_subsystem_advancement`: Scenario 4 subsystem advancement — Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply..

#### `integration/ai/test_wind_pillar_navigation.py`

- [ ] `test_navigation_uses_flow_field_for_far_town`: Navigation uses flow field for far town.
- [ ] `test_navigation_uses_astar_for_near_target`: Navigation uses astar for near target.
- [ ] `test_navigation_uses_flow_field_for_world_boss`: Navigation uses flow field for world boss.

#### `test_party_tactics.py`

- [ ] `test_vanguard_biases`: Vanguard biases.
- [ ] `test_support_biases`: Support biases.
- [ ] `test_protector_biases`: Protector biases.

#### `unit/ai/test_skirmish.py`

- [ ] `test_skirmish_boosts_move_for_ranged`: Skirmish boosts move for ranged.
- [ ] `test_skirmish_does_not_boost_melee`: Skirmish does not boost melee.

#### `unit/ai/test_tactical_behavior_contract.py`

- [x] `test_melee_striker_closes_distance`: Melee striker closes distance.
- [ ] `test_ranged_skirmisher_kites_when_close`: Ranged skirmisher kites when close.
- [ ] `test_ranged_skirmisher_maintains_distance`: Ranged skirmisher maintains distance.
- [ ] `test_safe_shot_detection`: Safe shot detection.
- [x] `test_tactical_retreat_at_low_hp`: Tactical retreat at low hp.
- [ ] `test_group_spacing_preservation`: Group spacing preservation.

#### `unit/core/logic/test_movement_model.py`

- [x] `test_movement_model_basic_path`: Movement model basic path.
- [x] `test_movement_model_yielding_priority`: Movement model yielding priority.
- [ ] `test_movement_model_stuck_threshold`: Movement model stuck threshold.

### Resource interaction / inventory / town loop

#### `integration/gameplay/test_toughness_decay.py`

- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP..
- [ ] `test_stat_decay_inactivity`: Stat decay inactivity — Verify that stat decay can be triggered..
- [ ] `test_toughness_hardening_integration`: Toughness hardening integration — Integration test for the restored hardening logic in CombatAction..

#### `test_building_unification.py`

- [ ] `test_actor`: Actor.
- [ ] `test_visit_guild_no_legacy_goals`: Visit guild no legacy goals — Verify that visiting the guild produces StrategicUpdate and PerceptionUpdate, but no string goals..
- [x] `test_visit_blacksmith_blocker_emission`: Visit blacksmith blocker emission — Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state..
- [ ] `test_visit_class_hall_resolution`: Visit class hall resolution — Verify that learning a skill emits a strategic resolution for the corresponding capability blocker..
- [ ] `test_visit_blacksmith_crafting_resolution`: Visit blacksmith crafting resolution — Verify that crafting an item emits a strategic resolution for the material blocker..
- [ ] `test_visit_home_upgrade_resolution`: Visit home upgrade resolution — Verify that home storage upgrade emits a strategic resolution for home maintenance..
- [x] `test_detour_suggestion_lifecycle_awareness`: Detour suggestion lifecycle awareness — Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones..

#### `unit/ai/test_routine_cycle.py`

- [x] `test_biological_decay_authoritative`: Biological decay authoritative.
- [x] `test_sleep_goal_utility_at_night`: Sleep goal utility at night.
- [ ] `test_nocturnal_predator_bonus`: Nocturnal predator bonus.

#### `unit/ai/test_routine_needs.py`

- [ ] `test_biological_utility_biasing`: Biological utility biasing.
- [x] `test_inn_visit_leads_to_sleeping`: Inn visit leads to sleeping.
- [ ] `test_home_visit_leads_to_eating`: Home visit leads to eating.
- [x] `test_sleeping_recovery_cycle`: Sleeping recovery cycle.

#### `unit/core/gameplay/test_item_contracts.py`

- [ ] `test_weapon_ranges_integrity`: Weapon ranges integrity — Verify that specific weapons have their intended ranges in the registry..
- [ ] `test_weapon_power_integrity`: Weapon power integrity — Verify that core progression weapons have their primary power correctly set..
- [ ] `test_registry_identity_integrity`: Registry identity integrity — Ensure all core items are successfully loaded and have consistent IDs..

#### `unit/systems/test_difficulty_scaling.py`

- [ ] `test_tier1_is_baseline`: Tier1 is baseline.
- [ ] `test_tier4_has_higher_stats_than_tier1`: Tier4 has higher stats than tier1 — Same seed, same enemy tier - tier 4 difficulty should have higher HP/ATK..
- [ ] `test_tier4_hp_significantly_higher`: Tier4 hp significantly higher — Tier 4 HP multiplier is 4.0x on base stats; with flat bonuses from traits/attributes the effective ratio will be lower but still substantial..
- [x] `test_difficulty_sets_level_range`: Difficulty sets level range — Entities in tier 3 should have level in [5, 10]..
- [ ] `test_gold_scales_with_difficulty`: Gold scales with difficulty — Tier 4 gold multiplier is 4.0x..
- [ ] `test_race_tier4_stronger_than_tier1`: Race tier4 stronger than tier1.
- [ ] `test_race_difficulty_tier_set`: Race difficulty tier set.
- [x] `test_race_level_in_range`: Race level in range.
- [ ] `test_all_races_scale`: All races scale — All four races should scale with difficulty..
- [ ] `test_boss_diff_capped_at_4`: Boss diff capped at 4.
- [ ] `test_boss_diff_adds_one`: Boss diff adds one.
- [ ] `test_spawn_default_is_tier1`: Spawn default is tier1.
- [ ] `test_spawn_race_default_is_tier1`: Spawn race default is tier1.

#### `unit/systems/test_toughness_decay.py`

- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP..
- [ ] `test_stat_decay_inactivity`: Stat decay inactivity — Verify that idling for 1000+ ticks triggers stat decay..

### Strategic mind / cognition / projects / blockers / leads

#### `ai/test_bounded_blockers.py`

- [ ] `test_accurate_diagnosis_high_wisdom`: Accurate diagnosis high wisdom.
- [ ] `test_misdiagnosis_low_wisdom`: Misdiagnosis low wisdom.

#### `ai/test_bounded_detours.py`

- [x] `test_detour_breadth_limit`: Detour breadth limit.
- [ ] `test_detour_depth_limit_fallback`: Detour depth limit fallback.
- [x] `test_retry_suppression`: Retry suppression.

#### `ai/test_bounded_objective_continuity.py`

- [ ] `test_objective_derivation_precedence_blocker_first`: Objective derivation precedence blocker first.
- [ ] `test_objective_derivation_precedence_active_objective_if_no_blocker`: Objective derivation precedence active objective if no blocker.
- [ ] `test_objective_derivation_precedence_first_unresolved_if_no_active`: Objective derivation precedence first unresolved if no active.

#### `ai/test_bounded_project_continuity.py`

- [x] `test_project_retention_when_rival_is_below_margin`: Project retention when rival is below margin.
- [x] `test_project_switch_when_rival_is_above_margin`: Project switch when rival is above margin.
- [x] `test_switch_margin_increases_with_higher_resistance_profile`: Switch margin increases with higher resistance profile.

#### `ai/test_bounded_strategic_slice.py`

- [ ] `test_low_profile_entity_has_smaller_active_slice_than_high_profile_entity`: Low profile entity has smaller active slice than high profile entity.
- [ ] `test_concern_intake_is_capped_by_profile`: Concern intake is capped by profile.
- [x] `test_lead_retention_is_capped_by_profile`: Lead retention is capped by profile.
- [x] `test_reserved_current_project_slot_is_used_when_current_project_exists`: Reserved current project slot is used when current project exists.
- [x] `test_dropped_candidate_counts_are_deterministic`: Dropped candidate counts are deterministic.

#### `ai/test_cognition_capacity_determinism.py`

- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: Profile derivation is deterministic for same entity state.
- [ ] `test_profile_derivation_is_independent_of_tick_in_milestone_1`: Profile derivation is independent of tick in milestone 1.
- [x] `test_profile_derivation_does_not_use_rng`: Profile derivation does not use rng.

#### `ai/test_cognition_capacity_non_mutation.py`

- [ ] `test_build_profile_does_not_mutate_entity_attributes`: Build profile does not mutate entity attributes.
- [ ] `test_build_profile_does_not_mutate_caps`: Build profile does not mutate caps.
- [ ] `test_build_profile_does_not_mutate_stamina`: Build profile does not mutate stamina.
- [ ] `test_build_profile_returns_new_profile_object_each_call`: Build profile returns new profile object each call.

#### `ai/test_cognition_explainability.py`

- [ ] `test_overload_metadata_population`: Overload metadata population — Verify that primary_overload_source and last_overload_tick are correctly populated in replay..
- [ ] `test_personality_formula_impact`: Personality formula impact — Verify that personality archetypes and traits impact the capacity profile..
- [ ] `test_inspector_smoke_coverage`: Inspector smoke coverage — Smoke test to ensure EntityInspector (AIPresenter) doesn't crash with new fields..

#### `ai/test_cognition_integrity.py`

- [ ] `test_ui_contract_alignment`: Ui contract alignment — Verify that every field in bounded_cognition_ui_contract.md exists in Pydantic schemas..
- [ ] `test_feature_spec_replay_alignment`: Feature spec replay alignment — Verify that replay fields mentioned in feature spec are present in recorder..
- [ ] `test_feature_spec_graph_export_alignment`: Feature spec graph export alignment — Verify that graph export fields mentioned in feature spec are present in exporter..
- [ ] `test_test_matrix_existence`: Test matrix existence — Verify that all test modules mentioned in test_matrix.md actually exist..
- [x] `test_populated_artifact_consistency`: Populated artifact consistency — Verify that a live HeadlessRunner execution produces populated and consistent artifacts. [TRACK 1 HARDENING].
- [ ] `test_truth_surface_parity`: Truth surface parity — Verify that Replay, API Schema, and Cognition Graph maintain strict parity. [TRUTH SURFACE OWNERSHIP PROOF].
- [ ] `test_documentation_alignment`: Documentation alignment — Verify that documented fields in intel_capacity_implementation_updated.md are real. [MILESTONE 8 PROOF].

#### `ai/test_directive_mutation_thresholds.py`

- [ ] `test_directive_mutation_thresholds`: Directive mutation thresholds — Verify that directives only mutate after repeated thresholded events..

#### `ai/test_event_interpretation.py`

- [x] `test_stable_concern_generation`: Stable concern generation.
- [ ] `test_unstable_panic_concern`: Unstable panic concern.
- [ ] `test_interruption_resistance_stable`: Interruption resistance stable.
- [ ] `test_interruption_resistance_unstable`: Interruption resistance unstable.
- [ ] `test_identity_drift_resistance`: Identity drift resistance.
- [ ] `test_rumor_sensitivity_unstable`: Rumor sensitivity unstable.

#### `ai/test_lead_learning.py`

- [ ] `test_learning_success`: Learning success.
- [ ] `test_learning_failure`: Learning failure.

#### `ai/test_social_cognition.py`

- [ ] `test_social_blocker_detection_solo`: Social blocker detection solo.
- [ ] `test_social_misjudgment_low_stability`: Social misjudgment low stability.
- [ ] `test_social_bandwidth_pool_limiting`: Social bandwidth pool limiting.

#### `ai/test_source_trust_learning_loop.py`

- [x] `test_source_trust_learning_loop`: Source trust learning loop — Prove that future weighting is affected by source trust after a learning event..

#### `ai/test_uncertainty_resolution_loop.py`

- [ ] `test_uncertainty_resolution_loop`: Uncertainty resolution loop — Prove that proximity to a rumored zone resolves imprecise leads into precise targets..

#### `core/test_cognition_graph_exporter.py`

- [x] `test_export_empty_strategy`: Export empty strategy — Verify export from an entity with no strategic state..
- [x] `test_export_with_core_strategic_state`: Export with core strategic state — Verify export of directives, projects, and objectives..
- [x] `test_export_determinism`: Export determinism — Verify that multiple exports from the same state are identical..
- [x] `test_non_mutation`: Non mutation — Verify that exporter does not mutate the source entity..

#### `core/test_strategy_models.py`

- [ ] `test_strategic_model_rebuild`: Strategic model rebuild — Verify pydantic model rebuild handles recursive refs..
- [ ] `test_directive_creation`: Directive creation.
- [x] `test_strategic_state_defaults`: Strategic state defaults.
- [x] `test_strategic_state_serialization`: Strategic state serialization.

#### `integration/strategy/test_cognition_graph_regression.py`

- [ ] `test_cognition_graph_deterministic_simulation`: Cognition graph deterministic simulation — Verify that a simulation produces a valid, repeatable cognition graph..
- [ ] `test_graph_structural_invariants`: Graph structural invariants — Verify that the graph follows structural rules across ticks..

#### `integration/strategy/test_strategic_brain_integration.py`

- [x] `test_strategic_pivot_on_regional_danger`: Strategic pivot on regional danger — Verify that heroes pivot from personal quests to regional stabilization during high-danger events..
- [x] `test_scar_detection`: Scar detection — Verify that heroes sense nearby world trauma (scars) and investigate..
- [x] `test_near_death_triggers_survival_consequences`: Near death triggers survival consequences — Verify that a NEAR_DEATH event generates a concern and suspends the current project via applicator..
- [x] `test_betrayal_mutates_directives`: Betrayal mutates directives — Verify that a salient betrayal turning point adds an 'Avenge' directive..
- [ ] `test_divergent_home_response`: Divergent home response — Verify that only entities with place attachment react strongly to home damage..
- [x] `test_betrayal_trauma_affects_recruitment`: Betrayal trauma affects recruitment — Verify that a recent betrayal makes entities less willing to accept recruitment offers..

#### `integration/strategy/test_strategic_capacity_enforcement.py`

- [x] `test_budget_enforcement_truncation`: Budget enforcement truncation — Verify that candidate_zone_limit correctly truncates the pool AND preserves highest-scored zones..
- [x] `test_source_trust_behavioral_impact`: Source trust behavioral impact — Verify that updating source trust results in different weighting in the next cycle. [MILESTONE 3].
- [ ] `test_overload_metrics_visibility`: Overload metrics visibility — Verify that primary_overload_source and metrics are populated when stressed..

#### `integration/strategy/test_strategic_continuity.py`

- [x] `test_directive_mutation_salience_threshold`: Directive mutation salience threshold — Verify that only high-salience turning points trigger mutations..
- [x] `test_directive_priority_strengthening`: Directive priority strengthening — Verify that repeated high-salience events strengthen directive priority..

#### `integration/strategy/test_strategic_continuity_hardening.py`

- [ ] `test_strategic_objective_continuity`: Strategic objective continuity — Prove that an existing objective is preserved if the project remains stable and no high blockers appear..
- [ ] `test_objective_resumption_aligns_with_tactical`: Objective resumption aligns with tactical — Verify that a resumed objective correctly drives goal selection..

#### `integration/strategy/test_strategic_determinism.py`

- [ ] `test_harness_determinism`: Harness determinism — Verify that two runs with the same seed produce byte-identical results..
- [x] `test_harness_non_determinism_different_seed`: Harness non determinism different seed — Verify that different seeds produce different outcomes (basic sanity check)..

#### `integration/strategy/test_strategic_explainability.py`

- [ ] `test_candidate_zone_enforcement`: Candidate zone enforcement — Verify that candidate_zone_limit is enforced and drops excess zones..
- [ ] `test_ally_evaluation_enforcement`: Ally evaluation enforcement — Verify that ally_evaluation_limit caps contracts and offers evaluated..
- [ ] `test_overload_source_trauma`: Overload source trauma — Verify that heavy HP damage triggers 'trauma' as the primary overload source..
- [ ] `test_switch_reason_transparency`: Switch reason transparency — Verify that a project switch provides a human-readable reason..

#### `integration/strategy/test_strategic_persistence.py`

- [x] `test_persistence_boost_prevents_switching`: Persistence boost prevents switching — Verify that the persistence boost prevents switching to a slightly better project..
- [x] `test_project_lock_prevents_switching`: Project lock prevents switching — Verify that project_lock_until strictly prevents any switches despite critical concerns..
- [x] `test_interruption_threshold_overridden_by_major_threat`: Interruption threshold overridden by major threat — Verify that a massive threat CAN overcome the interruption threshold..
- [ ] `test_strategic_pipeline_home_threat`: Strategic pipeline home threat — Verify the flow from life event through StrategicConsequenceService to project pivot..
- [x] `test_resume_restores_valid_objective`: Resume restores valid objective — Verify that brain restores the last active objective when resuming a project. [Strategy M2].
- [ ] `test_resumed_objective_survives_cycle`: Resumed objective survives cycle — Verify that a restored objective doesn't immediately flip back to ProjectRecord.objectives[0] if it matches. [Strategy M2].

#### `integration/strategy/test_strategic_replay_determinism.py`

- [ ] `test_world_strategic_registry_deep_isolation`: World strategic registry deep isolation — Verify that WorldStrategicRegistry.copy() performs a deep copy..
- [ ] `test_strategic_replay_graph_equality`: Strategic replay graph equality — Verify that replaying from a snapshot yields bit-identical cognition graphs..
- [ ] `test_lead_outcome_grounding_verification`: Lead outcome grounding verification — Verify that precise leads correctly ground into world entities..

#### `integration/strategy/test_strategic_resume_objective.py`

- [x] `test_objective_resume_reliability`: Objective resume reliability — Verify that a suspended objective is resumed correctly..

#### `integration/strategy/test_strategic_structural_integrity.py`

- [ ] `test_snapshot_strategic_isolation`: Snapshot strategic isolation — Verify that Snapshot.from_world deep-copies and freezes strategic state..
- [ ] `test_strategic_update_merging_identical_ids`: Strategic update merging identical ids — Verify that ActionSystem merges updates with identical IDs correctly..
- [ ] `test_serialization_round_trip`: Serialization round trip — Verify that StrategicState survives full JSON serialization round-trip..
- [ ] `test_strategic_update_coercion_from_dict`: Strategic update coercion from dict — Verify that StrategicUpdate correctly coerces dicts to models (worker transport emulation)..

#### `integration/strategy/test_strategic_transport.py`

- [ ] `test_strategic_update_multi_record_transport`: Strategic update multi record transport — Verify that a single proposal can carry multiple strategic updates..
- [ ] `test_strategic_update_repeated_id_last_one_wins`: Strategic update repeated id last one wins — Verify that repeated IDs in a single update follow last-one-wins semantics..
- [x] `test_strategic_update_idempotency_over_ticks`: Strategic update idempotency over ticks — Verify that applying the same update multiple times is idempotent..
- [ ] `test_strategic_update_target_routing`: Strategic update target routing — Verify that strategic updates can be routed to a target entity..

#### `integration/strategy/test_strategic_world_integration.py`

- [ ] `test_world_strategic_registry_persistence`: World strategic registry persistence — Verify that WorldStrategicRegistry is preserved in snapshots..
- [ ] `test_strategic_world_integration_system_pruning`: Strategic world integration system pruning — Verify that the system prunes expired world opportunities..
- [x] `test_telemetry_strategic_metrics`: Telemetry strategic metrics — Verify that TelemetrySystem collects strategic metrics..

#### `unit/ai/strategy/test_strategic_biasing.py`

- [x] `test_biological_need_to_strategic_bias`: Biological need to strategic bias.
- [x] `test_directive_to_project_flow`: Directive to project flow.
- [ ] `test_strategic_bias_impact_on_selection`: Strategic bias impact on selection.

#### `unit/ai/strategy/test_strategic_uncertainty.py`

- [x] `test_contradiction_degrades_certainty`: Contradiction degrades certainty — Verify that leads with contradictions lose certainty based on profile sensitivity. [MILESTONE 5].
- [x] `test_hypothesis_impacted_by_contradiction`: Hypothesis impacted by contradiction — Verify that hypotheses lose confidence when supporting leads are contradicted. [MILESTONE 5].

#### `unit/strategy/test_strategic_services.py`

- [ ] `test_canonical_blocker_structure`: Canonical blocker structure — Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs..
- [ ] `test_strategic_snapshot_isolation`: Strategic snapshot isolation — Verify that deep copying an entity results in a fully isolated strategic tree..
- [ ] `test_belief_decay_aoa_purity`: Belief decay aoa purity — Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place..
- [ ] `test_social_applicator_aoa_purity`: Social applicator aoa purity — Verify that SocialStateApplicator returns updates and does not mutate the world..
- [x] `test_concern_generation_near_death`: Concern generation near death.
- [x] `test_directive_mutation_near_death`: Directive mutation near death.
- [x] `test_project_mutation_interruption`: Project mutation interruption.
- [ ] `test_strategic_update_blocker_merging`: Strategic update blocker merging — Verify that ActionSystem merges blockers from StrategicUpdate correctly..

#### `unit/systems/test_strategy.py`

- [ ] `test_influence_shifts_on_monster_death`: Influence shifts on monster death.
- [ ] `test_influence_shifts_on_hero_death`: Influence shifts on hero death.
- [ ] `test_war_state_transition`: War state transition.
- [ ] `test_conquered_region_triggers_stronghold`: Conquered region triggers stronghold.
- [ ] `test_stronghold_debuff_application`: Stronghold debuff application.

#### `unit/systems/test_strategy_system.py`

- [ ] `test_war_declaration`: War declaration.
- [ ] `test_territory_conquest`: Territory conquest.
- [ ] `test_territory_liberation`: Territory liberation.

### Social / contracts / reputation / lived consequences

#### `ai/test_betrayal_social_consequence.py`

- [x] `test_betrayal_social_consequence`: Betrayal social consequence — Verify that private betrayal trauma prevents recruitment even for reputable founders..

#### `ai/test_learning_social.py`

- [ ] `test_intel_confirmation_by_sight`: Intel confirmation by sight — Verify that seeing a person mentioned in a lead confirms it and boosts trust..
- [ ] `test_intel_refutation_by_exhaustion`: Intel refutation by exhaustion — Verify that failing to find a target refutes the lead and drops trust..

#### `core/test_lived_models.py`

- [ ] `test_routine_profile_instantiation`: Routine profile instantiation — Verify RoutineProfile can be instantiated with hybrid scheduling..
- [ ] `test_place_attachment_instantiation`: Place attachment instantiation — Verify PlaceAttachment can be instantiated and supports sentiment..
- [ ] `test_group_record_instantiation`: Group record instantiation — Verify GroupRecord supports shared tactical intent..
- [ ] `test_entity_integration`: Entity integration — Verify Entity and IdentityAspect absorb new Phase 3 fields..
- [ ] `test_world_state_registry`: World state registry — Verify GroupRegistry integration in WorldState..

#### `integration/gameplay/test_social_meaning.py`

- [x] `test_social_event_betrayal`: Social event betrayal — Verify that hitting an ally triggers a betrayal event and social bond shift..
- [ ] `test_social_event_near_death_and_tp`: Social event near death and tp — Verify that a near-death experience creates a durable turning point..
- [ ] `test_social_event_first_kill_milestone`: Social event first kill milestone — Verify that first kill increments reputation and notoriety..

#### `test_phase_3_social_contracts.py`

- [ ] `test_recruitment_haggling_threshold`: Recruitment haggling threshold — Verify that candidates counter-offer when willingness is close to threshold..
- [x] `test_contract_outcome_consequences`: Contract outcome consequences — Verify that contract resolution returns correct intent updates for all members..
- [x] `test_role_aware_tactical_biases`: Role aware tactical biases — Verify that utility biases change based on contract role..

#### `unit/ai/test_social.py`

- [ ] `test_inn_gossip`: Inn gossip.
- [ ] `test_hero_trading`: Hero trading.

#### `unit/ai/test_social_integration.py`

- [ ] `test_social_bias_on_goal_scoring`: Social bias on goal scoring — Verify that a high-trust bond increases SOCIAL goal score..
- [ ] `test_reputation_impact_on_caution`: Reputation impact on caution — Verify low global reputation triggers defensive posture in cautious entities..

#### `unit/core/gameplay/test_npc_contracts.py`

- [ ] `test_npc_loadout_integrity`: Npc loadout integrity — Verify that specific NPC tiers are assigned their canonical equipment..
- [ ] `test_npc_kind_mapping_integrity`: Npc kind mapping integrity — Verify that race/tier combinations map to the correct semantic kind name..

#### `unit/core/models/test_social_milestones.py`

- [ ] `test_nemesis_milestone_creation`: Nemesis milestone creation.
- [x] `test_memory_salience_retention`: Memory salience retention.

#### `unit/core/models/test_social_registry_updates.py`

- [x] `test_combat_updates_social_registry`: Combat updates social registry.
- [ ] `test_archetype_influence_on_social_deltas`: Archetype influence on social deltas.

#### `unit/strategy/test_social_reasoning_bounding.py`

- [ ] `test_recruitment_offer_bounding_stable`: Recruitment offer bounding stable — Stable entities produce consistent offers without noise..
- [ ] `test_recruitment_offer_bounding_unstable`: Recruitment offer bounding unstable — Unstable entities produce noisy/perturbed offers..

#### `unit/systems/test_familiarity_scaling.py`

- [x] `test_cha_impacts_familiarity_gain`: Cha impacts familiarity gain — Verify that a hero with higher CHA gains familiarity faster..

### Progression / classes / skills / attributes / rewards

#### `unit/ai/test_legend_legacy.py`

- [ ] `test_narrative_memory_logging`: Narrative memory logging.
- [ ] `test_bravery_modifiers`: Bravery modifiers.
- [x] `test_regional_suppression`: Regional suppression.

#### `unit/combat/test_combat_rewards.py`

- [ ] `test_kill_reward_emission_in_apply`: Kill reward emission in apply.
- [ ] `test_no_reward_on_non_lethal_hit`: No reward on non lethal hit.

#### `unit/core/aspects/test_progression.py`

- [x] `test_undead_no_level_up`: Undead no level up — Undead should have a train_rate of 0.0 and never level up..
- [x] `test_milestone_level_up`: Milestone level up — Reaching a milestone like level 5 grants extra stats..
- [ ] `test_veterancy_multipliers`: Veterancy multipliers — Veterancy Ranks should boost stats via StatsProxy..
- [ ] `test_innate_talents_training`: Innate talents training — Talented attributes gain 2x points, weak attributes gain 0.5x..
- [ ] `test_combat_veterancy_points`: Combat veterancy points — Combat yields veterancy points..

#### `unit/core/aspects/test_skill_scaling.py`

- [x] `test_physical_skill_scaling`: Physical skill scaling.
- [x] `test_magical_skill_scaling`: Magical skill scaling.
- [x] `test_elemental_skill_scaling`: Elemental skill scaling.

#### `unit/core/gameplay/test_attribute_synergy.py`

- [ ] `test_luck_impacts_crit_rate_significantly`: Luck impacts crit rate significantly — Verify that Luck has a meaningful impact on critical hit rate..
- [ ] `test_luck_impacts_loot_modifier`: Luck impacts loot modifier — Verify that Luck/Perception provides a loot rarity multiplier..
- [ ] `test_per_based_hidden_discovery`: Per based hidden discovery — Verify that hidden entities are only visible with sufficient Perception..

#### `unit/core/gameplay/test_breakthroughs.py`

- [ ] `test_breakthrough_is_added`: Breakthrough is added.
- [ ] `test_breakthrough_applies_bonus`: Breakthrough applies bonus.

#### `unit/core/gameplay/test_class_gear.py`

- [ ] `test_warrior_prefers_defensive_gear`: Warrior prefers defensive gear — Verify that a Warrior weights defensive stats higher than a Mage..
- [ ] `test_hero_starting_gear_integrity`: Hero starting gear integrity — Verify that each hero class has the correct starting gear defined..

### World / entities / snapshot / determinism / engine authority

#### `core/test_snapshot_integrity.py`

- [x] `test_snapshot_immutability_enforced`: Snapshot immutability enforced.
- [x] `test_snapshot_entities_are_deep_copied`: Snapshot entities are deep copied.
- [x] `test_snapshot_entities_are_frozen`: Snapshot entities are frozen.

#### `integration/engine/test_determinism.py`

- [x] `test_simulation_determinism`: Simulation determinism — Verify that two identical simulations with the same seed produce the same result..
- [x] `test_different_seeds_different_hashes`: Different seeds different hashes — Verify that different seeds produce different world states..

#### `integration/engine/test_mutation_purity.py`

- [ ] `test_aibrain_statelessness`: Aibrain statelessness.

#### `integration/engine/test_snapshot_safety.py`

- [x] `test_entity_deep_copy_isolation`: Entity deep copy isolation — Verify that Entity.copy() provides absolute isolation for nested mutable structures..
- [x] `test_snapshot_actor_isolation`: Snapshot actor isolation — Verify that resolving an actor from a Snapshot ensures mutation safety..
- [ ] `test_aspect_model_rebuild_integrity`: Aspect model rebuild integrity — Ensure that deep copies correctly initialize models and don't lose data..
- [ ] `test_lived_structure_isolation`: Lived structure isolation — Verify isolation for Phase 3 routine and attachment structures..

#### `unit/core/entities/test_entity_serialization.py`

- [ ] `test_entity_to_full_schema_no_crash`: Entity to full schema no crash.
- [ ] `test_entity_to_full_schema_minimal`: Entity to full schema minimal.

#### `unit/core/models/test_snapshot_purity.py`

- [x] `test_simulation_model_collection_freeze_list`: Simulation model collection freeze list — Verify that lists in SimulationModel become immutable after freeze..
- [x] `test_simulation_model_collection_freeze_dict`: Simulation model collection freeze dict — Verify that dicts in SimulationModel become immutable MappingProxy after freeze..
- [x] `test_world_state_freeze_guards`: World state freeze guards — Verify that WorldState prevents mutations after freeze..
- [x] `test_snapshot_deep_purity`: Snapshot deep purity — Verify that Snapshot entities and their nested aspects are recursively frozen..
- [ ] `test_action_proposal_guard_integration`: Action proposal guard integration — Verify the ActionProposalGuard context manager properly freezes the snapshot..

#### `unit/core/test_deep_freeze.py`

- [x] `test_deep_freeze_nested_collections`: Deep freeze nested collections — Verify that freeze() recursively converts nested collections to immutable types..
- [x] `test_deep_freeze_idempotency`: Deep freeze idempotency — Verify that calling freeze() multiple times is safe..

#### `unit/core/test_domain_invariants.py`

- [ ] `test_combat_aspect_invariants`: Combat aspect invariants.
- [ ] `test_progression_aspect_invariants`: Progression aspect invariants.
- [ ] `test_freeze_calls_validate`: Freeze calls validate.
- [ ] `test_nested_freeze_invariants`: Nested freeze invariants.

#### `unit/core/test_invariants.py`

- [x] `test_speed_delay_invariants`: Speed delay invariants — Test that speed_delay never returns NaN or out-of-bounds values..
- [ ] `test_stats_invariants`: Stats invariants — AOA Stabilization: Test CombatAspect invariants (formerly Stats)..
- [x] `test_damage_calc_math`: Damage calc math — Test the core damage calculation logic in isolation..
- [x] `test_recalc_level_consistency`: Recalc level consistency — Ensure level-based stat recalculation remains consistent across aspects..
- [ ] `test_combat_damage_invariants`: Combat damage invariants — Ensure HP reduction application doesn't cause overflow or invalid states..

#### `unit/systems/test_calamity_evolution.py`

- [ ] `test_calamity_evolution`: Calamity evolution.

### Unclassified-but-included RPG-core tests

#### `ai/test_intel_capacity_regression.py`

- [ ] `test_intel_capacity_replay_and_graph_export`: Intel capacity replay and graph export — Verify that cognitive metrics survive replay and graph export pipelines..
- [x] `test_intel_capacity_determinism`: Intel capacity determinism — Verify that identical seeds produce identical cognitive profiles and artifacts..
- [ ] `test_intel_capacity_overload_injection`: Intel capacity overload injection — Inject extreme cognitive pressure and verify overload triggering in artifacts..
- [ ] `test_intel_capacity_divergence_scenario`: Intel capacity divergence scenario — Verify that different attributes lead to differing usage artifacts..
- [x] `test_intel_capacity_detour_depth_hardbound`: Intel capacity detour depth hardbound — Verify that detour depth is capped in artifacts even under pressure..

#### `ai/test_intel_capacity_visibility.py`

- [x] `test_cognition_api_serialization`: Cognition api serialization — Verify that cognitive metrics are correctly serialized for the API..
- [ ] `test_cognition_inspector_rendering`: Cognition inspector rendering — Verify that the CLI inspector correctly renders cognitive data..
- [ ] `test_cognition_empty_profile`: Cognition empty profile — Verify that inspector handles entities without cognitive profiles gracefully..

#### `integration/strategy/test_building_to_strategy_pipeline.py`

- [ ] `test_rng`: Rng.
- [ ] `test_entity`: Entity.
- [ ] `test_guild_intel_to_strategy_visible_pipeline`: Guild intel to strategy visible pipeline — Verify that guild intel produces leads/zones that are visible in API schemas..
- [ ] `test_blacksmith_blocker_resolution_pipeline`: Blacksmith blocker resolution pipeline — Verify that blacksmith constraints produce blockers that are resolved by acquisition..

#### `integration/strategy/test_knowledge_continuity_stabilization.py`

- [ ] `test_milestone_3_lead_testing_and_persistence`: Milestone 3 lead testing and persistence — Verify that exhausted search marks leads as tested and persists them..
- [x] `test_milestone_4_social_filtering`: Milestone 4 social filtering — Verify that social candidate selection filters hostiles and uses debt..
- [ ] `test_strategic_uncertainty_and_anti_cheating`: Strategic uncertainty and anti cheating — Verify that rumors have lower certainty and vague leads don't 'cheat' with perfect coords..

#### `integration/strategy/test_lead_feedback_loops.py`

- [x] `test_source_trust_recalibration`: Source trust recalibration — Verify that a 'False' lead outcome reduces source trust..
- [ ] `test_severe_failure_abandonment_impact`: Severe failure abandonment impact — Verify that a project switch/abandonment reflects in strategic drivers..

#### `integration/strategy/test_strategy_observability_consistency.py`

- [ ] `test_rng`: Rng.
- [ ] `test_entity`: Entity.
- [x] `test_strategy_observability_consistency`: Strategy observability consistency — Verify that a strategic shift is consistently observable across all surfaces..
- [x] `test_strategic_decision_driver_traceability`: Strategic decision driver traceability — Verify that DecisionDriver records flow from AIBrain to the entity state..

#### `movement/test_congestion_milestone_3.py`

- [ ] `test_blocked_retreat_yield`: Blocked retreat yield — Verify high-priority RETREAT ally forces yield from lower-priority ally..
- [ ] `test_oscillation_suppression`: Oscillation suppression — Verify A-B-A-B movement is suppressed after 2 cycles..
- [ ] `test_reroute_hysteresis`: Reroute hysteresis — Verify minor reroutes are ignored to prevent flip-flopping..
- [ ] `test_safe_sidestepping`: Safe sidestepping — Verify yielding entities do not sidestep closer to danger..

#### `unit/ai/strategy/test_recruitment_negotiation.py`

- [ ] `test_recruitment_offer_generation`: Recruitment offer generation — Verify that a recruiter creates a reasonable offer based on greed and risk. [PHASE 4].
- [x] `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend. [PHASE 4].
- [ ] `test_recruitment_haggling_counter_offer`: Recruitment haggling counter offer — Verify greedy candidate counter-offers when the payout is too low. [PHASE 4].
- [ ] `test_recruiter_evaluates_counter`: Recruiter evaluates counter — Verify recruiter accepts a counter-offer for an urgent project. [PHASE 4].

#### `unit/ai/test_action_styles.py`

- [ ] `test_execution_phase_modifies_proposal_with_aggressive_style`: Execution phase modifies proposal with aggressive style.
- [ ] `test_execution_phase_modifies_proposal_with_evasive_style`: Execution phase modifies proposal with evasive style.

#### `unit/ai/test_ai_heuristics.py`

- [ ] `test_ai_boredom_diversification`: Ai boredom diversification — Verify that an entity eventually shifts away from a repetitive goal due to boredom..
- [x] `test_life_stage_priority_shift`: Life stage priority shift — Verify level 1 and level 25 entities have different goal preferences..

#### `unit/ai/test_attention.py`

- [ ] `test_perception_phase_populates_attention_pool`: Perception phase populates attention pool.

#### `unit/ai/test_belief_cycle.py`

- [x] `test_belief_refresh_captures_apparent_state`: Belief refresh captures apparent state.
- [x] `test_belief_decay_lifecycle`: Belief decay lifecycle.
- [x] `test_threat_estimation_logic`: Threat estimation logic.

#### `unit/ai/test_cognitive_pipeline.py`

- [ ] `test_decide_produces_consistent_result`: Decide produces consistent result.
- [ ] `test_decide_increments_idle_ticks_on_rest`: Decide increments idle ticks on rest.
- [ ] `test_perception_phase_appraisal_sync`: Perception phase appraisal sync.

#### `unit/ai/test_combos.py`

- [ ] `test_shatter_combo`: Shatter combo.

#### `unit/ai/test_emotional_memory.py`

- [ ] `test_locational_trauma_triggers_dread`: Locational trauma triggers dread — Verify entering a high-trauma region increments DREAD..
- [x] `test_emotional_bias_on_utility`: Emotional bias on utility — Verify DREAD increases FLEE utility and decreases EXPLORE utility..
- [ ] `test_emotional_decay`: Emotional decay — Verify emotions propose negative delta for decay..

#### `unit/ai/test_emotions.py`

- [ ] `test_appraisal_phase_triggers_panic_on_low_hp`: Appraisal phase triggers panic on low hp.

#### `unit/ai/test_flanking.py`

- [x] `test_flanking_bonus`: Flanking bonus.
- [ ] `test_no_flanking_bonus_when_facing_attacker`: No flanking bonus when facing attacker.

#### `unit/ai/test_flow_fields.py`

- [ ] `test_flow_field_basic_navigation`: Flow field basic navigation.
- [ ] `test_flow_field_respects_terrain_cost`: Flow field respects terrain cost.
- [ ] `test_flow_field_smoothing_normalization`: Flow field smoothing normalization — Verify that get_vector returns a normalized Vector2..
- [ ] `test_flow_field_smoothing`: Flow field smoothing — Verify that get_vector uses neighbor averaging for smoother curves..
- [ ] `test_cache_with_ttl`: Cache with ttl.

#### `unit/ai/test_flow_fields_refinement.py`

- [ ] `test_bilinear_interpolation_basic`: Bilinear interpolation basic.
- [ ] `test_static_target_caching`: Static target caching.
- [ ] `test_moving_target_ttl`: Moving target ttl.

#### `unit/ai/test_narrative_memory.py`

- [x] `test_narrative_memory_trauma_biasing`: Narrative memory trauma biasing.
- [x] `test_narrative_memory_victory_confidence`: Narrative memory victory confidence.
- [ ] `test_region_fatigue_biasing`: Region fatigue biasing.
- [ ] `test_social_appraisal_with_narrative`: Social appraisal with narrative.

#### `unit/ai/test_personality.py`

- [ ] `test_motive_modifier_biases_explore`: Motive modifier biases explore.
- [ ] `test_motive_modifier_biases_rest`: Motive modifier biases rest.
- [ ] `test_motive_modifier_biases_flee`: Motive modifier biases flee.

#### `unit/ai/test_score_modifiers.py`

- [ ] `test_boredom_modifier_applies_multipliers`: Boredom modifier applies multipliers.
- [ ] `test_life_stage_modifier_early_bracket`: Life stage modifier early bracket.
- [ ] `test_goal_evaluator_uses_modifiers`: Goal evaluator uses modifiers.

#### `unit/ai/test_softmax.py`

- [ ] `test_softmax_distribution`: Softmax distribution.
- [ ] `test_softmax_with_equal_scores`: Softmax with equal scores.

#### `unit/ai/test_stuck.py`

- [ ] `test_perception_tracks_position_history`: Perception tracks position history.
- [ ] `test_appraisal_detects_stuck`: Appraisal detects stuck.

#### `unit/combat/test_building_sabotage.py`

- [ ] `test_validate_building_target`: Validate building target.
- [ ] `test_apply_building_sabotage`: Apply building sabotage.

#### `unit/combat/test_combat_building.py`

- [ ] `test_building_sabotage_validation`: Building sabotage validation.
- [ ] `test_building_sabotage_application`: Building sabotage application.

#### `unit/combat/test_consequences.py`

- [ ] `test_wound_infliction_massive_hit`: Wound infliction massive hit — Verify that damage > 25% max HP guarantees a wound..
- [ ] `test_wound_stat_impact`: Wound stat impact — Verify that wounds correctly reduce properties in CombatAspect..
- [ ] `test_scar_permanence`: Scar permanence — Verify that scars are permanent and identifiable..

#### `unit/combat/test_exhaustion.py`

- [ ] `test_stamina_drain_on_attack`: Stamina drain on attack — Verify that a basic attack drains stamina from the actor..
- [ ] `test_exhaustion_penalty_application`: Exhaustion penalty application — Verify that ActionSystem applies fatigue effect when stamina is low..

#### `unit/core/aspects/test_aoa_integrity.py`

- [ ] `test_entity_field_integrity`: Entity field integrity — Ensure Entity model_fields contains only the ID, Kind, and Aspects..
- [ ] `test_entity_property_locking`: Entity property locking — Ensure no forbidden legacy properties have been re-introduced as shims..
- [ ] `test_aspect_model_purity`: Aspect model purity — Ensure aspects themselves stay clean of Cross-Aspect dependencies..
- [ ] `test_mandatory_aspect_naming`: Mandatory aspect naming — Aspects must be named exactly as their type (lowercase)..

#### `unit/core/aspects/test_evolution.py`

- [x] `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap. [AOA REFACTOR].
- [ ] `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment. [AOA REFACTOR].

#### `unit/core/aspects/test_genetics.py`

- [ ] `test_genetic_seed_init`: Genetic seed init.
- [x] `test_training_uses_aptitudes`: Training uses aptitudes.
- [x] `test_aging_and_death`: Aging and death.

#### `unit/core/logic/test_person_logic.py`

- [ ] `test_personality_bias_logic`: Personality bias logic.
- [ ] `test_social_appraisal_logic`: Social appraisal logic.
- [ ] `test_full_motive_pipeline_integration`: Full motive pipeline integration — Verifies that social and personality biases stack correctly..

#### `unit/core/logic/test_routine_service.py`

- [x] `test_routine_service_sleep_bias`: Routine service sleep bias.
- [ ] `test_routine_service_forced_rest_during_off_hours`: Routine service forced rest during off hours.
- [x] `test_routine_service_hunger_bias`: Routine service hunger bias.

#### `unit/core/models/test_phase4_models.py`

- [ ] `test_history_registry_serialization`: History registry serialization.
- [ ] `test_household_record`: Household record.
- [ ] `test_local_scar_record`: Local scar record.
- [ ] `test_region_consequence_record`: Region consequence record.
- [ ] `test_world_state_integration_phase4`: World state integration phase4.

#### `unit/core/models/test_serialization_hardened.py`

- [ ] `test_json_encoder_mapping_proxy`: Json encoder mapping proxy.
- [ ] `test_json_encoder_enum`: Json encoder enum.
- [ ] `test_serialization_pydantic_model`: Serialization pydantic model.
- [ ] `test_serialization_frozen_model_with_proxy`: Serialization frozen model with proxy.
- [ ] `test_serializer_loads`: Serializer loads.

#### `unit/core/test_aoa_coercion.py`

- [ ] `test_vector2_coercion_during_freeze`: Vector2 coercion during freeze — CRITICAL ARCHITECTURAL VERIFICATION: Ensures that if a field expecting a SimulationModel subclass (like Vector2) contains a raw dict (e.g. from serialization drift), the freeze() logic authoritatively coerces it back to the proper object before applying proxies..

#### `unit/core/test_depth_features.py`

- [ ] `test_well_rested_effect_application`: Well rested effect application — Verify that the Well-Rested buff correctly affects Max HP and XP mult..
- [ ] `test_attribute_synergy_xp_mult`: Attribute synergy xp mult — Verify that Wisdom/Intelligence correctly affects XP multiplier..
- [ ] `test_class_weighted_gear`: Class weighted gear — Verify that item power is correctly weighted for different classes..

#### `unit/core/test_eb_isolated.py`

- [ ] `test_eb_stats_scaling`: Eb stats scaling.

#### `unit/core/test_performance_optimizations.py`

- [ ] `test_grid_bytearray_correctness`: Grid bytearray correctness — Verify Grid correctly stores and retrieves materials using bytearray and cache..
- [ ] `test_grid_copy_is_not_shared`: Grid copy is not shared — Verify Grid.copy() duplicates the bytearray data..
- [ ] `test_entity_copy_shallow_vs_refs`: Entity copy shallow vs refs — Verify Entity.copy() is shallow for aspects but produces a new Entity object..
- [ ] `test_ai_worker_batch_processing_logic`: Ai worker batch processing logic — Verify AIWorkerDaemon correctly handles a batch of tasks..

#### `unit/systems/test_action_convergence.py`

- [ ] `test_loot_no_duplication`: Loot no duplication — Verify that items picked up by the system are not duplicated by AI updates..
- [ ] `test_corpse_loot_convergence`: Corpse loot convergence — Verify that corpse recovery is authoritatively handled by ActionSystem..

#### `unit/systems/test_dynamic_quests.py`

- [x] `test_dynamic_liberate_quest`: Dynamic liberate quest.
- [ ] `test_history_logging`: History logging.

#### `unit/systems/test_evolution.py`

- [x] `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap..
- [ ] `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment..

#### `unit/systems/test_personality_ai.py`

- [ ] `test_grudge_accumulation`: Grudge accumulation.
- [ ] `test_should_flee_logic`: Should flee logic.
- [ ] `test_locational_memory_on_death`: Locational memory on death.
- [ ] `test_frontier_locational_penalty`: Frontier locational penalty.

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
- `src_v2` evidence
- divergence note
- proof path

---

# A. CLI and entrypoint compatibility

Relevant original source/test evidence:

- `src/__main__.py`
- `tests/e2e/test_logging_structure.py`

### CLI mode and parser contract

- [x] `python -m src` defaults to server mode when no subcommand is provided.
- [x] `python -m src serve` accepts the original `--host`, `--port`, `--seed`, `--entities`, `--workers`, `--log-level` arguments.
- [x] `python -m src cli` accepts the original `--ticks`, `--entities`, `--seed`, `--workers`, `--grid-width`, `--grid-height`, `--replay`, `--log-level` arguments.
- [x] `python -m src inspect` accepts the original `--id`, `--seed`, `--ticks`, `--entities`, `--workers`, `--log-level` arguments.
- [x] CLI argument defaults remain compatible with legacy expectations.
- [x] Invalid CLI arguments fail in a controlled, parser-driven way.
- [x] CLI replay-file argument writes to the expected output path semantics.
- [ ] CLI mode still initializes the same baseline world-building flow (town, sanctuary, camps, hero spawn, goblin spawn) under equivalent config.

### CLI environment boot behavior

- [ ] CLI mode forces broker-disabled behavior through environment setup when not already set.
- [ ] CLI startup still loads registries before simulation loop startup.
- [x] CLI startup still wires logging before engine loop execution.
- [x] CLI shutdown still tears down worker infrastructure cleanly after simulation.

---

# B. Optional-broker disabled-mode compatibility

Relevant original source/test evidence:

- `tests/api/test_broker_isolation.py`
- `tests/integration/infra/test_brokerless_import.py`

### RabbitMQ disabled-mode behavior

- [x] `DISABLE_RABBITMQ=1` causes RabbitMQ client code to enter explicit disabled mode.
- [x] RabbitMQ client imports do not crash when disabled.
- [ ] RabbitMQ public accessors return safe no-op values (`None`) when disabled.
- [x] RabbitMQ disabled-mode behavior remains safe even when broker libraries are missing.

### Kafka disabled-mode behavior

- [x] `DISABLE_KAFKA=1` causes Kafka client code to enter explicit disabled mode.
- [x] Kafka client imports do not crash when disabled.
- [ ] Kafka public accessors return safe no-op values (`None`) when disabled.
- [ ] Kafka disabled-mode behavior remains safe even when broker libraries are missing.

### Redis disabled / missing-package behavior

- [ ] Redis client behavior remains safe when Redis package or runtime is unavailable.
- [ ] Redis accessors fail safely without crashing simulation bootstrap when Redis is optional.

### Disabled-mode import isolation

- [x] Headless runner imports still succeed when optional brokers are disabled.
- [ ] Action-system imports still succeed when optional brokers are disabled.
- [x] Import-time behavior does not accidentally force broker setup.

---

# C. Worker-pool and infrastructure fallback behavior

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_infrastructure_isolation.py`
- worker-pool usage in original CLI and loop wiring

### Worker fallback semantics

- [x] Worker pool falls back to inline/local execution when broker transport is unavailable.
- [x] Worker pool does not require live RabbitMQ/Kafka to execute local simulation behavior.
- [ ] Worker fallback preserves authoritative action generation semantics.
- [x] Worker fallback preserves deterministic ordering expectations in local mode.
- [x] Worker shutdown remains safe after fallback execution paths.
- [x] Missing broker infrastructure does not block minimal simulation startup.

### Import/runtime isolation

- [ ] Infrastructure module isolation prevents optional dependencies from contaminating normal simulation imports.
- [ ] Runtime paths that do not require brokers do not import or initialize them accidentally.
- [ ] Fallback behavior is exercised by real tests, not only by mocks or assumptions.

---

# D. Chaos mode and infrastructure resilience

Relevant original source/test evidence:

- `tests/integration/infrastructure/test_chaos.py`

### Chaos resilience

- [ ] Chaos-enabled runs survive AI-result drop conditions without immediate simulation failure.
- [ ] Chaos-enabled runs continue ticking through configured chaos-drop scenarios.
- [ ] Chaos does not corrupt authoritative world state shape.
- [ ] Chaos does not break snapshot acquisition.

### Chaos determinism

- [ ] Given identical seed and identical chaos configuration, repeated chaos-mode runs remain deterministic.
- [ ] Chaos-mode determinism is verified by repeated world-state fingerprint comparison.
- [ ] Chaos-enabled infrastructure does not introduce hidden non-determinism into equivalent runs.

---

# E. Replay compatibility outside pure RPG-core semantics

Relevant original source/test evidence:

- replay usage in `src/__main__.py`
- replay-related explainability / determinism / regression tests
- `tests/e2e/test_deterministic_replay.py`

### Replay output contract

- [x] Replay files are written in the expected legacy location/format semantics for headless runs.
- [x] Replay snapshots preserve deterministic entity ordering and field availability where legacy tests rely on them.
- [ ] Replay preserves enough world-state detail to support legacy fingerprinting and regression assertions.
- [x] Replay can support structural comparison between repeated runs with same seed.
- [ ] Replay remains aligned with other truth surfaces where legacy tests expect parity.

### End-to-end deterministic replay path

- [x] Same seed and equivalent configuration produce identical replay-visible state across runs.
- [x] Different seeds produce divergent replay-visible state.
- [ ] Replay includes ground-item state where legacy determinism tests inspect it.
- [ ] Replay includes enough actor combat/progression/mind state for state-fingerprint checks.

---

# F. Structured logging compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py`
- original logging setup and JSON formatter usage in source

### Logging format contract

- [x] CLI stdout logs remain valid JSON line-by-line.
- [ ] Each emitted structured log includes mandatory fields:
  - [x] `timestamp`
  - [x] `level`
  - [x] `message`
  - [x] `component`
- [x] Log output remains machine-parseable under normal CLI execution.

### Logging context injection

- [x] World-loop logs include tick context.
- [x] World-loop logs preserve identifiable component naming.
- [x] Worker-pool logs preserve identifiable component naming where emitted.
- [x] Main entrypoint logs preserve identifiable `__main__` or equivalent component identity.
- [ ] Structured logging remains compatible with legacy context-injection expectations.

---

# G. Metrics and monitoring compatibility

Relevant original source/test evidence:

- `tests/e2e/test_logging_structure.py` (Prometheus check)
- original metrics/logging stack wiring in source

### Prometheus / telemetry compatibility

- [ ] Simulation metrics remain scrapeable by Prometheus in equivalent stack configurations.
- [ ] Legacy-queried metric names remain available where replacement claims require them.
- [ ] Tick-duration metrics remain emitted under the expected metric contract.
- [ ] Monitoring stack checks do not silently pass with empty data.

### Operational observability

- [ ] Engine-side metrics remain available without forcing gameplay divergence.
- [x] Metrics do not rely on broker-only paths if local/headless execution is supposed to work without brokers.
- [ ] Monitoring compatibility is verified under realistic stack conditions, not just unit stubs.

---

# H. API protocol and transport compatibility

Relevant original source/test evidence:

- API metadata tests
- websocket handshake tests
- gzip compression test

### Metadata endpoints

- [ ] Protocol metadata endpoint remains available at the expected route.
- [ ] Metadata response still includes entity key mapping where legacy consumers expect it.
- [ ] Metadata response still includes state enum mapping where legacy consumers expect it.
- [ ] Protocol metadata field order/meaning remains compatible where clients depend on it.

### WebSocket protocol behavior

- [ ] WebSocket endpoint still supports legacy handshake semantics.
- [ ] JSON handshake mode remains supported.
- [x] MessagePack handshake mode remains supported.
- [ ] Initial post-handshake payload remains structurally compatible with legacy client expectations.
- [ ] Tick/entity/event payload shape remains compatible where explicitly defined by legacy tests.

### Compression behavior

- [x] GZip middleware or equivalent response compression remains functional for large metadata responses.
- [x] Compression support does not break standard metadata endpoint access.

---

# I. Headless runner / final-system execution compatibility

Relevant original source/test evidence:

- headless runner import/use tests
- deterministic replay tests
- brokerless import tests
- cognition/replay consistency regression tests

### Headless execution path

- [ ] A minimal production-like headless run can still execute without optional brokers when disabled.
- [ ] Headless run still produces the expected result artifacts (at minimum replay, and where applicable manifest/graph outputs).
- [ ] Headless runner import remains isolated from optional broker setup.
- [ ] Final-system path remains suitable for regression use rather than demo-only use.

### Artifact consistency

- [ ] Final-system artifacts remain mutually consistent where legacy tests compare them.
- [ ] Structural graph/export surfaces remain aligned with replay where legacy tests require parity.
- [ ] Artifact generation failure paths remain visible rather than silently swallowed.

---

# J. Infrastructure-side “unhappy path” compatibility actually evidenced in legacy tests

Only include source-grounded unhappy paths.

### Disabled/missing dependency paths

- [ ] Missing RabbitMQ package with disabled flag does not crash import.
- [ ] Missing Kafka package with disabled flag does not crash import.
- [ ] Missing Redis package does not crash safe initialization paths where optional.
- [x] Missing broker dependencies do not block headless runner imports.

### Runtime degradation paths

- [ ] Worker transport degradation falls back safely to local execution.
- [ ] Chaos-mode packet/result drop does not terminate the simulation prematurely under supported settings.
- [ ] Monitoring checks fail loudly when expected data is missing.

### CLI/runtime robustness

- [ ] CLI execution still emits structured logs under minimal simulation runs.
- [ ] Short runs still produce enough output for regression inspection.
- [ ] Minimal runs do not require full external stack unless explicitly in E2E stack mode.

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
- `src_v2` evidence
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

- [ ] `test_perception_phase_populates_attention_pool`: attention pool population
- [x] `test_belief_refresh_captures_apparent_state`: belief refresh from apparent state
- [x] `test_belief_decay_lifecycle`: belief decay lifecycle
- [ ] `test_belief_conflict_resolution`: belief conflict handling
- [ ] `test_belief_sharing_propagation`: belief sharing propagation
- [x] `test_threat_estimation_logic`: threat estimation logic
- [ ] `test_perception_phase_appraisal_sync`: appraisal sync
- [ ] `test_perception_tracks_position_history`: position-history tracking
- [ ] `test_appraisal_phase_triggers_panic_on_low_hp`: panic trigger via appraisal
- [ ] `test_appraisal_detects_stuck`: stuck appraisal detection
- [ ] `test_social_appraisal_logic`: social appraisal logic
- [ ] `test_social_appraisal_with_narrative`: narrative-informed social appraisal

---

## B. Routine / motive / biological needs / life rhythm

Relevant original source/test evidence:

- `RoutineService`
- `ObjectiveDerivationService`
- `tests/unit/ai/test_routine.py`
- related rest/sleep/hunger tests in `all_test.py`

- [x] `test_sleep_goal_utility_at_night`: sleep utility at night
- [ ] `test_rest_to_sleep_transition`: rest-to-sleep transition
- [x] `test_routine_service_sleep_bias`: sleep bias
- [ ] `test_routine_service_forced_rest_during_off_hours`: forced off-hours rest
- [x] `test_routine_service_hunger_bias`: hunger bias
- [ ] `test_home_visit_leads_to_eating`: eating behavior from routine/home visit
- [x] `test_inn_visit_leads_to_sleeping`: inn visit leads to sleeping
- [ ] `test_biological_decay_and_forced_sleep`: biological decay and forced sleep
- [x] `test_sleeping_recovery_cycle`: sleeping recovery cycle
- [ ] `test_hunger_reduces_stability`: hunger consequence
- [ ] `test_routine_goal_priority`: routine goal priority
- [ ] `test_routine_disruption_panic`: disruption panic
- [ ] `test_attack_disruption_suppresses_routines`: attack suppresses routine
- [ ] `test_routine_priority_archetype_bias`: archetype-based routine bias
- [ ] `test_life_stage_priority_shift`: life-stage priority shift

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

- [ ] `test_ai_boredom_diversification`: boredom diversification effect
- [ ] `test_boredom_modifier_applies_multipliers`: boredom modifier law
- [ ] `test_life_stage_modifier_early_bracket`: life-stage modifier law
- [ ] `test_motive_modifier_biases_explore`: motive modifier explore bias
- [ ] `test_motive_modifier_biases_rest`: motive modifier rest bias
- [ ] `test_motive_modifier_biases_flee`: motive modifier flee bias
- [ ] `test_goal_evaluator_uses_modifiers`: goal evaluator modifier integration
- [ ] `test_softmax_distribution`: score-to-choice distribution
- [ ] `test_softmax_with_equal_scores`: equal-score handling

---

## D. Emotional / narrative memory / trauma logic

Relevant original source/test evidence:

- `MemorySalienceService`
- `EventInterpreterService`
- `tests/unit/ai/test_emotional_memory.py`
- `tests/unit/ai/test_narrative_memory.py`

- [ ] `test_locational_trauma_triggers_dread`: locational trauma -> dread
- [x] `test_emotional_bias_on_utility`: emotion changes utility
- [ ] `test_emotional_decay`: emotional decay
- [x] `test_narrative_memory_trauma_biasing`: trauma memory biasing
- [x] `test_narrative_memory_victory_confidence`: victory-confidence memory
- [ ] `test_narrative_memory_logging`: narrative memory logging
- [ ] `test_social_appraisal_with_narrative`: narrative-informed social appraisal
- [ ] `test_bravery_modifiers`: bravery modifiers

---

## E. Combat aftermath / wounds / scars / stamina / exhaustion

Relevant original source/test evidence:

- `DamageResolutionService`
- `CombatAftermathService`
- `tests/unit/combat/**`
- related stamina tests in `all_test.py`

- [ ] `test_wound_infliction_massive_hit`: wound infliction
- [ ] `test_wound_stat_impact`: wound stat penalties
- [ ] `test_scar_permanence`: scar permanence
- [ ] `test_scar_decay`: scar decay behavior if preserved
- [ ] `test_local_scar_record`: local scar record
- [x] `test_scar_detection`: scar detection
- [ ] `test_ai_perception_of_scars`: perception of scars
- [ ] `test_stamina_drain_on_attack`: stamina drain on attack
- [ ] `test_stamina_decreases_on_move`: stamina drain on move
- [ ] `test_stamina_decreases_on_harvest`: stamina drain on harvest
- [ ] `test_skill_use_costs_stamina`: stamina cost on skill use
- [ ] `test_stamina_regen_resting`: rest stamina regen
- [ ] `test_stamina_regen_active`: active regen
- [ ] `test_stamina_regen_capped`: regen cap
- [ ] `test_exhaustion_penalty_application`: exhaustion penalty
- [ ] `test_best_ready_skill_skips_insufficient_stamina`: skill gating by stamina

---

## F. Tactical specialty / action style / combo behavior

Relevant original source/test evidence:

- combat/tactical logic in `all_src.py`
- `tests/unit/ai/test_action_styles.py`
- `tests/unit/ai/test_flanking.py`
- `tests/unit/ai/test_combos.py`

- [ ] `test_execution_phase_modifies_proposal_with_aggressive_style`: aggressive action style
- [ ] `test_execution_phase_modifies_proposal_with_evasive_style`: evasive action style
- [x] `test_flanking_bonus`: flanking bonus
- [ ] `test_no_flanking_bonus_when_facing_attacker`: facing-sensitive flanking exclusion
- [ ] `test_shatter_combo`: combo behavior
- [ ] `test_ranged_hero_kites_when_adjacent`: ranged kiting
- [ ] `test_ranged_skirmisher_kites_when_close`: ranged skirmish spacing

---

## G. Loot / hidden discovery / local reward realism

Relevant original source/test evidence:

- loot and discovery logic in `all_src.py`
- related tests in `all_test.py`

- [ ] `test_luck_impacts_loot_modifier`: loot modifier from luck/perception
- [ ] `test_per_based_hidden_discovery`: hidden discovery from perception
- [ ] `test_loot_recovery_consistency`: loot recovery consistency
- [ ] `test_loot_no_duplication`: no duplicated loot
- [ ] `test_corpse_loot_convergence`: corpse loot convergence
- [ ] `test_loot_and_respawn`: loot and respawn interaction
- [ ] `test_loot_tables_exist`: loot table integrity
- [ ] `test_full_bag_aborts_looting`: abort looting when full
- [ ] `test_overweight_aborts_looting`: abort looting when overweight
- [ ] `test_near_weight_limit_penalizes_loot`: weight-limit penalty on looting

---

## H. Region-scale strategic and world consequences

Relevant original source/test evidence:

- `StrategicConsequenceService`
- `WorldConsequenceInterpretationService`
- region/world consequence tests in `all_test.py`

- [x] `test_regional_suppression`: regional suppression
- [x] `test_strategic_pivot_on_regional_danger`: pivot on regional danger
- [ ] `test_region_fatigue_biasing`: region fatigue biasing
- [ ] `test_region_consequence_record`: region consequence record
- [ ] `test_conquered_region_triggers_stronghold`: conquered region -> stronghold consequence
- [ ] `test_strategic_pipeline_home_threat`: home threat in strategic pipeline
- [ ] `test_world_consequence_*`: world consequence interpretation coverage where applicable

---

## I. Death / permadeath / succession / heirlooms / nemesis

Relevant original source/test evidence:

- lifecycle / death / social-consequence logic in `all_src.py`
- related tests in `all_test.py`

- [x] `test_aging_and_death`: aging and death
- [ ] `test_hero_lifecycle_system_permadeath`: hero permadeath
- [ ] `test_permadeath_succession_and_heirlooms`: succession and heirlooms
- [ ] `test_hero_death_creates_scar`: death scar consequences
- [x] `test_near_death_triggers_survival_consequences`: near-death survival consequences
- [x] `test_near_death_hardening`: near-death hardening
- [ ] `test_nemesis_recognition_and_fear_bias`: nemesis recognition and fear bias
- [ ] `test_nemesis_milestone_creation`: nemesis milestone creation
- [ ] `test_locational_memory_on_death`: locational memory on death
- [ ] `test_influence_shifts_on_monster_death`: influence shift on monster death
- [ ] `test_influence_shifts_on_hero_death`: influence shift on hero death

---

## J. Medical / diagnosis judgment logic

Relevant original source/test evidence:

- diagnosis logic in `all_src.py`
- related tests in `all_test.py`

- [ ] `test_accurate_diagnosis_high_wisdom`: accurate diagnosis at high wisdom
- [ ] `test_misdiagnosis_low_wisdom`: misdiagnosis at low wisdom

# Legacy `src` RPG-Core Checklist — Part 7 (Residual Test-Covered Logic)

This checklist is additive to Parts 1–6.

It exists to capture smaller but still real legacy logic families that are explicitly covered by tests and are easy to lose if they remain implicit under broad labels like strategy, progression, or world behavior.

This part should stay test-first. If a behavior is listed here, it should have an identifiable test anchor in the original legacy test surface.

---

## A. Quest lifecycle, generation, and completion logic

Relevant legacy test surface includes quest creation, progression, duplicate suppression, completion, rewards, and quest-type-specific behavior.

- [ ] `test_quest_creation`: quest creation baseline
- [ ] `test_quest_advance`: quest progression increments correctly
- [ ] `test_quest_advance_does_nothing_when_completed`: completed quests do not advance further
- [ ] `test_quest_progress_ratio`: progress-ratio computation is correct
- [ ] `test_generate_quest_returns_quest`: quest generator returns valid quest object
- [x] `test_generate_quest_respects_level`: generated quests respect level banding
- [ ] `test_generate_quest_skips_duplicate`: duplicate quest generation is suppressed
- [x] `test_generate_quest_gold_scales_with_level`: quest gold reward scales with level
- [ ] `test_generate_explore_quest`: explore-quest generation works
- [ ] `test_hunt_quest_completion_awards_rewards`: hunt-quest completion awards rewards
- [ ] `test_explore_quest_completes_near_target`: explore-quest completes near target
- [ ] `test_gather_quest_advance`: gather-quest progression works
- [x] `test_dynamic_liberate_quest`: liberate-quest generation/progression works
- [ ] `test_territory_conquest`: territory-conquest quest/world objective behavior is preserved

---

## B. Trait system logic

Relevant legacy test surface includes trait definitions, trait assignment, trait aggregation, compatibility, and serialization.

- [ ] `test_trait_serialization`: trait serialization is preserved
- [ ] `test_get_traits`: trait retrieval works
- [ ] `test_trait_defs_not_empty`: trait definitions exist and are non-empty
- [ ] `test_with_traits_assigns_traits`: explicit trait assignment works
- [ ] `test_no_traits_by_default`: no-trait default behavior is preserved
- [ ] `test_traits_with_different_race_prefix`: race-prefixed trait handling is preserved
- [ ] `test_empty_traits_returns_zero_bonus`: empty-trait bonus behavior is preserved
- [ ] `test_single_known_trait`: single-trait bonus behavior is preserved
- [ ] `test_multiple_traits_sum`: multiple traits stack/sum correctly
- [ ] `test_unknown_trait_id_ignored`: unknown traits are ignored safely
- [ ] `test_same_trait_compatible`: trait compatibility logic is preserved
- [ ] `test_assigns_between_2_and_4_traits`: random/default trait assignment count is preserved
- [ ] `test_all_assigned_traits_are_valid`: assigned traits are always valid
- [ ] `test_all_trait_types_have_definitions`: all trait types have definitions
- [ ] `test_trait_defs_have_all_utility_fields`: trait utility fields are complete
- [ ] `test_trait_defs_have_all_stat_fields`: trait stat fields are complete

---

## C. Role derivation and role-aware behavior

Relevant legacy test surface includes role derivation, role transition, role biasing, and tactical role-awareness.

- [ ] `test_initial_role_derivation`: initial role derivation is preserved
- [ ] `test_dynamic_role_transition_with_hysteresis`: dynamic role transition with hysteresis is preserved
- [x] `test_role_bias_influence`: role bias affects decisions as expected
- [x] `test_role_aware_tactical_biases`: tactical behavior reflects role-aware biasing

---

## D. Aptitudes, training-detail law, and stat recomputation

Relevant legacy test surface includes aptitude-driven training, soft caps, fractional accumulation, and recomputation of derived stats.

- [x] `test_training_uses_aptitudes`: aptitude-weighted training law is preserved
- [ ] `test_innate_talents_training`: innate talents affect training as expected
- [ ] `test_training_does_not_exceed_cap`: training respects hard caps
- [ ] `test_training_accumulates_fractionally`: fractional training accumulation is preserved
- [ ] `test_training_updates_stats_on_increment`: stat update on training increment is preserved
- [ ] `test_specialized_training_soft_caps`: soft-cap behavior for specialized training is preserved
- [ ] `test_output_derived_stat_ceilings`: derived-stat ceiling logic is preserved
- [ ] `test_stat_recalculation`: stat recomputation behavior is preserved
- [ ] `test_attribute_scaling_overlap`: overlapping attribute-scaling law is preserved

---

## E. Place attachment, home, and anchored behavior

Relevant legacy test surface includes place attachment, home behavior, home storage, retreat-to-home behavior, and home-driven actions.

- [ ] `test_place_attachment_instantiation`: place attachment can be instantiated
- [ ] `test_place_attachment_navigation`: place attachment influences navigation correctly
- [ ] `test_place_attachment_home_navigation`: home-oriented navigation behavior is preserved
- [ ] `test_no_home_returns_false`: no-home logic is preserved
- [ ] `test_home_sets_home_pos`: home position assignment is preserved
- [ ] `test_entity_copy_includes_home_storage`: home storage is preserved during copy
- [ ] `test_entity_without_home_storage`: no-home-storage case is preserved
- [ ] `test_divergent_home_response`: divergent home response behavior is explicit and preserved where intended
- [ ] `test_home_priority_retreat`: home-priority retreat behavior is preserved
- [ ] `test_visit_home_upgrade_resolution`: visit-home upgrade resolution is preserved
- [ ] `test_home_visit_leads_to_eating`: home visit can lead to eating behavior

---

## F. Leash, camp, and local anchored ecology

Relevant legacy test surface includes leash behavior, chase abandonment, camp return, and camp reinforcement logic.

- [ ] `test_no_leash_returns_false`: no-leash detection behavior is preserved
- [ ] `test_mob_beyond_leash_returns_to_camp`: beyond-leash return-to-camp behavior is preserved
- [ ] `test_mob_within_leash_wanders_normally`: within-leash wandering behavior is preserved
- [ ] `test_no_leash_mob_wanders_freely`: leash-free wandering behavior is preserved
- [ ] `test_chase_beyond_leash_abandons`: chase abandonment beyond leash is preserved
- [ ] `test_chase_within_leash_continues`: chase continuation within leash is preserved
- [ ] `test_no_leash_mob_hunts_freely`: no-leash hunting freedom is preserved
- [ ] `test_camp_reinforcements`: camp reinforcement behavior is preserved

---

## G. Travel topology, path-affordance, and regional traversal law

Relevant legacy test surface includes flow fields, terrain costs, roads, bridges, biome affordances, and difficulty-zone traversal constraints.

- [ ] `test_flow_field_basic_navigation`: basic flow-field navigation is preserved
- [ ] `test_flow_field_respects_terrain_cost`: terrain-cost-sensitive navigation is preserved
- [ ] `test_flow_field_smoothing`: flow-field smoothing is preserved
- [ ] `test_flow_field_smoothing_normalization`: smoothing normalization behavior is preserved
- [ ] `test_navigation_uses_flow_field_for_far_town`: far-town navigation uses flow fields
- [ ] `test_navigation_uses_flow_field_for_world_boss`: world-boss navigation uses flow fields
- [ ] `test_road_cost_is_low`: road traversal cost law is preserved
- [ ] `test_prefers_road_over_swamp`: road preference over swamp is preserved
- [ ] `test_each_biome_has_road_network`: biome road-network presence is preserved
- [ ] `test_road_connects_locations`: road connectivity behavior is preserved
- [ ] `test_bridges_placed_over_water`: bridge placement over water is preserved
- [ ] `test_all_four_biomes_have_features`: biome feature presence is preserved
- [x] `test_difficulty_sets_level_range`: region difficulty sets level range correctly
- [ ] `test_gold_scales_with_difficulty`: difficulty-linked gold scaling is preserved
- [ ] `test_in_region_returns_difficulty`: region difficulty query logic is preserved
- [ ] `test_difficulty_zones_defined`: difficulty-zone definition is preserved
- [ ] `test_lava_only_at_high_difficulty`: lava/high-difficulty coupling is preserved
- [ ] `test_all_terrains_have_names`: terrain naming coverage is preserved
- [ ] `test_all_terrains_have_race_labels`: terrain race-label coverage is preserved

---

## H. Cooperation, recruitment-adjacent coordination, and proximity bonding

Relevant legacy test surface includes small cooperative and bonding behaviors that affect social or local-world outcomes.

- [ ] `test_cooperation_recruitment_logic`: cooperation in recruitment/social choice is preserved
- [ ] `test_scenario_3_stationary_world_proximity_bonding`: proximity bonding behavior is preserved

---

## I. Residual small-world and economy-adjacent local realism

Relevant legacy test surface includes local inventory and burden realism that can affect action outcomes.

- [ ] `test_full_bag_aborts_looting`: full-bag looting abort is preserved
- [ ] `test_overweight_aborts_looting`: overweight looting abort is preserved
- [ ] `test_near_weight_limit_penalizes_loot`: near-limit loot penalty is preserved

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

- [ ] No Part 7 item should be left implicit under a generic bucket like “AI improvements” or “progression tuning`

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

- [ ] `test_default_values`: default entity/build values are preserved
- [ ] `test_default_values_all_zero`: default zero-valued state is preserved
- [ ] `test_default_multiplicative_values_are_1`: default multiplicative modifiers equal 1
- [ ] `test_default_additive_values_are_0`: default additive modifiers equal 0
- [ ] `test_default_metadata_is_none`: metadata defaults to `None`
- [ ] `test_none_metadata_preserved`: `None` metadata remains preserved
- [ ] `test_schema_none_metadata`: schema handles `None` metadata correctly
- [ ] `test_no_skills_by_default`: entities have no skills by default
- [ ] `test_no_inventory_by_default`: entities have no inventory by default
- [ ] `test_no_traits_by_default`: entities have no traits by default
- [ ] `test_entity_starts_with_no_quests`: entities start with no quests
- [ ] `test_default_core_rate_is_1`: default core subsystem rate is preserved
- [ ] `test_default_environment_rate_is_2`: default environment subsystem rate is preserved
- [ ] `test_default_economy_rate_is_5`: default economy subsystem rate is preserved
- [ ] `test_default_region_id`: default region identifier is preserved
- [ ] `test_default_empty`: default empty collection/container semantics are preserved
- [ ] `test_empty_zones_returns_1`: empty-zone fallback behavior is preserved
- [ ] `test_empty_regions_returns_none`: empty-region lookup returns `None`
- [ ] `test_select_returns_none_on_empty`: selection on empty inputs returns `None`
- [x] `test_export_empty_strategy`: exporting empty strategy state is safe

---

## B. No-op, empty-tick, and “does nothing safely” assumptions

These tests assert that when there is nothing to do, the system degrades safely and predictably.

- [ ] `test_no_changes_skipped`: no-change updates are skipped safely
- [ ] `test_effects_tick_on_empty_tick`: effects still tick on empty ticks
- [ ] `test_stamina_regens_on_empty_tick`: stamina regen still occurs on empty ticks
- [ ] `test_skill_cooldowns_tick_on_empty_tick`: skill cooldowns still tick on empty ticks
- [ ] `test_quest_advance_does_nothing_when_completed`: completed quests ignore further advance calls
- [ ] `test_unknown_action_does_nothing`: unknown actions are safely ignored
- [ ] `test_full_hp_no_change`: full-HP state remains unchanged
- [ ] `test_no_region_no_penalty`: no-region case applies no penalty
- [ ] `test_safe_region_no_penalty`: safe-region case applies no penalty
- [ ] `test_unknown_region_returns_0`: unknown region uses zero/fallback difficulty
- [ ] `test_no_region_returns_0`: no-region difficulty fallback is preserved

---

## C. Copy, clone, preservation, and ownership assumptions

These tests assert what is supposed to be preserved across copying and what must not be shared.

- [ ] `test_quest_copy`: quest copy preserves quest state
- [ ] `test_entity_copy_preserves_quests`: entity copy preserves quests
- [ ] `test_entity_copy_preserves_attributes`: entity copy preserves attributes
- [ ] `test_entity_copy_preserves_skills`: entity copy preserves skills
- [ ] `test_entity_copy_includes_home_storage`: entity copy preserves home storage
- [ ] `test_entity_without_home_storage`: no-home-storage case remains safe
- [ ] `test_region_copy`: region copy semantics are preserved
- [ ] `test_attributes_copy`: attribute copy semantics are preserved
- [ ] `test_copy`: generic model copy semantics are preserved wherever tested
- [ ] `test_grid_copy_is_not_shared`: copied grids are not aliased
- [ ] `test_entity_copy_shallow_vs_refs`: copy/ref-sharing behavior is explicit and preserved
- [ ] `test_latest_preserves_metadata`: latest-version object preserves metadata

---

## D. Serialization, schema, and round-trip assumptions

These tests assert that important models are supposed to serialize safely and consistently.

- [ ] `test_serialization_round_trip`: serialization round-trip is preserved
- [ ] `test_item_serialization`: item serialization is preserved
- [ ] `test_enchanted_blade_serialization`: enchanted item serialization is preserved
- [ ] `test_skill_serialization`: skill serialization is preserved
- [ ] `test_passive_skill_serialization`: passive skill serialization is preserved
- [ ] `test_class_serialization`: class serialization is preserved
- [ ] `test_breakthrough_serialization`: breakthrough serialization is preserved
- [ ] `test_trait_serialization`: trait serialization is preserved
- [ ] `test_history_registry_serialization`: history registry serialization is preserved
- [ ] `test_entity_to_full_schema_no_crash`: full schema export does not crash
- [ ] `test_serialization_pydantic_model`: pydantic serialization assumption is preserved
- [ ] `test_serialization_frozen_model_with_proxy`: frozen/proxy serialization is preserved
- [ ] `test_inspection_serialization`: inspection serialization is preserved
- [x] `test_cognition_api_serialization`: cognition API serialization is preserved

---

## E. Freeze, immutability, and deep-isolation assumptions

These tests assert that certain state surfaces are supposed to be frozen, safe, and non-mutating.

- [x] `test_entity_deep_copy_isolation`: deep-copy isolation is preserved
- [x] `test_deep_freeze_nested_collections`: deep freeze handles nested collections
- [x] `test_deep_freeze_idempotency`: deep freeze is idempotent
- [ ] `test_freeze_calls_validate`: freeze triggers validation correctly
- [ ] `test_nested_freeze_invariants`: nested freeze invariants are preserved
- [x] `test_world_state_freeze_guards`: world-state freeze guards are preserved
- [x] `test_simulation_model_collection_freeze_list`: list freezing behavior is preserved
- [x] `test_simulation_model_collection_freeze_dict`: dict freezing behavior is preserved
- [ ] `test_vector2_coercion_during_freeze`: vector coercion during freeze is preserved
- [x] `test_non_mutation`: non-mutation guarantee is preserved
- [ ] `test_build_profile_does_not_mutate_caps`: cognition-profile derivation is non-mutating
- [ ] `test_build_profile_returns_new_profile_object_each_call`: fresh profile object guarantee is preserved

---

## F. Determinism and repeatability assumptions

These tests assert that the system is supposed to be repeatable under the same conditions.

- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: deterministic profile derivation
- [x] `test_intel_capacity_determinism`: intelligence-capacity determinism is preserved
- [ ] `test_strategic_replay_graph_equality`: replay graph equality is preserved
- [ ] `test_same_seed_same_result`: same-seed world/result determinism is preserved
- [ ] `test_harness_non_determinism_different_seed`: different-seed divergence remains explicit
- [ ] `test_first_by_id_wins_same_tile`: deterministic same-tile tie-breaking is preserved
- [ ] `test_diagonal_same_target_one_wins`: deterministic same-target conflict resolution is preserved
- [ ] `test_non_conflicting_moves_both_succeed`: independent valid moves both survive
- [ ] `test_equidistant_returns_first`: deterministic first-choice behavior on ties is preserved

---

## G. Registry, definition, and data-completeness assumptions

These tests assert that key registries and definition maps are supposed to exist and be complete.

- [ ] `test_item_registry_not_empty`: item registry is non-empty
- [ ] `test_skill_defs_not_empty`: skill definitions are non-empty
- [ ] `test_trait_defs_not_empty`: trait definitions are non-empty
- [ ] `test_registry_not_empty`: generic registry non-empty guarantee is preserved
- [ ] `test_skill_registry_not_empty`: skill registry is non-empty
- [ ] `test_all_trait_types_have_definitions`: all trait types have definitions
- [ ] `test_all_tiers_defined`: all expected tier sets are defined
- [ ] `test_tier1_empty`: tier-1 empty expectation is preserved where applicable
- [ ] `test_tier4_defined`: tier-4 definition exists where expected
- [ ] `test_all_base_classes_defined`: base class definitions exist
- [ ] `test_breakthroughs_defined`: breakthrough definitions exist
- [ ] `test_all_types_have_name_templates`: type name-template completeness is preserved
- [ ] `test_all_terrains_have_names`: all terrains have names
- [ ] `test_all_terrains_have_race_labels`: all terrains have race labels
- [ ] `test_all_four_biomes_have_features`: all biomes expose expected features
- [ ] `test_all_regions_have_territory`: all regions have territory assignment
- [ ] `test_difficulty_zones_defined`: difficulty zones are defined
- [ ] `test_loot_tables_exist`: loot tables exist

---

## H. Safe fallback and degraded-mode assumptions

These tests assert that when something is missing, disabled, or unsupported, the system is supposed to fail soft or fall back safely.

- [ ] `test_detour_depth_limit_fallback`: detour depth fallback is preserved
- [x] `test_worker_pool_fallback_to_inline`: worker pool falls back to inline execution
- [ ] `test_rabbitmq_disabled_no_crash`: RabbitMQ-disabled mode does not crash
- [ ] `test_kafka_disabled_no_crash`: Kafka-disabled mode does not crash
- [ ] `test_redis_disabled_no_crash`: Redis-disabled mode does not crash
- [x] `test_headless_runner_importable_without_brokers`: headless runner imports safely without brokers
- [ ] `test_action_system_importable_without_brokers`: action system imports safely without brokers
- [x] `test_simulation_step_runs_without_brokers`: simulation can step without brokers
- [ ] `test_regression_runner_survives_no_infrastructure`: regression runner survives no-infrastructure mode
- [ ] `test_get_unknown`: unknown registry/class lookup is handled safely
- [ ] `test_unknown_trait_id_ignored`: unknown trait IDs are ignored safely
- [ ] `test_unknown_type_falls_back_to_physical`: unknown damage/action type falls back safely

---

## I. Caps, clamps, floors, ceilings, and boundedness assumptions

These tests assert what is supposed to happen at boundaries.

- [ ] `test_hp_clamped_after_recalc`: HP is clamped after recomputation
- [ ] `test_stamina_cannot_go_below_zero`: stamina lower bound is preserved
- [ ] `test_stamina_regen_capped`: stamina regeneration upper cap is preserved
- [ ] `test_training_does_not_exceed_cap`: training hard caps are preserved
- [x] `test_level_up_respects_cap`: level-up cap compliance is preserved
- [ ] `test_boss_diff_capped_at_4`: boss difficulty cap is preserved
- [ ] `test_specialized_training_soft_caps`: soft-cap law is preserved
- [ ] `test_output_derived_stat_ceilings`: derived-stat ceilings are preserved
- [ ] `test_physical_no_attributes_defaults_mult_to_1`: missing-attribute multiplier defaults are preserved
- [ ] `test_magical_no_attributes_defaults_mult_to_1`: magical default multiplier law is preserved
- [ ] `test_full_bag_returns_zero`: full-bag score/utility floor is preserved
- [ ] `test_overweight_loot_score_zero`: overweight loot utility floor is preserved

---

## J. Precedence, selection, and ordering assumptions

These tests assert what the system is supposed to prefer when multiple valid candidates exist.

- [ ] `test_objective_derivation_precedence_active_objective_if_no_blocker`: active-objective precedence is preserved
- [ ] `test_objective_derivation_precedence_first_unresolved_if_no_active`: unresolved-first precedence is preserved
- [x] `test_reserved_current_project_slot_is_used_when_current_project_exists`: current-project reserved slot law is preserved
- [ ] `test_next_step_returns_first_tile`: first-step path semantics are preserved
- [ ] `test_returns_nearest`: nearest-target selection is preserved
- [ ] `test_equidistant_returns_first`: stable first-on-tie semantics are preserved
- [ ] `test_best_ready_skill_returns_highest_power`: best-ready-skill precedence is preserved
- [ ] `test_best_ready_skill_skips_on_cooldown`: cooldown exclusion precedence is preserved
- [ ] `test_best_ready_skill_skips_insufficient_stamina`: stamina exclusion precedence is preserved
- [ ] `test_best_ready_skill_none_when_no_skills`: no-skill fallback is preserved

---

## K. Guardrail and authorization assumptions

These tests assert that the system is supposed to prevent or reject things in specific safe ways.

- [ ] `test_phase_guard_read_unauthorized`: unauthorized phase read is guarded
- [ ] `test_no_path_through_walls`: pathfinding guardrail against walls is preserved
- [ ] `test_next_step_no_path`: no-path fallback is preserved
- [ ] `test_safe_shot_detection`: safe-shot guard logic is preserved
- [ ] `test_no_flanking_bonus_when_facing_attacker`: flanking exclusion guardrail is preserved
- [ ] `test_no_opportunity_attack_when_moving_toward`: OA guardrail is preserved
- [ ] `test_no_cover_on_open_ground`: cover absence on open ground is preserved
- [ ] `test_non_equipment_ignored`: non-equipment inputs are ignored safely
- [ ] `test_cannot_breakthrough_no_class`: breakthrough precondition guard is preserved
- [ ] `test_no_class`: no-class guard behavior is preserved

---

## L. Metadata, inspection, and smoke-stability assumptions

These tests assert that inspection and debug-facing surfaces are supposed to remain safe even in empty or corrupted cases.

- [ ] `test_inspector_smoke_empty_state`: empty-state inspector safety is preserved
- [ ] `test_inspector_smoke_corrupted_state`: corrupted-state inspector safety is preserved
- [ ] `test_inspector_smoke_maximal_state`: maximal-state inspector safety is preserved
- [ ] `test_render_strategic_domain_empty`: empty strategic-domain rendering is preserved
- [ ] `test_empty_strategic_state_rendering`: empty strategic rendering is preserved
- [ ] `test_cognition_inspector_rendering`: cognition inspector rendering is preserved
- [ ] `test_cognition_empty_profile`: empty cognition-profile rendering is preserved

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

- [ ] Goal registry contains the expected built-in goals.
- [ ] Goal registry names are unique.
- [ ] Every built-in goal maps to a valid target AI state.
- [ ] Combat goal scores high when hostile enemies are visible.
- [ ] Flee goal scores high below HP threshold.
- [ ] Explore goal has a stable baseline score.
- [ ] Empty goal candidate list returns `None`.
- [ ] RNG value `0.0` selects the highest candidate.
- [ ] `top_n` selection limits candidates before weighted selection.
- [ ] Neuroticism can break goal commitment lock under low HP pressure.
- [ ] Legacy `goal_evaluator.py` shim behavior is preserved or intentionally removed.
- [ ] Loot goal returns zero when bag is full.
- [ ] Trade goal receives urgency when inventory is nearly full or overweight.

Why this matters: goal scoring is the bridge between cognition and action. If this drifts, V2 entities may have the same systems but completely different behavior.

---

## 2. EntityBuilder construction law

The checklist mentions entity aspects and spawning, but not the builder as an atomic compatibility surface. Legacy has a large fluent `EntityBuilder` contract: default identity, faction, AI state, stats, class attributes, race skills, class skills, inventory, home storage, traits, clique, household, leash, world role, and randomized spawn stats.

Add:

- [ ] EntityBuilder default entity has stable kind, faction, alive combat state, and wander AI state.
- [ ] `.kind()`, `.at()`, `.home()`, `.ai_state()`, `.faction()`, `.tier()` preserve exact field effects.
- [ ] Hero kind enforces minimum stamina behavior.
- [ ] Base stats initialize combat and progression fields consistently.
- [ ] Randomized stats use deterministic spawn-domain RNG.
- [ ] Hero class derives attributes and caps from class definition.
- [ ] Mob attributes scale by tier.
- [ ] Race attributes apply racial modifiers and deterministic variance.
- [ ] Race skills and class skills can be combined without loss.
- [ ] No-skills-by-default behavior is preserved.
- [ ] Builder supports clique, household, home building, world role, and leash fields.
- [ ] Builder-created entities deep-copy safely.

This is not “just construction.” It is the source of initial state truth.

---

## 3. Registry and data-driven loading law

The checklist mentions registries generally, but it should explicitly preserve the data-driven runtime contract.

Add:

- [ ] `load_all_registries()` loads items, classes, skills, breakthroughs, traits, spawn configs, and loot configs.
- [ ] Spawn config entries actually initialize generated entities.
- [ ] Loot config entries are loaded and used by `EntityGenerator`.
- [ ] Item registry lookup returns expected item type and bonuses.
- [ ] Class definitions contain class skill lists.
- [ ] Every class skill ID resolves in the skill registry.
- [ ] Missing registry entries fail safely, not silently.
- [ ] Registry loading is deterministic and idempotent.
- [ ] Duplicate or malformed data definitions are rejected or explicitly handled.

This is a big blind spot. A V2 port can pass behavior tests with hardcoded objects while silently breaking data-driven gameplay.

---

## 4. Quest lifecycle and generation

The checklist has quest mentions, but it is not atomic enough for the original quest tests.

Add:

- [ ] Quest starts with progress `0`, not completed.
- [ ] Quest progress ratio is correct.
- [ ] Quest `advance()` returns `True` only on first completion.
- [ ] Advancing an already completed quest does not mutate state.
- [ ] Quest copy is deep enough that copied progress mutation does not affect original.
- [ ] Quest serialization omits position for non-position quests.
- [ ] Explore quest serialization includes target position.
- [ ] Quest generation respects hero level.
- [ ] Quest generation skips duplicates.
- [ ] Quest rewards scale with level.
- [ ] Explore quest generation produces valid target positions.
- [ ] Template map and template list stay consistent.
- [ ] Entity quest list starts empty.
- [ ] Entity copies preserve quest progress independently.
- [ ] Hunt quest completion grants gold and XP.
- [ ] Explore quest completes within target proximity.
- [ ] Gather quest can advance by count.
- [ ] Max active quest limit is enforced.

Do not treat “dynamic quests exist” as enough. The old code had model, generator, tracking, reward, and serialization rules.

---

## 5. Equipment enhancement, home storage, shops, treasure chests

This is clearly underrepresented. The checklist mentions progression/classes/items, but not several old mechanics.

Add:

- [ ] `recalc_derived_stats()` creation mode applies attribute bonuses.
- [ ] `recalc_derived_stats()` delta mode removes old bonuses before applying new ones.
- [ ] HP clamps to new max HP after stat recalculation.
- [ ] Noncombat derived stats update vision, HP regen, trade bonus, and loot bonus.
- [ ] `auto_equip_best()` equips into empty slot.
- [ ] Better equipment replaces worse equipment and returns old item to inventory.
- [ ] Worse equipment is not auto-equipped.
- [ ] Non-equipment items are ignored by auto-equip.
- [ ] Unknown item power returns zero.
- [ ] Stronger item power ordering is stable.
- [ ] Home storage add/remove/full/copy behavior is preserved.
- [ ] Shop contains expanded item set.
- [ ] Buff potion item types are consumable.
- [ ] Skill learning respects level, prerequisites, and mastery.
- [ ] All hero classes expose at least one available skill chain.
- [ ] Treasure chests start available.
- [ ] Chest loot sets respawn tick and unavailable state.
- [ ] Chest respawns only at or after respawn tick.
- [ ] Chest loot tables exist for expected tiers.
- [ ] Entity copy preserves home storage deeply.
- [ ] Training that increments an attribute immediately recomputes derived stats.

This entire area is easy to lose because it sits between inventory, progression, and world objects.

---

## 6. Ranged combat, line-of-sight, cover, and range-aware skills

The existing checklist has ranged legality, but it needs finer atomic rules.

Add:

- [ ] Melee weapons default to range `1`.
- [ ] Shortbow and longbow have distinct weapon ranges.
- [ ] Clear horizontal line of sight passes.
- [ ] Clear diagonal line of sight passes.
- [ ] Wall between attacker and target blocks LOS.
- [ ] Wall on diagonal path blocks LOS.
- [ ] Adjacent tiles are always visible under legacy rule.
- [ ] Wall at endpoint does not block LOS.
- [ ] Wall at start does not block LOS.
- [ ] Adjacent wall counts as cover.
- [ ] Open ground gives no cover.
- [ ] Melee attack adjacent is valid.
- [ ] Melee attack out of range is invalid.
- [ ] Ranged attack at valid distance is valid.
- [ ] Unarmed entity range is `1`.
- [ ] Ranged skill can be selected at distance.
- [ ] Melee skill is not selected at ranged distance.
- [ ] Starting gear gives warrior sword and ranger bow.

The checklist currently risks collapsing this into “range and LOS exist.” That is not enough.

---

## 7. A\* pathfinding details

The checklist mentions movement and pathfinding, but several pathfinding laws are missing or buried.

Add:

- [ ] Straight-line path returns expected step count.
- [ ] Same start and goal returns empty path.
- [ ] Adjacent goal returns single-step path.
- [ ] Path routes around walls.
- [ ] Fully enclosed goal returns no path.
- [ ] Unwalkable goal returns no path.
- [ ] Returned path excludes start position.
- [ ] Max-node budget can terminate search with no path.
- [ ] `next_step()` returns first path tile.
- [ ] Occupied tiles are avoided.
- [ ] Goal tile can remain reachable even if listed as occupied.
- [ ] Road cost is lower than floor.
- [ ] Swamp cost is higher than floor.
- [ ] Terrain cost registry is used by pathfinding.
- [ ] Long-distance movement uses A\*.
- [ ] Short-distance movement can use greedy fallback.

That last distinction matters: A\* and greedy fallback are different behavior contracts, not implementation details.

---

## 8. Mob leash, chase give-up, and return-to-camp

The checklist has leash references, but the atomic old behavior needs to be explicit.

Add:

- [ ] Entity with `leash_radius=0` is never beyond leash.
- [ ] Entity with no home position is never beyond leash.
- [ ] Distance within leash returns false.
- [ ] Distance beyond leash returns true.
- [ ] Leash multiplier extends allowed chase range.
- [ ] Wander handler sends beyond-leash mob to return-to-camp.
- [ ] Within-leash mob continues wandering.
- [ ] No-leash mob wanders freely.
- [ ] Hunt handler abandons chase beyond `1.5x` leash.
- [ ] Hunt handler continues chase inside `1.5x` leash.
- [ ] Hunt handler gives up after chase timeout.
- [ ] Chase ticks reset on combat engagement.
- [ ] Return-to-camp heals while returning.
- [ ] Returning mob resumes normal behavior after reaching camp.

This is not just movement. It prevents mobs from becoming global homing missiles.

---

## 9. Group coordination and contract-party formation

The social checklist is broad, but group mechanics are under-specified.

Add:

- [ ] Entities with the same `cluster_id` and faction can form a group.
- [ ] Group requires at least two living members.
- [ ] Group leader is selected by highest level.
- [ ] Group anchor follows leader position.
- [ ] Members receive group ID linkage.
- [ ] Group dissolves if leader dies.
- [ ] Group removes dead members.
- [ ] Group dissolves if membership drops below two.
- [ ] Group cohesion decreases with distance from leader.
- [ ] Shared group goal biases member goal scoring.
- [ ] Distance from leader increases social regrouping bias.
- [ ] Active social contracts can instantiate party groups.
- [ ] Contract kind maps to shared group goal.
- [ ] Contract party dissolution applies contract consequences.

Without these, social “contracts” may exist as records but not as behavior.

---

## 10. Calamity / world-boss system

This is a real omission. The checklist mentions calamity evolution, but not the actual world-boss system.

Add:

- [ ] World maturity increases on schedule.
- [ ] Calamity spawn obeys interval and forced-spawn ticks.
- [ ] Spawned calamity has world-boss identity and role.
- [ ] Calamity uses legendary stats.
- [ ] Calamity receives legendary equipment/loot.
- [ ] Calamity spawn creates bounty quests for heroes.
- [ ] Calamity aura applies local debuffs.
- [ ] Camp reinforcements occur on schedule.
- [ ] Camp reinforcement level increases when camp is full.
- [ ] Faction raids spawn on raid interval.
- [ ] Raid mobs use raid AI state.
- [ ] Raid mobs do not return home.
- [ ] Killing world boss grants fame.
- [ ] Killing world boss grants title.
- [ ] Bounty completion rewards are applied.

This is not optional world flavor. It affects progression, quests, combat, world pressure, and hero identity.

---

## 11. Region and Voronoi topology

The checklist has world/regions, but not enough of the concrete topology contract.

Add:

- [ ] Region contains uses Manhattan distance.
- [ ] Region copy deep-copies locations.
- [ ] Location model preserves type, position, and region ID.
- [ ] Difficulty tier chosen by distance zones.
- [ ] Boundary distances map to expected tier.
- [ ] Empty difficulty zones default safely.
- [ ] Region name selection is deterministic by terrain counter.
- [ ] Resetting name counters restarts name sequence.
- [ ] Every terrain has region names.
- [ ] Every terrain has race label.
- [ ] Difficulty multipliers exist for all tiers.
- [ ] Difficulty multipliers scale upward.
- [ ] All location types have name templates.
- [ ] Expected POI types exist: camp, grove, ruins, dungeon, shrine, boss arena, outpost, watchtower, portal, fishing spot, graveyard, obelisk.
- [ ] Voronoi map coverage is near-total.
- [ ] Region terrain, overlays, details, and town tiles account for map tiles.
- [ ] Regions border each other.
- [ ] Every region owns some territory.
- [ ] `find_region_at()` returns nearest region.
- [ ] Equidistant region lookup returns first region.
- [ ] Empty region list returns `None`.
- [ ] Single region always matches.

This is a map-authority contract. If V2 changes it, spawning, difficulty, resource placement, and exploration all drift.

---

## 12. Platform primitives: RNG and spatial hash

The checklist mentions determinism, but not the primitive contracts.

Add:

- [ ] Deterministic RNG repeats exactly for same seed/domain/entity/tick.
- [ ] RNG domain separation produces different streams for different domains.
- [ ] `next_int()` always respects inclusive bounds.
- [ ] Spatial hash insert places entity in correct cell.
- [ ] Spatial hash radius query includes neighboring cells.
- [ ] Spatial hash move removes old cell membership and adds new cell membership.
- [ ] Spatial hash remove clears membership.
- [ ] Spatial hash behavior is deterministic independent of insertion order where required.

These are low-level, but if they drift, every higher-level system becomes untrustworthy.

---

## 13. Phase guard and authoritative phase authorization

The checklist only has one unauthorized phase read item. Legacy tests cover more.

Add:

- [ ] Unauthorized phase read raises.
- [ ] Unauthorized phase mutation raises.
- [ ] Unauthorized phase emit raises.
- [ ] Authorized mutation succeeds only in permitted phase.
- [ ] Internal field access is controlled.
- [ ] Scheduling phase cannot mutate HP.
- [ ] Persistence phase is read-only.
- [ ] Phase guard prevents bypassing authoritative action/update application.
- [ ] Nested phase access follows the same authorization law.

This is directly tied to V2’s “one authoritative mutation path” principle.

---

## 14. Behavior inspection and presenter truth

The checklist excludes UI-only presentation, which is fine. But some inspection/presenter behavior is not merely UI. It is behavioral explainability and debugging truth.

Add under an optional “inspection truth” section:

- [ ] AI presenter maps structured decision drivers.
- [ ] Belief inspection includes apparent state.
- [ ] Injury blurring affects API-visible state consistently.
- [ ] Stat breakdown service matches real derived stat math.
- [ ] Combat trace recording is inspectable.
- [ ] AI explainability persists across ticks.
- [ ] Scheduler timeline is inspectable.
- [ ] Entity inspection behavior matches legacy.
- [ ] AI explanation parity is preserved or intentionally divergent.
- [ ] Missing continuity data is handled safely.
- [ ] Corrupted inspection state does not crash.

This should not be mixed with gameplay parity, but it should not disappear either. Debug surfaces are part of operational truth.

---

## 15. Assertion and test helper semantics

The checklist should preserve some internal validation helpers because they define what “consistent” means.

Add:

- [ ] Strategic consistency assertion fails on real drift.
- [ ] Cognition consistency assertion fails when replay and graph diverge.
- [ ] Graph integrity assertion catches broken cognition graph structure.
- [ ] Determinism assertion compares actual replay outputs, not superficial success.
- [ ] Overload behavior assertion preserves capacity failure semantics.
- [ ] Combat arena helper preserves default factions, hostility, tick running, and entity lookup semantics.
- [ ] Legacy stat helper preserves expected combat math inputs.

This sounds like test infrastructure, but it encodes legacy truth. Removing it weakens the audit.

---

## 16. Brokerless, recovery, and degraded-mode behavior tied to execution

Some infra is outside RPG-core scope, but not all of it. If missing Kafka/RabbitMQ changes whether the simulation step can run, it belongs in the checklist.

Add:

- [ ] Simulation step runs when brokers are missing.
- [ ] RabbitMQ missing-package path fails closed or disables cleanly.
- [ ] Kafka missing-package path fails closed or disables cleanly.
- [ ] Engine manager recovery handles missing Kafka.
- [ ] Worker pool RabbitMQ dispatch contract is preserved if broker mode is supported.
- [ ] Kafka recovery can reconstruct from snapshot plus event stream.
- [ ] Live-vs-manual replay produces same world state for loot recovery.

This connects directly to V2’s lifecycle and operational-truth goals.
