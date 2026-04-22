### Unclassified-but-included RPG-core tests

#### `ai/test_intel_capacity_regression.py`

- [ ] `test_intel_capacity_replay_and_graph_export`: Intel capacity replay and graph export — Verify that cognitive metrics survive replay and graph export pipelines..
- [x] `test_intel_capacity_determinism`: Intel capacity determinism — Verify that identical seeds produce identical cognitive profiles and artifacts..
- [ ] `test_intel_capacity_overload_injection`: Intel capacity overload injection — Inject extreme cognitive pressure and verify overload triggering in artifacts..
- [ ] `test_intel_capacity_divergence_scenario`: Intel capacity divergence scenario — Verify that different attributes lead to differing usage artifacts..
- [ ] `test_intel_capacity_detour_depth_hardbound`: Intel capacity detour depth hardbound — Verify that detour depth is capped in artifacts even under pressure..

#### `ai/test_intel_capacity_visibility.py`

- [ ] `test_cognition_api_serialization`: Cognition api serialization — Verify that cognitive metrics are correctly serialized for the API..
- [ ] `test_cognition_inspector_rendering`: Cognition inspector rendering — Verify that the CLI inspector correctly renders cognitive data..
- [ ] `test_cognition_empty_profile`: Cognition empty profile — Verify that inspector handles entities without cognitive profiles gracefully..

#### `integration/strategy/test_building_to_strategy_pipeline.py`

- [ ] `test_rng`: Rng.
- [ ] `test_entity`: Entity.
- [ ] `test_guild_intel_to_strategy_visible_pipeline`: Guild intel to strategy visible pipeline — Verify that guild intel produces leads/zones that are visible in API schemas..
- [ ] `test_blacksmith_blocker_resolution_pipeline`: Blacksmith blocker resolution pipeline — Verify that blacksmith constraints produce blockers that are resolved by acquisition..

#### `integration/strategy/test_knowledge_continuity_stabilization.py`

- [ ] `test_milestone_3_lead_testing_and_persistence`: Milestone 3 lead testing and persistence — Verify that exhausted search marks leads as tested and persists them..
- [ ] `test_milestone_4_social_filtering`: Milestone 4 social filtering — Verify that social candidate selection filters hostiles and uses debt..
- [ ] `test_strategic_uncertainty_and_anti_cheating`: Strategic uncertainty and anti cheating — Verify that rumors have lower certainty and vague leads don't 'cheat' with perfect coords..

#### `integration/strategy/test_lead_feedback_loops.py`

- [ ] `test_source_trust_recalibration`: Source trust recalibration — Verify that a 'False' lead outcome reduces source trust..
- [ ] `test_severe_failure_abandonment_impact`: Severe failure abandonment impact — Verify that a project switch/abandonment reflects in strategic drivers..

#### `integration/strategy/test_strategy_observability_consistency.py`

- [ ] `test_rng`: Rng.
- [ ] `test_entity`: Entity.
- [ ] `test_strategy_observability_consistency`: Strategy observability consistency — Verify that a strategic shift is consistently observable across all surfaces..
- [ ] `test_strategic_decision_driver_traceability`: Strategic decision driver traceability — Verify that DecisionDriver records flow from AIBrain to the entity state..

#### `movement/test_congestion_milestone_3.py`

- [x] `test_blocked_retreat_yield`: Blocked retreat yield — Verify high-priority RETREAT ally forces yield from lower-priority ally..
- [x] `test_oscillation_suppression`: Oscillation suppression — Verify A-B-A-B movement is suppressed after 2 cycles..
- [x] `test_reroute_hysteresis`: Reroute hysteresis — Verify minor reroutes are ignored to prevent flip-flopping..
- [x] `test_safe_sidestepping`: Safe sidestepping — Verify yielding entities do not sidestep closer to danger..

original evidence: `movement/test_congestion_milestone_3.py`
`src_v2` evidence: `src_v2/engine/movement.py`
divergence note: v2 converges movement and congestion resolution into the `MovementSystem` to enforce spatial truth and prevent thrashing.
proof path: `tests_v2/engine/test_anti_thrashing.py`

#### `unit/ai/strategy/test_recruitment_negotiation.py`
 
- [x] `test_recruitment_offer_generation`: Recruitment offer generation — Verify that a recruiter creates a reasonable offer based on greed and risk.
- [x] `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend.
- [x] `test_recruitment_haggling_counter_offer`: Recruitment haggling counter offer — Verify greedy candidate counter-offers when the payout is too low.
- [x] `test_recruiter_evaluates_counter`: Recruiter evaluates counter — Verify recruiter accepts a counter-offer for an urgent project.

#### `unit/ai/test_action_styles.py`

- [ ] `test_execution_phase_modifies_proposal_with_aggressive_style`: Execution phase modifies proposal with aggressive style.
- [ ] `test_execution_phase_modifies_proposal_with_evasive_style`: Execution phase modifies proposal with evasive style.

#### `unit/ai/test_ai_heuristics.py`

- [ ] `test_ai_boredom_diversification`: Ai boredom diversification — Verify that an entity eventually shifts away from a repetitive goal due to boredom..
- [ ] `test_life_stage_priority_shift`: Life stage priority shift — Verify level 1 and level 25 entities have different goal preferences..

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
- [ ] `test_emotional_bias_on_utility`: Emotional bias on utility — Verify DREAD increases FLEE utility and decreases EXPLORE utility..
- [ ] `test_emotional_decay`: Emotional decay — Verify emotions propose negative delta for decay..

#### `unit/ai/test_emotions.py`

- [ ] `test_appraisal_phase_triggers_panic_on_low_hp`: Appraisal phase triggers panic on low hp.

#### `unit/ai/test_flanking.py`

- [ ] `test_flanking_bonus`: Flanking bonus.
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
- [x] `test_apply_building_sabotage`: Apply building sabotage.

#### `unit/combat/test_combat_building.py`

- [ ] `test_building_sabotage_validation`: Building sabotage validation.
- [x] `test_building_sabotage_application`: Building sabotage application.

#### `unit/combat/test_consequences.py`

- [ ] `test_wound_infliction_massive_hit`: Wound infliction massive hit — Verify that damage > 25% max HP guarantees a wound..
- [ ] `test_wound_stat_impact`: Wound stat impact — Verify that wounds correctly reduce properties in CombatAspect..
- [ ] `test_scar_permanence`: Scar permanence — Verify that scars are permanent and identifiable..

#### `unit/combat/test_exhaustion.py`

- [ ] `test_stamina_drain_on_attack`: Stamina drain on attack — Verify that a basic attack drains stamina from the actor..
- [ ] `test_exhaustion_penalty_application`: Exhaustion penalty application — Verify that ActionSystem applies fatigue effect when stamina is low..

#### `unit/core/aspects/test_aoa_integrity.py`

- [x] `test_entity_field_integrity`: Entity field integrity — Ensure Entity model_fields contains only the ID, Kind, and Aspects..
- [x] `test_entity_property_locking`: Entity property locking — Ensure no forbidden legacy properties have been re-introduced as shims..
- [x] `test_aspect_model_purity`: Aspect model purity — Ensure aspects themselves stay clean of Cross-Aspect dependencies..
- [ ] `test_mandatory_aspect_naming`: Mandatory aspect naming — Aspects must be named exactly as their type (lowercase)..

original evidence: `unit/core/aspects/test_aoa_integrity.py`
`src_v2` evidence: `src_v2/core/state.py`
divergence note: v2 utilizes a flattened `EntityState` with typed components (`Identity`, `Inventory`, `Strategic`) to enforce the new AOA contract.
proof path: `tests_v2/core/test_authoritative_state_contract.py`

#### `unit/core/aspects/test_evolution.py`

- [x] `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap. [AOA REFACTOR].
- [x] `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment. [AOA REFACTOR].

#### `unit/core/aspects/test_genetics.py`

- [ ] `test_genetic_seed_init`: Genetic seed init.
- [ ] `test_training_uses_aptitudes`: Training uses aptitudes.
- [ ] `test_aging_and_death`: Aging and death.

#### `unit/core/logic/test_person_logic.py`

- [ ] `test_personality_bias_logic`: Personality bias logic.
- [ ] `test_social_appraisal_logic`: Social appraisal logic.
- [ ] `test_full_motive_pipeline_integration`: Full motive pipeline integration — Verifies that social and personality biases stack correctly..

#### `unit/core/logic/test_routine_service.py`

- [ ] `test_routine_service_sleep_bias`: Routine service sleep bias.
- [ ] `test_routine_service_forced_rest_during_off_hours`: Routine service forced rest during off hours.
- [ ] `test_routine_service_hunger_bias`: Routine service hunger bias.

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
- [x] `test_entity_copy_shallow_vs_refs`: Entity copy shallow vs refs — Verify Entity.copy() is shallow for aspects but produces a new Entity object..
- [x] `test_ai_worker_batch_processing_logic`: Ai worker batch processing logic — Verify AIWorkerDaemon correctly handles a batch of tasks..

original evidence: `unit/core/test_performance_optimizations.py`
`src_v2` evidence: `src_v2/engine/executor.py`, `src_v2/engine/kernel.py`
divergence note: v2 replaces the generic AIWorkerDaemon with a profile-driven `IWorkExecutor` strategy (Sequential or Concurrent).
proof path: `tests_v2/engine/test_worker_equivalence.py`

#### `unit/systems/test_action_convergence.py`

- [ ] `test_loot_no_duplication`: Loot no duplication — Verify that items picked up by the system are not duplicated by AI updates..
- [ ] `test_corpse_loot_convergence`: Corpse loot convergence — Verify that corpse recovery is authoritatively handled by ActionSystem..

#### `unit/systems/test_dynamic_quests.py`

- [x] `test_dynamic_liberate_quest`: Dynamic liberate quest.
- [ ] `test_history_logging`: History logging.

#### `unit/systems/test_evolution.py`

- [x] `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap..
- [x] `test_evolution_equipment_refresh`: Evolution equipment refresh — Verify that evolution provides new equipment..

#### `unit/systems/test_personality_ai.py`

- [ ] `test_grudge_accumulation`: Grudge accumulation.
- [ ] `test_should_flee_logic`: Should flee logic.
- [ ] `test_locational_memory_on_death`: Locational memory on death.
- [ ] `test_frontier_locational_penalty`: Frontier locational penalty.
