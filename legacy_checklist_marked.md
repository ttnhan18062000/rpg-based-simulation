# legacy_checklist_v2_marked.md — checked lines only

## A. Source logic inventory

### Authoritative action and update model

- [x] Action proposals are typed intents, not direct world mutation.
- [x] World mutation happens after proposal generation, not inside worker thought code.
- [x] Action application supports partial rejection without corrupting unrelated update domains.
- [x] Conflict resolution preserves one authoritative outcome per tick.
- [x] Worker decision-making is decoupled from authoritative application.
- [x] Replay and observability consume authoritative results rather than defining them.

### Combat / movement / legality / tactics

- [x] Manhattan distance is the shared spatial metric for movement and combat range where claimed.
- [x] Cardinal/tile movement and occupancy legality are explicit.
- [x] Occupied-tile movement is rejected or redirected rather than silently overlapped.
- [x] Melee legality depends on adjacency/engagement rules, not raw damage stats.
- [x] Ranged legality depends on range and line-of-sight rules.
- [x] Quiet ticks still advance passive world consequences.
- [x] Disengagement, pursuit, target stickiness, and opportunity consequences are explicit rules.
- [x] Anti-stalemate logic handles repeated chase/kite/step-back loops.
- [x] Tactical choice is a bounded choice among legal actions, not a geometry exploit.

### Resource interaction / inventory / buildings / town loop

- [x] Looting is a channeled state with progress, interruption, and completion semantics.
- [x] Harvesting is a channeled state tied to nearby resource-node legality and harvest duration.
- [x] Loot/harvest can abort because of inventory slot pressure.
- [x] Loot/harvest can abort because of inventory weight pressure.
- [x] Inventory state tracks both slots and weight/carry burden.
- [x] Ground items, node yields, and inventory additions/removals are authoritative side effects.
- [x] Town return is a real gameplay state, not a cosmetic teleport.
- [x] Shop visits resolve bounded buy/sell behavior using inventory/gold truth.
- [x] Blacksmith visits resolve recipe/crafting/material-gating behavior.
- [x] Inn/home/class-hall visits have distinct progression or recovery semantics.
- [x] Building interactions are explicit gameplay slices, not generic proximity triggers.

### Strategic mind / projects / blockers / leads / cognition

- [x] Strategic state is first-class and survives across ticks (directives, projects, objectives, concerns, blockers, obligations, contracts, offers, leads, candidate zones, hypotheses).
- [x] Current project/objective continuity is explicit and bounded.
- [x] Project switching uses interruption resistance / margin logic, not full rescore every tick.
- [x] Blockers are inferred from project/objective state and can be accurate or misdiagnosed under bounded cognition.
- [x] Leads are retained under profile-specific bandwidth limits.
- [x] Concerns are retained under profile-specific intake limits.
- [x] Detours are suggested from blockers and leads within breadth/depth limits.
- [x] Rejected/tested leads are suppressed to avoid blind retries.
- [x] Event interpretation can mutate directives, projects, concerns, and source trust.
- [x] Knowledge remains uncertain (leads/candidate zones/hypotheses) until resolved.
- [x] Cognition graph export exposes persisted strategic state without becoming the source of truth.

### Social / contracts / relationships / reputation

- [x] Private betrayal history can override public recruiter reputation.
- [x] Social learning updates familiarity/trust-like bonds from interaction evidence.
- [x] Social contracts and obligations are explicit strategic objects, not flavor text.
- [x] Breaking or honoring contracts has persistent consequences.
- [x] Public reputation is distinct from private narrative meaning.
- [x] Turning points and interpreted life events feed future strategic and social behavior.
- [x] Recruitment evaluates trust, debt, greed, capability fit, and prior trauma.

### Progression / classes / skills / attributes / entity growth

- [x] Attributes have domain ownership and scaling semantics.
- [x] Combat and progression rewards update gold, XP, veterancy, effects, and consequences through authoritative updates.

### World / entities / regions / spawning / deterministic substrate

- [x] World generation is deterministic under seed and domain-specific RNG use.
- [x] Entity snapshots are immutable enough for worker reasoning and deterministic replay.
- [x] No hidden mutation leaks occur from snapshot or AI evaluation paths.
- [x] Deterministic replay/delta behavior is preserved across runs with same seed.
- [x] Regional hazards, calamities, local scars, and world consequences can feed gameplay and strategy.
- [x] Entity builder and serialization preserve gameplay-relevant state safely.
- [x] Engine phase order preserves gameplay semantics and subsystem tick integrity.

## B. Test-derived atomic checklist

### Combat / movement rulebook & combat-time

- [x] `test_arena_stop_condition_stall`: Arena stop condition stall — Verify that the arena correctly detects lack of activity (STALL) as a telemetry report.
- [x] `test_stalemate_detection`: Stalemate detection.
- [x] `test_stalemate_loop_breaker_boosts_flee`: Stalemate loop breaker boosts flee.
- [x] `test_stalemate_detection_and_breaker`: Stalemate detection and breaker — Verify that 3 cycles of rhythmic oscillation trigger the stalemate breaker.
- [x] `test_high_ground_bonus`: High ground bonus — Verify High Ground bonus applies when attacker is on MOUNTAIN and defender is on FLOOR.
- [x] `test_flanking_bonus`: Flanking bonus — Verify Flanking bonus applies when defender is bracketed north/south.
- [x] `test_manhattan_distance`: Manhattan distance — Verify Manhattan distance calculation.
- [x] `test_orthogonal_adjacency`: Orthogonal adjacency — Verify that only orthogonal tiles are adjacent.
- [x] `test_check_range`: Check range — Verify range enforcement.
- [x] `test_check_occupancy`: Check occupancy — Verify 1-unit-per-tile occupancy rule.
- [x] `test_check_targeting_legality`: Check targeting legality — Verify consolidated targeting rules (Range + LOS).
- [x] `test_engagement_detection`: Engagement detection.
- [x] `test_engagement_clears_on_separation`: Engagement clears on separation.
- [x] `test_engagement_respects_hostility`: Engagement respects hostility.
- [x] `test_oa_triggered_on_disengagement`: Oa triggered on disengagement.
- [x] `test_target_stickiness_bias`: Target stickiness bias.
- [x] `test_passive_progression_on_quiet_tick`: Passive progression on quiet tick — Verify that biological decay and lifecycle systems run even if entity does not act.
- [x] `test_scenario_1_dead_world_progression`: Scenario 1 dead world progression — Scenario 1: No living entities. Verify tick still increments and systems advance.
- [x] `test_scenario_2_sleeping_world_biological_decay`: Scenario 2 sleeping world biological decay — Scenario 2: All entities have high next_act_at. Verify biological decay hits.
- [x] `test_scenario_4_subsystem_advancement`: Scenario 4 subsystem advancement — Scenario 4: Verify that registered subsystems receive the tick signal even if no actions apply.
- [x] `test_melee_striker_closes_distance`: Melee striker closes distance.
- [x] `test_tactical_retreat_at_low_hp`: Tactical retreat at low hp.
- [x] `test_movement_model_basic_path`: Movement model basic path.
- [x] `test_movement_model_yielding_priority`: Movement model yielding priority.

### Resource interaction / inventory / town loop

- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.
- [x] `test_visit_blacksmith_blocker_emission`: Visit blacksmith blocker emission — Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state.
- [x] `test_visit_blacksmith_crafting_resolution`: Visit blacksmith crafting resolution — Verify that crafting an item emits a strategic resolution for the corresponding material blocker.
- [x] `test_detour_suggestion_lifecycle_awareness`: Detour suggestion lifecycle awareness — Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones.
- [x] `test_biological_decay_authoritative`: Biological decay authoritative.
- [x] `test_sleep_goal_utility_at_night`: Sleep goal utility at night.
- [x] `test_inn_visit_leads_to_sleeping`: Inn visit leads to sleeping.
- [x] `test_sleeping_recovery_cycle`: Sleeping recovery cycle.
- [x] `test_difficulty_sets_level_range`: Difficulty sets level range — Entities in tier 3 should have level in [5, 10].
- [x] `test_race_level_in_range`: Race level in range.
- [x] `test_near_death_hardening`: Near death hardening — Verify that surviving at low HP increases Max HP.

### Strategic mind / cognition / projects / blockers / leads

- [x] `test_detour_breadth_limit`: Detour breadth limit.
- [x] `test_retry_suppression`: Retry suppression.
- [x] `test_project_retention_when_rival_is_below_margin`: Project retention when rival is below margin.
- [x] `test_project_switch_when_rival_is_above_margin`: Project switch when rival is above margin.
- [x] `test_switch_margin_increases_with_higher_resistance_profile`: Switch margin increases with higher resistance profile.
- [x] `test_lead_retention_is_capped_by_profile`: Lead retention is capped by profile.
- [x] `test_reserved_current_project_slot_is_used_when_current_project_exists`: Reserved current project slot is used when current project exists.
- [x] `test_dropped_candidate_counts_are_deterministic`: Dropped candidate counts are deterministic.
- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: Profile derivation is deterministic for same entity state.
- [x] `test_profile_derivation_does_not_use_rng`: Profile derivation does not use rng.
- [x] `test_populated_artifact_consistency`: Populated artifact consistency — Verify that a live HeadlessRunner execution produces populated and consistent artifacts.
- [x] `test_stable_concern_generation`: Stable concern generation.
- [x] `test_source_trust_learning_loop`: Source trust learning loop — Prove that future weighting is affected by source trust after a learning event.
- [x] `test_export_empty_strategy`: Export empty strategy — Verify export from an entity with no strategic state.
- [x] `test_export_with_core_strategic_state`: Export with core strategic state — Verify export of directives, projects, and objectives.
- [x] `test_export_determinism`: Export determinism — Verify that multiple exports from the same state are identical.
- [x] `test_non_mutation`: Non mutation — Verify that exporter does not mutate the source entity.
- [x] `test_strategic_state_defaults`: Strategic state defaults.
- [x] `test_strategic_state_serialization`: Strategic state serialization.
- [x] `test_strategic_pivot_on_regional_danger`: Strategic pivot on regional danger — Verify that heroes pivot from personal quests to regional stabilization during high-danger events.
- [x] `test_scar_detection`: Scar detection — Verify that heroes sense nearby world trauma/scars and investigate.
- [x] `test_near_death_triggers_survival_consequences`: Near death triggers survival consequences — Verify that a NEAR_DEATH event generates a concern and suspends the current project via applicator.
- [x] `test_betrayal_mutates_directives`: Betrayal mutates directives — Verify that a salient betrayal turning point adds an Avenge directive.
- [x] `test_betrayal_trauma_affects_recruitment`: Betrayal trauma affects recruitment — Verify that a recent betrayal makes entities less willing to accept recruitment offers.
- [x] `test_budget_enforcement_truncation`: Budget enforcement truncation — Verify that candidate_zone_limit correctly truncates the pool and preserves highest-scored zones.
- [x] `test_source_trust_behavioral_impact`: Source trust behavioral impact — Verify that updating source trust results in different weighting in the next cycle.
- [x] `test_directive_mutation_salience_threshold`: Directive mutation salience threshold — Verify that only high-salience turning points trigger mutations.
- [x] `test_directive_priority_strengthening`: Directive priority strengthening — Verify that repeated high-salience events strengthen directive priority.
- [x] `test_harness_non_determinism_different_seed`: Harness non determinism different seed — Verify that different seeds produce different outcomes.
- [x] `test_persistence_boost_prevents_switching`: Persistence boost prevents switching — Verify that the persistence boost prevents switching to a slightly better project.
- [x] `test_project_lock_prevents_switching`: Project lock prevents switching — Verify that project_lock_until strictly prevents any switches despite critical concerns.
- [x] `test_interruption_threshold_overridden_by_major_threat`: Interruption threshold overridden by major threat — Verify that a massive threat can overcome the interruption threshold.
- [x] `test_resume_restores_valid_objective`: Resume restores valid objective — Verify that brain restores the last active objective when resuming a project.
- [x] `test_objective_resume_reliability`: Objective resume reliability — Verify that a suspended objective is resumed correctly.
- [x] `test_strategic_update_idempotency_over_ticks`: Strategic update idempotency over ticks — Verify that applying the same update multiple times is idempotent.
- [x] `test_telemetry_strategic_metrics`: Telemetry strategic metrics — Verify that TelemetrySystem collects strategic metrics.
- [x] `test_biological_need_to_strategic_bias`: Biological need to strategic bias.
- [x] `test_directive_to_project_flow`: Directive to project flow.
- [x] `test_contradiction_degrades_certainty`: Contradiction degrades certainty — Verify that leads with contradictions lose certainty based on profile sensitivity.
- [x] `test_hypothesis_impacted_by_contradiction`: Hypothesis impacted by contradiction — Verify that hypotheses lose confidence when supporting leads are contradicted.
- [x] `test_concern_generation_near_death`: Concern generation near death.
- [x] `test_directive_mutation_near_death`: Directive mutation near death.
- [x] `test_project_mutation_interruption`: Project mutation interruption.

### Social / contracts / reputation / lived consequences

- [x] `test_betrayal_social_consequence`: Betrayal social consequence — Verify that private betrayal trauma prevents recruitment even for reputable founders.
- [x] `test_social_event_betrayal`: Social event betrayal — Verify that hitting an ally triggers a betrayal event and social bond shift.
- [x] `test_contract_outcome_consequences`: Contract outcome consequences — Verify that contract resolution returns correct intent updates for all members.
- [x] `test_role_aware_tactical_biases`: Role aware tactical biases — Verify that utility biases change based on contract role.
- [x] `test_memory_salience_retention`: Memory salience retention.
- [x] `test_combat_updates_social_registry`: Combat updates social registry.
- [x] `test_cha_impacts_familiarity_gain`: Cha impacts familiarity gain — Verify that a hero with higher CHA gains familiarity faster.

### Progression / classes / skills / attributes / rewards

- [x] `test_regional_suppression`: Regional suppression.
- [x] `test_undead_no_level_up`: Undead no level up — Undead should have a train_rate of 0.0 and never level up.
- [x] `test_milestone_level_up`: Milestone level up — Reaching a milestone like level 5 grants extra stats.
- [x] `test_physical_skill_scaling`: Physical skill scaling.
- [x] `test_magical_skill_scaling`: Magical skill scaling.
- [x] `test_elemental_skill_scaling`: Elemental skill scaling.

### World / entities / snapshot / determinism / engine authority

- [x] `test_snapshot_immutability_enforced`: Snapshot immutability enforced.
- [x] `test_snapshot_entities_are_deep_copied`: Snapshot entities are deep copied.
- [x] `test_snapshot_entities_are_frozen`: Snapshot entities are frozen.
- [x] `test_simulation_determinism`: Simulation determinism — Verify that two identical simulations with the same seed produce the same result.
- [x] `test_different_seeds_different_hashes`: Different seeds different hashes — Verify that different seeds produce different world states.
- [x] `test_entity_deep_copy_isolation`: Entity deep copy isolation — Verify that Entity.copy() provides absolute isolation for nested mutable structures.
- [x] `test_snapshot_actor_isolation`: Snapshot actor isolation — Verify that resolving an actor from a Snapshot ensures mutation safety.
- [x] `test_simulation_model_collection_freeze_list`: Simulation model collection freeze list — Verify that lists in SimulationModel become immutable after freeze.
- [x] `test_simulation_model_collection_freeze_dict`: Simulation model collection freeze dict — Verify that dicts in SimulationModel become immutable MappingProxy after freeze.
- [x] `test_world_state_freeze_guards`: World state freeze guards — Verify that WorldState prevents mutations after freeze.
- [x] `test_snapshot_deep_purity`: Snapshot deep purity — Verify that Snapshot entities and their nested aspects are recursively frozen.
- [x] `test_deep_freeze_nested_collections`: Deep freeze nested collections — Verify that freeze() recursively converts nested collections to immutable types.
- [x] `test_deep_freeze_idempotency`: Deep freeze idempotency — Verify that calling freeze() multiple times is safe.
- [x] `test_speed_delay_invariants`: Speed delay invariants — Test that speed_delay never returns NaN or out-of-bounds values.
- [x] `test_damage_calc_math`: Damage calc math — Test the core damage calculation logic in isolation.
- [x] `test_recalc_level_consistency`: Recalc level consistency — Ensure level-based stat recalculation remains consistent across aspects.
- [x] `test_combat_damage_invariants`: Combat damage invariants — Ensure HP reduction application does not cause overflow or invalid states.

### Unclassified-but-included RPG-core tests

- [x] `test_intel_capacity_determinism`: Intel capacity determinism — Verify that identical seeds produce identical cognitive profiles and artifacts.
- [x] `test_intel_capacity_detour_depth_hardbound`: Intel capacity detour depth hardbound — Verify that detour depth is capped in artifacts even under pressure.
- [x] `test_cognition_api_serialization`: Cognition api serialization — Verify that cognitive metrics are correctly serialized for the API.
- [x] `test_milestone_4_social_filtering`: Milestone 4 social filtering — Verify that social candidate selection filters hostiles and uses debt.
- [x] `test_strategic_uncertainty_and_anti_cheating`: Strategic uncertainty and anti cheating — Verify that rumors have lower certainty and vague leads do not cheat with perfect coords.
- [x] `test_source_trust_recalibration`: Source trust recalibration — Verify that a false lead outcome reduces source trust.
- [x] `test_strategy_observability_consistency`: Strategy observability consistency — Verify that a strategic shift is consistently observable across all surfaces.
- [x] `test_strategic_decision_driver_traceability`: Strategic decision driver traceability — Verify that DecisionDriver records flow from AIBrain to the entity state.
- [x] `test_recruitment_offer_evaluation_acceptance`: Recruitment offer evaluation acceptance — Verify candidate accepts a fair offer from a trusted friend.
- [x] `test_life_stage_priority_shift`: Life stage priority shift — Verify level 1 and level 25 entities have different goal preferences.
- [x] `test_belief_refresh_captures_apparent_state`: Belief refresh captures apparent state.
- [x] `test_belief_decay_lifecycle`: Belief decay lifecycle.
- [x] `test_threat_estimation_logic`: Threat estimation logic.
- [x] `test_emotional_bias_on_utility`: Emotional bias on utility — Verify DREAD increases FLEE utility and decreases EXPLORE utility.
- [x] `test_flanking_bonus`: Flanking bonus.
- [x] `test_narrative_memory_trauma_biasing`: Narrative memory trauma biasing.
- [x] `test_narrative_memory_victory_confidence`: Narrative memory victory confidence.
- [x] `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap.
- [x] `test_training_uses_aptitudes`: Training uses aptitudes.
- [x] `test_aging_and_death`: Aging and death.
- [x] `test_routine_service_sleep_bias`: Routine service sleep bias.
- [x] `test_routine_service_hunger_bias`: Routine service hunger bias.
- [x] `test_dynamic_liberate_quest`: Dynamic liberate quest.
- [x] `test_entity_evolution_transformation`: Entity evolution transformation — Verify that a goblin evolves into a warrior/scout when hitting level cap.

# Legacy src Add-On Checklist

## A. CLI and entrypoint compatibility

- [x] `python -m src` defaults to server mode when no subcommand is provided.
- [x] `python -m src serve` accepts the original `--host`, `--port`, `--seed`, `--entities`, `--workers`, `--log-level` arguments.
- [x] `python -m src cli` accepts the original `--ticks`, `--entities`, `--seed`, `--workers`, `--grid-width`, `--grid-height`, `--replay`, `--log-level` arguments.
- [x] `python -m src inspect` accepts the original `--id`, `--seed`, `--ticks`, `--entities`, `--workers`, `--log-level` arguments.
- [x] CLI argument defaults remain compatible with legacy expectations.
- [x] Invalid CLI arguments fail in a controlled, parser-driven way.
- [x] CLI replay-file argument writes to the expected output path semantics.
- [x] CLI startup still wires logging before engine loop execution.
- [x] CLI shutdown still tears down worker infrastructure cleanly after simulation.

## B. Optional-broker disabled-mode compatibility

- [x] `DISABLE_RABBITMQ=1` causes RabbitMQ client code to enter explicit disabled mode.
- [x] RabbitMQ client imports do not crash when disabled.
- [x] RabbitMQ disabled-mode behavior remains safe even when broker libraries are missing.
- [x] `DISABLE_KAFKA=1` causes Kafka client code to enter explicit disabled mode.
- [x] Kafka client imports do not crash when disabled.
- [x] Headless runner imports still succeed when optional brokers are disabled.
- [x] Import-time behavior does not accidentally force broker setup.

## C. Worker-pool and infrastructure fallback behavior

- [x] Worker pool falls back to inline/local execution when broker transport is unavailable.
- [x] Worker pool does not require live RabbitMQ/Kafka to execute local simulation behavior.
- [x] Worker fallback preserves deterministic ordering expectations in local mode.
- [x] Worker shutdown remains safe after fallback execution paths.
- [x] Missing broker infrastructure does not block minimal simulation startup.

## E. Replay compatibility outside pure RPG-core semantics

- [x] Replay files are written in the expected legacy location/format semantics for headless runs.
- [x] Replay snapshots preserve deterministic entity ordering and field availability where legacy tests rely on them.
- [x] Replay can support structural comparison between repeated runs with same seed.
- [x] Same seed and equivalent configuration produce identical replay-visible state across runs.
- [x] Different seeds produce divergent replay-visible state.

## F. Structured logging compatibility

- [x] CLI stdout logs remain valid JSON line-by-line.
- [x] `timestamp`
- [x] `level`
- [x] `message`
- [x] `component`
- [x] Log output remains machine-parseable under normal CLI execution.
- [x] World-loop logs include tick context.
- [x] World-loop logs preserve identifiable component naming.
- [x] Worker-pool logs preserve identifiable component naming where emitted.
- [x] Main entrypoint logs preserve identifiable `__main__` or equivalent component identity.

## G. Metrics and monitoring compatibility

- [x] Metrics do not rely on broker-only paths if local/headless execution is supposed to work without brokers.

## H. API protocol and transport compatibility

- [x] MessagePack handshake mode remains supported.
- [x] GZip middleware or equivalent response compression remains functional for large metadata responses.
- [x] Compression support does not break standard metadata endpoint access.

## J. Infrastructure-side unhappy path compatibility

- [x] Missing broker dependencies do not block headless runner imports.

# Part 6 Additive Missing Logic

## A. Perception / belief / appraisal / attention

- [x] `test_belief_refresh_captures_apparent_state`: belief refresh from apparent state
- [x] `test_belief_decay_lifecycle`: belief decay lifecycle
- [x] `test_threat_estimation_logic`: threat estimation logic

## B. Routine / motive / biological needs / life rhythm

- [x] `test_sleep_goal_utility_at_night`: sleep utility at night
- [x] `test_routine_service_sleep_bias`: sleep bias
- [x] `test_routine_service_hunger_bias`: hunger bias
- [x] `test_inn_visit_leads_to_sleeping`: inn visit leads to sleeping
- [x] `test_sleeping_recovery_cycle`: sleeping recovery cycle

## D. Emotional / narrative memory / trauma logic

- [x] `test_emotional_bias_on_utility`: emotion changes utility
- [x] `test_narrative_memory_trauma_biasing`: trauma memory biasing
- [x] `test_narrative_memory_victory_confidence`: victory-confidence memory

## E. Combat aftermath / wounds / scars / stamina / exhaustion

- [x] `test_scar_detection`: scar detection

## F. Tactical specialty / action style / combo behavior

- [x] `test_flanking_bonus`: flanking bonus

## H. Region-scale strategic and world consequences

- [x] `test_regional_suppression`: regional suppression
- [x] `test_strategic_pivot_on_regional_danger`: pivot on regional danger

## I. Death / permadeath / succession / heirlooms / nemesis

- [x] `test_aging_and_death`: aging and death
- [x] `test_near_death_triggers_survival_consequences`: near-death survival consequences
- [x] `test_near_death_hardening`: near-death hardening

# Part 7 Residual Test-Covered Logic

## A. Quest lifecycle, generation, and completion logic

- [x] `test_generate_quest_respects_level`: generated quests respect level banding
- [x] `test_generate_quest_gold_scales_with_level`: quest gold reward scales with level
- [x] `test_dynamic_liberate_quest`: liberate-quest generation/progression works

## C. Role derivation and role-aware behavior

- [x] `test_role_bias_influence`: role bias affects decisions as expected
- [x] `test_role_aware_tactical_biases`: tactical behavior reflects role-aware biasing

## D. Aptitudes, training-detail law, and stat recomputation

- [x] `test_training_uses_aptitudes`: aptitude-weighted training law is preserved

## G. Travel topology, path-affordance, and regional traversal law

- [x] `test_difficulty_sets_level_range`: region difficulty sets level range correctly

# Part 8 Assumption / Invariant Checklist

## A. Default-state and neutral-behavior assumptions

- [x] `test_export_empty_strategy`: exporting empty strategy state is safe

## D. Serialization, schema, and round-trip assumptions

- [x] `test_cognition_api_serialization`: cognition API serialization is preserved

## E. Freeze, immutability, and deep-isolation assumptions

- [x] `test_entity_deep_copy_isolation`: deep-copy isolation is preserved
- [x] `test_deep_freeze_nested_collections`: deep freeze handles nested collections
- [x] `test_deep_freeze_idempotency`: deep freeze is idempotent
- [x] `test_world_state_freeze_guards`: world-state freeze guards are preserved
- [x] `test_simulation_model_collection_freeze_list`: list freezing behavior is preserved
- [x] `test_simulation_model_collection_freeze_dict`: dict freezing behavior is preserved
- [x] `test_non_mutation`: non-mutation guarantee is preserved

## F. Determinism and repeatability assumptions

- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: deterministic profile derivation
- [x] `test_intel_capacity_determinism`: intelligence-capacity determinism is preserved

## H. Safe fallback and degraded-mode assumptions

- [x] `test_worker_pool_fallback_to_inline`: worker pool falls back to inline execution
- [x] `test_headless_runner_importable_without_brokers`: headless runner imports safely without brokers
- [x] `test_simulation_step_runs_without_brokers`: simulation can step without brokers

## I. Caps, clamps, floors, ceilings, and boundedness assumptions

- [x] `test_level_up_respects_cap`: level-up cap compliance is preserved

## J. Precedence, selection, and ordering assumptions

- [x] `test_reserved_current_project_slot_is_used_when_current_project_exists`: current-project reserved slot law is preserved
