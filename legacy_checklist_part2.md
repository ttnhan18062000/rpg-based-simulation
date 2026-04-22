### Strategic mind / cognition / projects / blockers / leads

#### `ai/test_bounded_blockers.py`

- [ ] `test_accurate_diagnosis_high_wisdom`: Accurate diagnosis high wisdom.
- [ ] `test_misdiagnosis_low_wisdom`: Misdiagnosis low wisdom.

#### `ai/test_bounded_detours.py`

- [x] `test_detour_breadth_limit`: Detour breadth limit.
- [x] `test_detour_depth_limit_fallback`: Detour depth limit fallback.
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
- [x] `test_concern_intake_is_capped_by_profile`: Concern intake is capped by profile.
- [x] `test_lead_retention_is_capped_by_profile`: Lead retention is capped by profile.
- [ ] `test_reserved_current_project_slot_is_used_when_current_project_exists`: Reserved current project slot is used when current project exists.
- [ ] `test_dropped_candidate_counts_are_deterministic`: Dropped candidate counts are deterministic.

#### `ai/test_cognition_capacity_determinism.py`

- [x] `test_profile_derivation_is_deterministic_for_same_entity_state`: Profile derivation is deterministic for same entity state.
- [ ] `test_profile_derivation_is_independent_of_tick_in_milestone_1`: Profile derivation is independent of tick in milestone 1.
- [ ] `test_profile_derivation_does_not_use_rng`: Profile derivation does not use rng.

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
- [ ] `test_populated_artifact_consistency`: Populated artifact consistency — Verify that a live HeadlessRunner execution produces populated and consistent artifacts. [TRACK 1 HARDENING].
- [ ] `test_truth_surface_parity`: Truth surface parity — Verify that Replay, API Schema, and Cognition Graph maintain strict parity. [TRUTH SURFACE OWNERSHIP PROOF].
- [ ] `test_documentation_alignment`: Documentation alignment — Verify that documented fields in intel_capacity_implementation_updated.md are real. [MILESTONE 8 PROOF].

#### `ai/test_directive_mutation_thresholds.py`

- [ ] `test_directive_mutation_thresholds`: Directive mutation thresholds — Verify that directives only mutate after repeated thresholded events..

#### `ai/test_event_interpretation.py`

- [x] `test_stable_concern_generation`: Stable concern generation.
- [x] `test_unstable_panic_concern`: Unstable panic concern.
- [x] `test_interruption_resistance_stable`: Interruption resistance stable.
- [x] `test_interruption_resistance_unstable`: Interruption resistance unstable.
- [ ] `test_identity_drift_resistance`: Identity drift resistance.
- [ ] `test_rumor_sensitivity_unstable`: Rumor sensitivity unstable.

#### `ai/test_lead_learning.py`

- [x] `test_learning_success`: Learning success.
- [x] `test_learning_failure`: Learning failure.

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
- [ ] `test_strategic_state_defaults`: Strategic state defaults.
- [ ] `test_strategic_state_serialization`: Strategic state serialization.

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

- [ ] `test_budget_enforcement_truncation`: Budget enforcement truncation — Verify that candidate_zone_limit correctly truncates the pool AND preserves highest-scored zones..
- [ ] `test_source_trust_behavioral_impact`: Source trust behavioral impact — Verify that updating source trust results in different weighting in the next cycle. [MILESTONE 3].
- [ ] `test_overload_metrics_visibility`: Overload metrics visibility — Verify that primary_overload_source and metrics are populated when stressed..

#### `integration/strategy/test_strategic_continuity.py`

- [x] `test_directive_mutation_salience_threshold`: Directive mutation salience threshold — Verify that only high-salience turning points trigger mutations..
- [x] `test_directive_priority_strengthening`: Directive priority strengthening — Verify that repeated high-salience events strengthen directive priority..

#### `integration/strategy/test_strategic_continuity_hardening.py`

- [ ] `test_strategic_objective_continuity`: Strategic objective continuity — Prove that an existing objective is preserved if the project remains stable and no high blockers appear..
- [ ] `test_objective_resumption_aligns_with_tactical`: Objective resumption aligns with tactical — Verify that a resumed objective correctly drives goal selection..

#### `integration/strategy/test_strategic_determinism.py`

- [x] `test_harness_determinism`: Harness determinism — Verify that two runs with the same seed produce byte-identical results..
- [ ] `test_harness_non_determinism_different_seed`: Harness non determinism different seed — Verify that different seeds produce different outcomes (basic sanity check)..

#### `integration/strategy/test_strategic_explainability.py`

- [ ] `test_candidate_zone_enforcement`: Candidate zone enforcement — Verify that candidate_zone_limit is enforced and drops excess zones..
- [ ] `test_ally_evaluation_enforcement`: Ally evaluation enforcement — Verify that ally_evaluation_limit caps contracts and offers evaluated..
- [ ] `test_overload_source_trauma`: Overload source trauma — Verify that heavy HP damage triggers 'trauma' as the primary overload source..
- [ ] `test_switch_reason_transparency`: Switch reason transparency — Verify that a project switch provides a human-readable reason..

#### `integration/strategy/test_strategic_persistence.py`

- [ ] `test_persistence_boost_prevents_switching`: Persistence boost prevents switching — Verify that the persistence boost prevents switching to a slightly better project..
- [x] `test_project_lock_prevents_switching`: Project lock prevents switching — Verify that project_lock_until strictly prevents any switches despite critical concerns..
- [x] `test_interruption_threshold_overridden_by_major_threat`: Interruption threshold overridden by major threat — Verify that a massive threat CAN overcome the interruption threshold..
- [ ] `test_strategic_pipeline_home_threat`: Strategic pipeline home threat — Verify the flow from life event through StrategicConsequenceService to project pivot..
- [x] `test_resume_restores_valid_objective`: Resume restores valid objective — Verify that brain restores the last active objective when resuming a project. [Strategy M2].
- [ ] `test_resumed_objective_survives_cycle`: Resumed objective survives cycle — Verify that a restored objective doesn't immediately flip back to ProjectRecord.objectives[0] if it matches. [Strategy M2].

#### `integration/strategy/test_strategic_replay_determinism.py`

- [x] `test_world_strategic_registry_deep_isolation`: World strategic registry deep isolation — Verify that WorldStrategicRegistry.copy() performs a deep copy..
- [x] `test_strategic_replay_graph_equality`: Strategic replay graph equality — Verify that replaying from a snapshot yields bit-identical cognition graphs..
- [ ] `test_lead_outcome_grounding_verification`: Lead outcome grounding verification — Verify that precise leads correctly ground into world entities..

#### `integration/strategy/test_strategic_resume_objective.py`

- [ ] `test_objective_resume_reliability`: Objective resume reliability — Verify that a suspended objective is resumed correctly..

#### `integration/strategy/test_strategic_structural_integrity.py`

- [x] `test_snapshot_strategic_isolation`: Snapshot strategic isolation — Verify that Snapshot.from_world deep-copies and freezes strategic state..
- [ ] `test_strategic_update_merging_identical_ids`: Strategic update merging identical ids — Verify that ActionSystem merges updates with identical IDs correctly..
- [x] `test_serialization_round_trip`: Serialization round trip — Verify that StrategicState survives full JSON serialization round-trip..
- [ ] `test_strategic_update_coercion_from_dict`: Strategic update coercion from dict — Verify that StrategicUpdate correctly coerces dicts to models (worker transport emulation)..

#### `integration/strategy/test_strategic_transport.py`

- [ ] `test_strategic_update_multi_record_transport`: Strategic update multi record transport — Verify that a single proposal can carry multiple strategic updates..
- [ ] `test_strategic_update_repeated_id_last_one_wins`: Strategic update repeated id last one wins — Verify that repeated IDs in a single update follow last-one-wins semantics..
- [ ] `test_strategic_update_idempotency_over_ticks`: Strategic update idempotency over ticks — Verify that applying the same update multiple times is idempotent..
- [ ] `test_strategic_update_target_routing`: Strategic update target routing — Verify that strategic updates can be routed to a target entity..

#### `integration/strategy/test_strategic_world_integration.py`

- [ ] `test_world_strategic_registry_persistence`: World strategic registry persistence — Verify that WorldStrategicRegistry is preserved in snapshots..
- [ ] `test_strategic_world_integration_system_pruning`: Strategic world integration system pruning — Verify that the system prunes expired world opportunities..
- [ ] `test_telemetry_strategic_metrics`: Telemetry strategic metrics — Verify that TelemetrySystem collects strategic metrics..

#### `unit/ai/strategy/test_strategic_biasing.py`

- [ ] `test_biological_need_to_strategic_bias`: Biological need to strategic bias.
- [ ] `test_directive_to_project_flow`: Directive to project flow.
- [ ] `test_strategic_bias_impact_on_selection`: Strategic bias impact on selection.

#### `unit/ai/strategy/test_strategic_uncertainty.py`

- [x] `test_contradiction_degrades_certainty`: Contradiction degrades certainty — Verify that leads with contradictions lose certainty based on profile sensitivity. [MILESTONE 5].
- [x] `test_hypothesis_impacted_by_contradiction`: Hypothesis impacted by contradiction — Verify that hypotheses lose confidence when supporting leads are contradicted. [MILESTONE 5].

#### `unit/ai/strategy/test_blocker_resolution.py`

- [x] `test_blocker_material_resolution`: Blocker material resolution — Verify that adding missing materials to inventory resolves associated 'material' blockers..
- [x] `test_blocker_access_resolution`: Blocker access resolution — Verify that reaching a target location resolves 'access' blockers..
- [x] `test_blocker_re_triggering`: Blocker re triggering — Verify that losing a material re-triggers the blocker..

original evidence: `unit/ai/strategy/test_blocker_resolution.py`
`src_v2` evidence: `src_v2/systems/strategic.py`
divergence note: v2 converges blocker resolution into the `StrategicIntelligenceSystem` within the authoritative tick resolution phase.
proof path: `tests_v2/contract/test_resource_intelligence_contract.py`

#### `unit/strategy/test_strategic_services.py`

- [ ] `test_canonical_blocker_structure`: Canonical blocker structure — Verify that StrategicState has a blockers list and ObjectiveRecord uses IDs..
- [ ] `test_strategic_snapshot_isolation`: Strategic snapshot isolation — Verify that deep copying an entity results in a fully isolated strategic tree..
- [x] `test_belief_decay_aoa_purity`: Belief decay aoa purity — Verify that BeliefService.decay_stale_beliefs returns an update and does not mutate in-place..
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
- [x] `test_intel_refutation_by_exhaustion`: Intel refutation by exhaustion — Verify that failing to find a target refutes the lead and drops trust..

#### `core/test_lived_models.py`

- [ ] `test_routine_profile_instantiation`: Routine profile instantiation — Verify RoutineProfile can be instantiated with hybrid scheduling..
- [ ] `test_place_attachment_instantiation`: Place attachment instantiation — Verify PlaceAttachment can be instantiated and supports sentiment..
- [ ] `test_group_record_instantiation`: Group record instantiation — Verify GroupRecord supports shared tactical intent..
- [ ] `test_entity_integration`: Entity integration — Verify Entity and IdentityAspect absorb new Phase 3 fields..
- [ ] `test_world_state_registry`: World state registry — Verify GroupRegistry integration in WorldState..

#### `integration/gameplay/test_social_meaning.py`

- [ ] `test_social_event_betrayal`: Social event betrayal — Verify that hitting an ally triggers a betrayal event and social bond shift..
- [ ] `test_social_event_near_death_and_tp`: Social event near death and tp — Verify that a near-death experience creates a durable turning point..
- [ ] `test_social_event_first_kill_milestone`: Social event first kill milestone — Verify that first kill increments reputation and notoriety..

#### `test_phase_3_social_contracts.py`

- [ ] `test_recruitment_haggling_threshold`: Recruitment haggling threshold — Verify that candidates counter-offer when willingness is close to threshold..
- [ ] `test_contract_outcome_consequences`: Contract outcome consequences — Verify that contract resolution returns correct intent updates for all members..
- [ ] `test_role_aware_tactical_biases`: Role aware tactical biases — Verify that utility biases change based on contract role..

#### `unit/ai/test_social.py`

- [ ] `test_inn_gossip`: Inn gossip.
- [ ] `test_hero_trading`: Hero trading.

#### `unit/ai/strategy/test_lead_generation.py`

- [x] `test_lead_generation_from_blocker`: Lead generation from blocker — Verify that a blocker without a known location generates a 'location' lead..
- [ ] `test_lead_deduplication`: Lead deduplication — Ensure same clue doesn't create duplicate leads..

original evidence: `unit/ai/strategy/test_lead_generation.py`
`src_v2` evidence: `src_v2/systems/strategic.py`
divergence note: Lead generation is currently baseline-only in Phase 5.
proof path: `tests_v2/contract/test_resource_intelligence_contract.py`

#### `unit/ai/test_social_integration.py`

- [ ] `test_social_bias_on_goal_scoring`: Social bias on goal scoring — Verify that a high-trust bond increases SOCIAL goal score..
- [ ] `test_reputation_impact_on_caution`: Reputation impact on caution — Verify low global reputation triggers defensive posture in cautious entities..

#### `unit/core/gameplay/test_npc_contracts.py`

- [ ] `test_npc_loadout_integrity`: Npc loadout integrity — Verify that specific NPC tiers are assigned their canonical equipment..
- [ ] `test_npc_kind_mapping_integrity`: Npc kind mapping integrity — Verify that race/tier combinations map to the correct semantic kind name..

#### `unit/core/models/test_social_milestones.py`

- [ ] `test_nemesis_milestone_creation`: Nemesis milestone creation.
- [ ] `test_memory_salience_retention`: Memory salience retention..

#### `unit/core/models/test_social_registry_updates.py`

- [ ] `test_combat_updates_social_registry`: Combat updates social registry.
- [ ] `test_archetype_influence_on_social_deltas`: Archetype influence on social deltas.

#### `unit/ai/strategy/test_social_recruitment.py`

- [ ] `test_recruitment_necessity_evaluation`: Recruitment necessity evaluation — Verify that a blocker with 'group' requirement triggers recruitment intention..
- [ ] `test_candidate_viability_check`: Candidate viability check — Ensure recruiter skips hostile or incapable candidates..

original evidence: `unit/ai/strategy/test_social_recruitment.py`
`src_v2` evidence: `N/A`
divergence note: Social recruitment is unsupported in Phase 5.
proof path: N/A

#### `unit/strategy/test_social_reasoning_bounding.py`

- [ ] `test_recruitment_offer_bounding_stable`: Recruitment offer bounding stable — Stable entities produce consistent offers without noise..
- [ ] `test_recruitment_offer_bounding_unstable`: Recruitment offer bounding unstable — Unstable entities produce noisy/perturbed offers..

#### `unit/systems/test_familiarity_scaling.py`

- [x] `test_cha_impacts_familiarity_gain`: Cha impacts familiarity gain — Verify that a hero with higher CHA gains familiarity faster..
