---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS
artifact_type: plan
tags: [simulation-quality, observability, world]
---

# Plan — TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS

## New files

1. **`config/simulation_quality/entity_lifecycle_weights.yaml`** (data-driven thresholds, matching
   `quality_scoring_contract.md` §4.8's convention — no numeric literals in the tool's own code):
   ```yaml
   minimum_sample_threshold: 6       # path_length floor for trusting entropy/loop/conclusion metrics
   stall_detector_window_ticks: 300  # mirrors capability_growth_stalled's own real window (progression.py)
   life_arc_generation_threshold: 2  # mirrors life_arc_incoherent's own real threshold
   clustering_similarity_threshold: 0.85  # bigram-Jaccard cutoff for "near-duplicate path" pairs
   default_obs_mode: NORMAL
   lifecycle_phase_buckets:
     VITALS: [biological_state_changed, stamina_changed, wound_sustained, wound_healed, scar_gained]
     GROWTH_PROGRESSION: [attribute_changed, xp_granted, level_up, skill_unlocked, trait_expressed,
       pillar_trait_unlocked, recipe_learned, skill_cooldown_started, item_equipped, item_unequipped,
       equipment_durability_changed, progression_conversion_applied, capability_growth_stalled,
       life_arc_incoherent, progression_plateau_detected]
     EXPLORATION: [movement, resource_harvested]
     COMBAT: [combat_damage, combat_initiated, combat_kill, hazard_drain_applied, near_death_survival,
       combat_hard_law_violation, raid_party_spawned]
     ECONOMY: [shop_transaction, trade_executed, quest_reward_dispensed, gold_sink_fired,
       gold_transaction, paid_information_transaction, paid_info_transaction, conservation_law_verified]
     SOCIAL: [social_memory_created, reputation_delta, contract_offer_created, contract_offer_accepted,
       contract_completed, contract_lapsed, contract_expired_offer, contract_milestone_completed,
       group_joined, group_expelled]
     STRATEGY_COGNITION: [strategic_goal_changed, project_started, project_completed, project_abandoned,
       knowledge_default_fallback, belief_assimilated, belief_updated, lead_certainty_updated,
       self_model_updated]
     NARRATIVE_QUEST: [quest_started, quest_completed, quest_failed]
     IDENTITY: [entity_role_changed, entity_faction_changed]
     CONCLUSION_DEMOGRAPHIC: [entity_killed, demographic_mortality, demographic_birth]
     GROWTH_TAGS: [attribute_changed, xp_granted, level_up, skill_unlocked, recipe_learned,
       item_equipped]   # subset of GROWTH_PROGRESSION used as the positive side of growth_trajectory
     STALL_TAGS: [capability_growth_stalled, progression_plateau_detected]  # negative side
   ```
2. **`tools/entity_lifecycle_score.py`**:
   - `load_weights(path=None) -> dict` — reads the YAML above, matching
     `tools/generate_corpus_registry.py`'s own config-loading style.
   - `_run_for_analysis(world, seed, ticks, obs_mode, entity_count=10) -> str` (returns run_dir) —
     the dedicated, lean run-driver from investigation.md's Item-4 decision: duplicates
     `_run_engine()`'s RNG/state-loading/feature-flag/Kernel-construction/tick-loop/shutdown
     logic (imported helpers reused where possible — `_load_world_state`,
     `_load_profile_feature_flags` — only the guard itself is not reused), sets
     `os.environ["SIM_OBS_MODE"] = obs_mode` before constructing the Kernel, checks
     `dropped_count == 0` and reports it in the output rather than hard-failing on
     `pressure_mode_final`.
   - `extract_entity_paths(run_dir, world_state) -> dict[int, EntityPath]` — reads
     `simulation_events.jsonl`, groups by `entity_id`, joins each entity's own
     role/faction/kind/region metadata from `world_state` (per investigation.md Item 1's
     corrected field paths).
   - `compute_entity_metrics(path, weights) -> dict` — the 7 metrics, each a plain field, with a
     `confidence: "low"` marker on entropy/loop_score/conclusion_coherence when `path_length <
     minimum_sample_threshold`.
   - `aggregate(entity_metrics, group_by=None) -> dict` — mean + stdev per metric, globally and
     (if `group_by` given) per group; includes z-scores per entity relative to its own run's
     population.
   - `cluster_paths(entity_metrics) -> dict` — event-type-set + transition-bigram Jaccard
     clustering, dominant-cluster share, globally and per group.
   - `run_metadata(ticks, weights) -> dict` — `stall_detector_reachable`/
     `life_arc_detector_reachable` booleans from the config's own threshold ticks.
   - CLI: `--world`/`--seed`/`--ticks`/`--obs-mode` (drives a fresh run) OR `--run-dir` (scores an
     existing one); `--group-by role,faction,kind,region` (comma-separated, optional).
3. **`docs/simulation_quality/entity_lifecycle_score.md`** (technical): the 7 metric formulas +
   property table (from the original design conversation, now finalized), the 9-bucket mapping
   with its entity.yaml row cross-references, the comparability mechanism, the real
   NORMAL-vs-LIGHT mode finding and the `_run_engine()` guard-reuse decision, both with real
   numbers from Investigate.
4. **`docs/guides/entity_lifecycle_score.md`** (practitioner guide): how to run it
   (`--world`/`--seed`/`--ticks` vs `--run-dir`), how to read a report, worked example using the
   investigation's own real `sandbox_world`/`frontier_extended` findings.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms metadata/obs-mode/bucket-mapping/data-source | Done |
| plan.md specifies final formulas/aggregation/clustering/comparability | This file |
| Tool implemented, config-driven | `tools/entity_lifecycle_score.py` + weights YAML |
| Technical + guide docs | 2 new docs |
| Scoped tests pass incl. regression check | `tests/tools/test_entity_lifecycle_score.py` |
