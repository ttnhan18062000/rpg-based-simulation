# Legacy `src` RPG-Core Checklist — Part 7 (Residual Test-Covered Logic)

This checklist is additive to Parts 1–6.

It exists to capture smaller but still real legacy logic families that are explicitly covered by tests and are easy to lose if they remain implicit under broad labels like strategy, progression, or world behavior.

This part should stay test-first. If a behavior is listed here, it should have an identifiable test anchor in the original legacy test surface.

---

## A. Quest lifecycle, generation, and completion logic

Relevant legacy test surface includes quest creation, progression, duplicate suppression, completion, rewards, and quest-type-specific behavior.

- [x] `test_quest_creation`: quest creation baseline
- [x] `test_quest_advance`: quest progression increments correctly
- [x] `test_quest_advance_does_nothing_when_completed`: completed quests do not advance further
- [x] `test_quest_progress_ratio`: progress-ratio computation is correct
- [x] `test_generate_quest_returns_quest`: quest generator returns valid quest object
- [x] `test_generate_quest_respects_level`: generated quests respect level banding
- [x] `test_generate_quest_skips_duplicate`: duplicate quest generation is suppressed
- [x] `test_generate_quest_gold_scales_with_level`: quest gold reward scales with level
- [x] `test_generate_explore_quest`: explore-quest generation works
- [x] `test_hunt_quest_completion_awards_rewards`: hunt-quest completion awards rewards
- [x] `test_explore_quest_completes_near_target`: explore-quest completes near target
- [x] `test_gather_quest_advance`: gather-quest progression works
- [x] `test_dynamic_liberate_quest`: liberate-quest generation/progression works
- [x] `test_territory_conquest`: territory-conquest quest/world objective behavior is preserved

---

## B. Trait system logic

Relevant legacy test surface includes trait definitions, trait assignment, trait aggregation, compatibility, and serialization.

- [x] `test_trait_serialization`: trait serialization is preserved
- [x] `test_get_traits`: trait retrieval works
- [x] `test_trait_defs_not_empty`: trait definitions exist and are non-empty
- [x] `test_with_traits_assigns_traits`: explicit trait assignment works
- [x] `test_no_traits_by_default`: no-trait default behavior is preserved
- [x] `test_traits_with_different_race_prefix`: race-prefixed trait handling is preserved
- [x] `test_empty_traits_returns_zero_bonus`: empty-trait bonus behavior is preserved
- [x] `test_single_known_trait`: single-trait bonus behavior is preserved
- [x] `test_multiple_traits_sum`: multiple traits stack/sum correctly
- [x] `test_unknown_trait_id_ignored`: unknown traits are ignored safely
- [x] `test_same_trait_compatible`: trait compatibility logic is preserved
- [x] `test_assigns_between_2_and_4_traits`: random/default trait assignment count is preserved
- [x] `test_all_assigned_traits_are_valid`: assigned traits are always valid
- [x] `test_all_trait_types_have_definitions`: all trait types have definitions
- [x] `test_trait_defs_have_all_utility_fields`: trait utility fields are complete
- [x] `test_trait_defs_have_all_stat_fields`: trait stat fields are complete

---

## C. Role derivation and role-aware behavior

Relevant legacy test surface includes role derivation, role transition, role biasing, and tactical role-awareness.

- [x] `test_initial_role_derivation`: initial role derivation is preserved (StrategicIntelligenceSystem)
- [x] `test_dynamic_role_transition_with_hysteresis`: dynamic role transition with hysteresis is preserved
- [x] `test_role_bias_influence`: role bias affects decisions as expected (RoutineService)
- [x] `test_role_aware_tactical_biases`: tactical behavior reflects role-aware biasing

---

## D. Aptitudes, training-detail law, and stat recomputation

Relevant legacy test surface includes aptitude-driven training, soft caps, fractional accumulation, and recomputation of derived stats.

- [x] `test_training_uses_aptitudes`: aptitude-weighted training law is preserved
- [x] `test_innate_talents_training`: innate talents affect training as expected
- [x] `test_training_does_not_exceed_cap`: training respects hard caps
- [x] `test_training_accumulates_fractionally`: fractional training accumulation is preserved
- [x] `test_training_updates_stats_on_increment`: stat update on training increment is preserved
- [x] `test_specialized_training_soft_caps`: soft-cap behavior for specialized training is preserved
- [x] `test_output_derived_stat_ceilings`: derived-stat ceiling logic is preserved
- [x] `test_stat_recalculation`: stat recomputation behavior is preserved
- [x] `test_attribute_scaling_overlap`: overlapping attribute-scaling law is preserved

---

## E. Place attachment, home, and anchored behavior

Relevant legacy test surface includes place attachment, home behavior, home storage, retreat-to-home behavior, and home-driven actions.

- [x] `test_place_attachment_instantiation`: place attachment can be instantiated
- [x] `test_place_attachment_navigation`: place attachment influences navigation correctly
- [x] `test_place_attachment_home_navigation`: home-oriented navigation behavior is preserved
- [x] `test_no_home_returns_false`: no-home logic is preserved
- [x] `test_home_sets_home_pos`: home position assignment is preserved
- [x] `test_entity_copy_includes_home_storage`: home storage is preserved during copy
- [x] `test_entity_without_home_storage`: no-home-storage case is preserved
- [x] `test_divergent_home_response`: divergent home response behavior is explicit and preserved where intended
- [x] `test_home_priority_retreat`: home-priority retreat behavior is preserved
- [x] `test_visit_home_upgrade_resolution`: visit-home upgrade resolution is preserved
- [x] `test_home_visit_leads_to_eating`: home visit can lead to eating behavior

---

## F. Leash, camp, and local anchored ecology

Relevant legacy test surface includes leash behavior, chase abandonment, camp return, and camp reinforcement logic.

- [x] `test_no_leash_returns_false`: no-leash detection behavior is preserved
- [x] `test_mob_beyond_leash_returns_to_camp`: beyond-leash return-to-camp behavior is preserved
- [x] `test_mob_within_leash_wanders_normally`: within-leash wandering behavior is preserved
- [x] `test_no_leash_mob_wanders_freely`: leash-free wandering behavior is preserved
- [x] `test_chase_beyond_leash_abandons`: chase abandonment beyond leash is preserved
- [x] `test_chase_within_leash_continues`: chase continuation within leash is preserved
- [x] `test_no_leash_mob_hunts_freely`: no-leash hunting freedom is preserved
- [x] `test_camp_reinforcements`: camp reinforcement behavior is preserved

---

## G. Travel topology, path-affordance, and regional traversal law

Relevant legacy test surface includes flow fields, terrain costs, roads, bridges, biome affordances, and difficulty-zone traversal constraints.

- [x] `test_flow_field_basic_navigation`: basic flow-field navigation is preserved
- [x] `test_flow_field_respects_terrain_cost`: terrain-cost-sensitive navigation is preserved
- [x] `test_flow_field_smoothing`: flow-field smoothing is preserved
- [x] `test_flow_field_smoothing_normalization`: smoothing normalization behavior is preserved
- [x] `test_navigation_uses_flow_field_for_far_town`: far-town navigation uses flow fields
- [x] `test_navigation_uses_flow_field_for_world_boss`: world-boss navigation uses flow fields
- [x] `test_road_cost_is_low`: road traversal cost law is preserved
- [x] `test_prefers_road_over_swamp`: road preference over swamp is preserved
- [x] `test_each_biome_has_road_network`: biome road-network presence is preserved
- [x] `test_road_connects_locations`: road connectivity behavior is preserved
- [x] `test_bridges_placed_over_water`: bridge placement over water is preserved
- [x] `test_all_four_biomes_have_features`: biome feature presence is preserved
- [x] `test_difficulty_sets_level_range`: region difficulty sets level range correctly
- [x] `test_gold_scales_with_difficulty`: difficulty-linked gold scaling is preserved
- [x] `test_in_region_returns_difficulty`: region difficulty query logic is preserved
- [x] `test_difficulty_zones_defined`: difficulty-zone definition is preserved
- [x] `test_lava_only_at_high_difficulty`: lava/high-difficulty coupling is preserved
- [x] `test_all_terrains_have_names`: terrain naming coverage is preserved
- [x] `test_all_terrains_have_race_labels`: terrain race-label coverage is preserved

---

## H. Cooperation, recruitment-adjacent coordination, and proximity bonding

Relevant legacy test surface includes small cooperative and bonding behaviors that affect social or local-world outcomes.

- [x] `test_cooperation_recruitment_logic`: cooperation in recruitment/social choice is preserved
- [x] `test_scenario_3_stationary_world_proximity_bonding`: proximity bonding behavior is preserved

---

## I. Residual small-world and economy-adjacent local realism

Relevant legacy test surface includes local inventory and burden realism that can affect action outcomes.

- [x] `test_full_bag_aborts_looting`: full-bag looting abort is preserved
- [x] `test_overweight_aborts_looting`: overweight looting abort is preserved
- [x] `test_near_weight_limit_penalizes_loot`: near-limit loot penalty is preserved

These are listed again here intentionally if not already fully owned elsewhere, because they are small and easy to lose.

---

## J. Mapping guidance for roadmap ownership

This section is governance-only.

Use this part to map residual logic into roadmap phases:

- [x] Phase 8 owns:
  - leash/camp/local anchored ecology
  - local burden/loot-abort realism
  - local/path-affordance pieces only where they directly affect immediate tactics

- [x] Phase 9 owns:
  - quests
  - traits
  - roles
  - aptitude/training-detail law
  - place attachment/home behavior when it affects long-horizon choices
  - regional traversal/topology when it affects world-scale intention
  - cooperation/proximity bonding

- [x] No Part 7 item should be left implicit under a generic bucket like “AI improvements” or “progression tuning”

---

## Completion rule for Part 7

A Part 7 item is not considered covered merely because it “probably exists” inside a broader subsystem.

Each item should be considered closed only when:

- [x] the specific legacy behavior has a clear roadmap owner
- [x] the specific behavior has a direct implementation or explicit divergence decision
- [x] the specific behavior has test coverage or parity justification
- [x] the replacement ledger/support boundary reflects the truth of that item
