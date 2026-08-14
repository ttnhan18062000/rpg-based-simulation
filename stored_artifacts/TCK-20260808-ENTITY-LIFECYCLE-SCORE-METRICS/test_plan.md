---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS
artifact_type: test_plan
tags: [simulation-quality, observability, world]
---

# Test Plan — TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS

New file: `tests/tools/test_entity_lifecycle_score.py`

## Per-entity metric formulas (hand-built event sequences, no real Kernel needed)
1. `test_path_length_and_density` — hand-built sequence of N events over T ticks; assert
   `path_length == N`, `path_density == N/T`.
2. `test_phase_coverage_counts_distinct_buckets_touched` — events spanning 3 of 9 buckets;
   assert `phase_coverage == 3/9`.
3. `test_path_entropy_zero_for_single_type_max_for_uniform` — degenerate (all one event type) →
   entropy ≈ 0; uniform across N distinct types → entropy ≈ 1 (normalized).
4. `test_loop_score_detects_dominant_short_cycle` — a real period-2 repeating sequence → high
   loop_score (low novelty); a genuinely varied sequence → low loop_score.
5. `test_growth_trajectory_positive_and_negative` — sequence dominated by growth-tagged events →
   positive; sequence dominated by stall tags → negative.
6. `test_conclusion_coherence_flags_incoherent_and_silent_from_spawn` — a `life_arc_incoherent`-
   tagged sequence and a zero-event ("silent from spawn," matching D05's own finding) entity both
   flagged incoherent; a normal death-with-cause sequence flagged coherent.
7. `test_minimum_sample_gating_flags_low_confidence` — an entity with `path_length < 6` marks
   `path_entropy`/`loop_score`/`conclusion_coherence` as `confidence: "low"` in its own output.

## Population aggregation + grouping
8. `test_aggregation_reports_mean_and_stdev_not_mean_alone` — a population with 2 distinct
   sub-groups of different metric values; assert both mean AND stdev present and stdev > 0
   (catches a regression to "mean only," which is the exact failure mode the investigation found).
9. `test_grouping_by_role_faction_kind_region` — entities tagged with different
   role/faction/kind/region; assert per-group aggregates are computed separately and differ.
10. `test_path_clustering_reports_dominant_shape_share` — a population where 70% share an
    identical event-type set; assert clustering reports 1 dominant cluster at ~70% share — a
    direct regression check against the investigation's own real finding
    (`{capability_growth_stalled, progression_plateau_detected}` at 67% on `sandbox_world`).

## Comparability mechanism
11. `test_within_run_zscore_computation` — a population with known mean/stdev; assert each
    entity's z-score matches the hand-computed value.
12. `test_detector_reachability_metadata_reflects_tick_count` — `ticks=200` →
    `stall_detector_reachable: False`; `ticks=800` → `True` (300-tick threshold, per
    `capability_growth_stalled`'s own real detector window).

## Data source / run driver
13. `test_scoring_an_existing_run_dir_does_not_drive_a_new_kernel` — pass `--run-dir` pointing at
    a hand-built scratch `simulation_events.jsonl`; assert no Kernel is constructed (mock/spy or
    a real absence-of-side-effect check).
14. `test_dedicated_run_driver_reports_dropped_count_without_hard_failing_on_pressure` — real,
    non-mocked: run a short real simulation at `SIM_OBS_MODE=NORMAL`; assert the tool's own
    output includes a `dropped_count` field and does NOT raise merely because
    `pressure_mode_final != "NORMAL"` (the real conflict found in Investigate) — construct this
    by monkeypatching/forcing queue pressure if a natural real repro isn't reliably reproducible
    in test time, documented if so.

## Regression baseline against the investigation's own real findings
15. `test_sandbox_world_800t_matches_investigation_baseline` — real, non-mocked: run
    `sandbox_world` seed 42, 800 ticks, `SIM_OBS_MODE=NORMAL` (not the investigation's own LIGHT-
    mode run — this is a stronger, richer-data version of the same check); assert the tool
    produces non-trivial `path_length` distribution and a real clustering result, sanity-checked
    against plausible bounds, not exact investigation numbers (those were LIGHT-mode, this is
    NORMAL — different inputs, same tool correctness question: does it run and produce sane
    output on a real world).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms metadata fields, obs-mode decision, bucket mapping, data source | Done |
| plan.md specifies final metric formulas, aggregation design, clustering, comparability mechanism | plan.md |
| Tool implemented, weights/thresholds config-driven | Implement |
| Technical doc + guide doc | Implement |
| Scoped tests pass, including a real regression check | Tests 1-15 |
