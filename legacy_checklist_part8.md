# Legacy `src` Assumption / Invariant Checklist — Part 8

This checklist is additive to Parts 1–7.

It is not a new gameplay-logic trunk.
It exists to capture **legacy assumptions and invariants** that the old system was supposed to have and that are explicitly enforced by tests.

These are the kinds of rules that often get broken during migration because they are treated as “small details,” even though they are foundational to trustworthiness.

This part should remain **test-first**.

---

## A. Default-state and neutral-behavior assumptions

These tests assert what objects or systems are supposed to look like before gameplay meaning starts.

- [x] `test_default_values`: default entity/build values are preserved
- [x] `test_default_values_all_zero`: default zero-valued state is preserved
- [x] `test_default_multiplicative_values_are_1`: default multiplicative modifiers equal 1
- [x] `test_default_additive_values_are_0`: default additive modifiers equal 0
- [x] `test_default_metadata_is_none`: metadata defaults to `None`
- [x] `test_none_metadata_preserved`: `None` metadata remains preserved
- [x] `test_schema_none_metadata`: schema handles `None` metadata correctly
- [x] `test_no_skills_by_default`: entities have no skills by default
- [x] `test_no_inventory_by_default`: entities have no inventory by default
- [x] `test_no_traits_by_default`: entities have no traits by default
- [x] `test_entity_starts_with_no_quests`: entities start with no quests
- [x] `test_default_core_rate_is_1`: default core subsystem rate is preserved
- [x] `test_default_environment_rate_is_2`: default environment subsystem rate is preserved
- [x] `test_default_economy_rate_is_5`: default economy subsystem rate is preserved
- [x] `test_default_region_id`: default region identifier is preserved
- [x] `test_default_empty`: default empty collection/container semantics are preserved
- [x] `test_empty_zones_returns_1`: empty-zone fallback behavior is preserved
- [x] `test_empty_regions_returns_none`: empty-region lookup returns `None`
- [x] `test_select_returns_none_on_empty`: selection on empty inputs returns `None`
- [x] `test_export_empty_strategy`: exporting empty strategy state is safe

---

## B. No-op, empty-tick, and “does nothing safely” assumptions

These tests assert that when there is nothing to do, the system degrades safely and predictably.

- [x] `test_no_changes_skipped`: no-change updates are skipped safely
- [x] `test_effects_tick_on_empty_tick`: effects still tick on empty ticks
- [x] `test_stamina_regens_on_empty_tick`: stamina regen still occurs on empty ticks
- [x] `test_skill_cooldowns_tick_on_empty_tick`: skill cooldowns still tick on empty ticks
- [x] `test_quest_advance_does_nothing_when_completed`: completed quests ignore further advance calls
- [x] `test_unknown_action_does_nothing`: unknown actions are safely ignored
- [x] `test_full_hp_no_change`: full-HP state remains unchanged
- [x] `test_no_region_no_penalty`: no-region case applies no penalty
- [x] `test_safe_region_no_penalty`: safe-region case applies no penalty
- [x] `test_unknown_region_returns_0`: unknown region uses zero/fallback difficulty
- [x] `test_no_region_returns_0`: no-region difficulty fallback is preserved

---

## C. Copy, clone, preservation, and ownership assumptions

These tests assert what is supposed to be preserved across copying and what must not be shared.

- [x] `test_quest_copy`: quest copy preserves quest state
- [x] `test_entity_copy_preserves_quests`: entity copy preserves quests
- [x] `test_entity_copy_preserves_attributes`: entity copy preserves attributes
- [x] `test_entity_copy_preserves_skills`: entity copy preserves skills
- [x] `test_entity_copy_includes_home_storage`: entity copy preserves home storage
- [x] `test_entity_without_home_storage`: no-home-storage case remains safe
- [x] `test_region_copy`: region copy semantics are preserved
- [x] `test_attributes_copy`: attribute copy semantics are preserved
- [x] `test_copy`: generic model copy semantics are preserved wherever tested
- [x] `test_grid_copy_is_not_shared`: copied grids are not aliased
- [x] `test_entity_copy_shallow_vs_refs`: copy/ref-sharing behavior is explicit and preserved
- [x] `test_latest_preserves_metadata`: latest-version object preserves metadata

---

## D. Serialization, schema, and round-trip assumptions

These tests assert that important models are supposed to serialize safely and consistently.

- [x] `test_serialization_round_trip`: serialization round-trip is preserved
- [x] `test_item_serialization`: item serialization is preserved
- [x] `test_enchanted_blade_serialization`: enchanted item serialization is preserved
- [x] `test_skill_serialization`: skill serialization is preserved
- [x] `test_passive_skill_serialization`: passive skill serialization is preserved
- [x] `test_class_serialization`: class serialization is preserved
- [x] `test_breakthrough_serialization`: breakthrough serialization is preserved
- [x] `test_trait_serialization`: trait serialization is preserved
- [x] `test_history_registry_serialization`: history registry serialization is preserved
- [x] `test_entity_to_full_schema_no_crash`: full schema export does not crash
- [x] `test_serialization_pydantic_model`: pydantic serialization assumption is preserved
- [x] `test_serialization_frozen_model_with_proxy`: frozen/proxy serialization is preserved
- [x] `test_inspection_serialization`: inspection serialization is preserved
- [x] `test_cognition_api_serialization`: cognition API serialization is preserved

---

## E. Freeze, immutability, and deep-isolation assumptions

These tests assert that certain state surfaces are supposed to be frozen, safe, and non-mutating.

- [x] `test_entity_deep_copy_isolation`: deep-copy isolation is preserved
- [x] `test_deep_freeze_nested_collections`: deep freeze handles nested collections
- [x] `test_deep_freeze_idempotency`: deep freeze is idempotent
- [x] `test_freeze_calls_validate`: freeze triggers validation correctly
- [x] `test_nested_freeze_invariants`: nested freeze invariants are preserved
- [x] `test_world_state_freeze_guards`: world-state freeze guards are preserved
- [x] `test_simulation_model_collection_freeze_list`: list freezing behavior is preserved
- [x] `test_simulation_model_collection_freeze_dict`: dict freezing behavior is preserved
- [x] `test_vector2_coercion_during_freeze`: vector coercion during freeze is preserved
- [x] `test_non_mutation`: non-mutation guarantee is preserved
- [x] `test_build_profile_does_not_mutate_caps`: cognition-profile derivation is non-mutating
- [x] `test_build_profile_returns_new_profile_object_each_call`: fresh profile object guarantee is preserved

---

## F. Determinism and repeatability assumptions

These tests assert that the system is supposed to be repeatable under the same conditions.

- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: deterministic profile derivation
- [x] `test_intel_capacity_determinism`: intelligence-capacity determinism is preserved
- [x] `test_strategic_replay_graph_equality`: replay graph equality is preserved
- [x] `test_same_seed_same_result`: same-seed world/result determinism is preserved
- [x] `test_harness_non_determinism_different_seed`: different-seed divergence remains explicit
- [x] `test_first_by_id_wins_same_tile`: deterministic same-tile tie-breaking is preserved
- [x] `test_diagonal_same_target_one_wins`: deterministic same-target conflict resolution is preserved
- [x] `test_non_conflicting_moves_both_succeed`: independent valid moves both survive
- [x] `test_equidistant_returns_first`: deterministic first-choice behavior on ties is preserved

---

## G. Registry, definition, and data-completeness assumptions

These tests assert that key registries and definition maps are supposed to exist and be complete.

- [x] `test_item_registry_not_empty`: item registry is non-empty
- [x] `test_skill_defs_not_empty`: skill definitions are non-empty
- [x] `test_trait_defs_not_empty`: trait definitions are non-empty
- [x] `test_registry_not_empty`: generic registry non-empty guarantee is preserved
- [x] `test_skill_registry_not_empty`: skill registry is non-empty
- [x] `test_all_trait_types_have_definitions`: all trait types have definitions
- [x] `test_all_tiers_defined`: all expected tier sets are defined
- [x] `test_tier1_empty`: tier-1 empty expectation is preserved where applicable
- [x] `test_tier4_defined`: tier-4 definition exists where expected
- [x] `test_all_base_classes_defined`: base class definitions exist
- [x] `test_breakthroughs_defined`: breakthrough definitions exist
- [x] `test_all_types_have_name_templates`: type name-template completeness is preserved
- [x] `test_all_terrains_have_names`: all terrains have names
- [x] `test_all_terrains_have_race_labels`: all terrains have race labels
- [x] `test_all_four_biomes_have_features`: all biomes expose expected features
- [x] `test_all_regions_have_territory`: all regions have territory assignment
- [x] `test_difficulty_zones_defined`: difficulty zones are defined
- [x] `test_loot_tables_exist`: loot tables exist

---

## H. Safe fallback and degraded-mode assumptions

These tests assert that when something is missing, disabled, or unsupported, the system is supposed to fail soft or fall back safely.

- [x] `test_detour_depth_limit_fallback`: detour depth fallback is preserved
- [x] `test_worker_pool_fallback_to_inline`: worker pool falls back to inline execution
- [x] `test_rabbitmq_disabled_no_crash`: RabbitMQ-disabled mode does not crash
- [x] `test_kafka_disabled_no_crash`: Kafka-disabled mode does not crash
- [x] `test_redis_disabled_no_crash`: Redis-disabled mode does not crash
- [x] `test_headless_runner_importable_without_brokers`: headless runner imports safely without brokers
- [x] `test_action_system_importable_without_brokers`: action system imports safely without brokers
- [x] `test_simulation_step_runs_without_brokers`: simulation can step without brokers
- [x] `test_regression_runner_survives_no_infrastructure`: regression runner survives no-infrastructure mode
- [x] `test_get_unknown`: unknown registry/class lookup is handled safely
- [x] `test_unknown_trait_id_ignored`: unknown trait IDs are ignored safely
- [x] `test_unknown_type_falls_back_to_physical`: unknown damage/action type falls back safely

---

## I. Caps, clamps, floors, ceilings, and boundedness assumptions

These tests assert what is supposed to happen at boundaries.

- [x] `test_hp_clamped_after_recalc`: HP is clamped after recomputation
- [x] `test_stamina_cannot_go_below_zero`: stamina lower bound is preserved
- [x] `test_stamina_regen_capped`: stamina regeneration upper cap is preserved
- [x] `test_training_does_not_exceed_cap`: training hard caps are preserved
- [x] `test_level_up_respects_cap`: level-up cap compliance is preserved
- [x] `test_boss_diff_capped_at_4`: boss difficulty cap is preserved
- [x] `test_specialized_training_soft_caps`: soft-cap law is preserved
- [x] `test_output_derived_stat_ceilings`: derived-stat ceilings are preserved
- [x] `test_physical_no_attributes_defaults_mult_to_1`: missing-attribute multiplier defaults are preserved
- [x] `test_magical_no_attributes_defaults_mult_to_1`: magical default multiplier law is preserved
- [x] `test_full_bag_returns_zero`: full-bag score/utility floor is preserved
- [x] `test_overweight_loot_score_zero`: overweight loot utility floor is preserved

---

## J. Precedence, selection, and ordering assumptions

These tests assert what the system is supposed to prefer when multiple valid candidates exist.

- [x] `test_objective_derivation_precedence_active_objective_if_no_blocker`: active-objective precedence is preserved
- [x] `test_objective_derivation_precedence_first_unresolved_if_no_active`: unresolved-first precedence is preserved
- [x] `test_reserved_current_project_slot_is_used_when_current_project_exists`: current-project reserved slot law is preserved
- [x] `test_next_step_returns_first_tile`: first-step path semantics are preserved
- [x] `test_returns_nearest`: nearest-target selection is preserved
- [x] `test_equidistant_returns_first`: stable first-on-tie semantics are preserved
- [x] `test_best_ready_skill_returns_highest_power`: best-ready-skill precedence is preserved
- [x] `test_best_ready_skill_skips_on_cooldown`: cooldown exclusion precedence is preserved
- [x] `test_best_ready_skill_skips_insufficient_stamina`: stamina exclusion precedence is preserved
- [x] `test_best_ready_skill_none_when_no_skills`: no-skill fallback is preserved

---

## K. Guardrail and authorization assumptions

These tests assert that the system is supposed to prevent or reject things in specific safe ways.

- [x] `test_phase_guard_read_unauthorized`: unauthorized phase read is guarded
- [x] `test_no_path_through_walls`: pathfinding guardrail against walls is preserved
- [x] `test_next_step_no_path`: no-path fallback is preserved
- [x] `test_safe_shot_detection`: safe-shot guard logic is preserved
- [x] `test_no_flanking_bonus_when_facing_attacker`: flanking exclusion guardrail is preserved
- [x] `test_no_opportunity_attack_when_moving_toward`: OA guardrail is preserved
- [x] `test_no_cover_on_open_ground`: cover absence on open ground is preserved
- [x] `test_non_equipment_ignored`: non-equipment inputs are ignored safely
- [x] `test_cannot_breakthrough_no_class`: breakthrough precondition guard is preserved
- [x] `test_no_class`: no-class guard behavior is preserved

---

## L. Metadata, inspection, and smoke-stability assumptions

These tests assert that inspection and debug-facing surfaces are supposed to remain safe even in empty or corrupted cases.

- [x] `test_inspector_smoke_empty_state`: empty-state inspector safety is preserved
- [x] `test_inspector_smoke_corrupted_state`: corrupted-state inspector safety is preserved
- [x] `test_inspector_smoke_maximal_state`: maximal-state inspector safety is preserved
- [x] `test_render_strategic_domain_empty`: empty strategic-domain rendering is preserved
- [x] `test_empty_strategic_state_rendering`: empty strategic rendering is preserved
- [x] `test_cognition_inspector_rendering`: cognition inspector rendering is preserved
- [x] `test_cognition_empty_profile`: empty cognition-profile rendering is preserved

---

## M. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map assumption logic to roadmap owners rather than creating another giant roadmap phase.

- [x] Phase 7 owns:
  - serialization / freeze / deep-isolation / determinism / phase guards / non-mutation assumptions

- [x] Phase 8 owns:
  - immediate-action guardrails
  - local boundedness and combat/tactical caps/clamps
  - local selection/tie-breaking assumptions where action resolution depends on them

- [x] Phase 9 owns:
  - precedence and boundedness assumptions in cognition/strategy/progression
  - traits / registries / progression caps where they materially shape long-horizon gameplay

- [x] Phase 10 owns:
  - disabled-mode / fallback / importability / infra-safe assumptions
  - consumer/entry black-box degraded-mode assumptions

- [x] Phase 11+ owns:
  - governance truth for any surviving invariant classified as preserved/divergent/unsupported

---

## Completion rule for Part 8

A Part 8 item is not closed merely because the system “seems to behave sensibly.”

Each item should be considered closed only when:

- [x] the specific assumption has a clear roadmap owner
- [x] the specific assumption has direct implementation or an explicit divergence/unsupported decision
- [x] the specific assumption has test coverage or proof justification
- [x] the support boundary and replacement ledger reflect its true status
