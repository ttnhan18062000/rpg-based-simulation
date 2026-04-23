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

- [x] `test_sleep_goal_utility_at_night`: sleep utility at night (RoutineService)
- [x] `test_rest_to_sleep_transition`: rest-to-sleep transition
- [x] `test_routine_service_sleep_bias`: sleep bias
- [x] `test_routine_service_forced_rest_during_off_hours`: forced off-hours rest
- [x] `test_routine_service_hunger_bias`: hunger bias
- [x] `test_home_visit_leads_to_eating`: eating behavior from routine/home visit
- [x] `test_inn_visit_leads_to_sleeping`: inn visit leads to sleeping
- [x] `test_biological_decay_and_forced_sleep`: biological decay and forced sleep
- [x] `test_sleeping_recovery_cycle`: sleeping recovery cycle
- [x] `test_hunger_reduces_stability`: hunger consequence
- [x] `test_routine_goal_priority`: routine goal priority
- [x] `test_routine_disruption_panic`: disruption panic
- [x] `test_attack_disruption_suppresses_routines`: attack suppresses routine
- [x] `test_routine_priority_archetype_bias`: archetype-based routine bias
- [x] `test_life_stage_priority_shift`: life-stage priority shift

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
- [ ] `test_emotional_bias_on_utility`: emotion changes utility
- [ ] `test_emotional_decay`: emotional decay
- [ ] `test_narrative_memory_trauma_biasing`: trauma memory biasing
- [ ] `test_narrative_memory_victory_confidence`: victory-confidence memory
- [x] `test_narrative_memory_logging`: narrative memory logging
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
- [ ] `test_scar_detection`: scar detection
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
- [ ] `test_flanking_bonus`: flanking bonus
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

- [x] `test_regional_suppression`: regional suppression (AuthoritativeApplyPipeline)
- [x] `test_strategic_pivot_on_regional_danger`: pivot on regional danger
- [x] `test_region_fatigue_biasing`: region fatigue biasing (Regional hazard drain)
- [x] `test_region_consequence_record`: region consequence record
- [x] `test_conquered_region_triggers_stronghold`: conquered region -> stronghold consequence
- [x] `test_strategic_pipeline_home_threat`: home threat in strategic pipeline
- [ ] `test_world_consequence_*`: world consequence interpretation coverage where applicable

---

## I. Death / permadeath / succession / heirlooms / nemesis

Relevant original source/test evidence:

- lifecycle / death / social-consequence logic in `all_src.py`
- related tests in `all_test.py`

- [x] `test_aging_and_death`: aging and death (LifecycleSystem)
- [x] `test_hero_lifecycle_system_permadeath`: hero permadeath
- [x] `test_permadeath_succession_and_heirlooms`: succession and heirlooms
- [x] `test_hero_death_creates_scar`: death scar consequences
- [x] `test_near_death_triggers_survival_consequences`: near-death survival consequences
- [x] `test_near_death_hardening`: near-death hardening (+5 HP)
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
