---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [simulation-quality, calibration]
---

# Plan — TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER

## New tool: `tools/simq_long_run_observation.py`

One real Kernel run per world (via `entity_lifecycle_score._run_for_analysis()` — the lean,
reliable driver already established by the sibling ticket, deliberately not
`calibrate_simq._run_engine()`'s own fragile integrity guard), reused for **both** signals so the
engine only runs once per world at 5000 ticks:

1. Drive: `run_dir, health = _run_for_analysis(world, seed, ticks, obs_mode="NORMAL")`.
2. SimQ pillar report: reuse `calibrate_simq._load_weights(profile)` +
   `calibrate_simq._build_hub(weights, run_dir, run_id)` +
   `calibrate_simq._replay_jsonl_through_hub(run_dir, hub)` + `hub.get_quality_report().to_dict()`
   — the exact same real mechanism `calibrate_simq.py`'s own CLI uses, without re-driving the
   Kernel a second time.
3. Entity lifecycle score: `entity_lifecycle_score.score_run(run_dir, world_state, ticks,
   els_weights, group_by=[...], world_name=world)`.
4. Write both, plus `health`, to a durable, committed output:
   `docs/simulation_quality/long_run_observations/{world}_seed{seed}_{ticks}t.json` — a `docs/`
   location (not `data/calibration/` or `data/runs/`) since this is a periodic, human/agent-
   reviewed observation snapshot, not a fixture consumed by a tight-tolerance regression test.
5. Clean up the run's own `data/runs/` scratch directory (matches this repo's own convention —
   never leave scratch run data behind).

**World subset**: the 6 worlds already established by `TCK-20260808-ENTITY-LIFECYCLE-SCORE-
CALIBRATION`'s own density-correlation sample (`wilderness_survival`, `resource_dense_basin`,
`crowded_frontier`, `hero_guild_routing`, `dungeon_crawl`, `urban_political`) — default in the
CLI, overridable via `--worlds`.

**CLI**: `--ticks` (default 5000), `--seed` (default 42), `--worlds` (default the 6 above,
comma-separated override), `--obs-mode` (default `NORMAL`).

**`Makefile`**: new `simq-long-run-lifecycle-observation` target, matching the `simq-corpus-
registry`/`parity-index` style (plain `python3 tools/... ` invocation).

## Docs

- `docs/simulation_quality/corpus_tier_taxonomy.md`: short section distinguishing tier/archetype
  (per-world, orthogonal to length) from this new observation practice.
- `docs/simulation_quality/entity_lifecycle_score.md`: document the new tool/target and the real
  5000-tick cost data this ticket measured.

## No `grade_anchors.json` / pillar-scoring-formula change

Per this ticket's own Out of Scope — this tier observes, it does not grade or gate.

## After Implement: run it for real

Per the user's own explicit follow-up instruction: once this tool exists, actually run it across
the 6 curated worlds at 5000 ticks, producing real committed output — then deeply investigate the
combined SimQ + lifecycle-score data and scope a new epic ticket for the next phase of
entity-lifecycle improvement work. This is downstream of this ticket's own Acceptance Criteria
(which require the mechanism to exist and be re-runnable, not that a specific analysis be
completed) but is the concrete next action once this ticket closes.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| investigation.md surveys all tick-gated detectors | Done — 7 detectors beyond the 2 already known, real max 500 ticks |
| investigation.md reports real 5000-tick cost, 2+ worlds | Done — 250.3s/250.9s, frontier_extended/simq_scale_stress_seed42 |
| plan.md specifies tier/fixture shape and world coverage | This plan |
| Real, repeatable mechanism, re-runnable, durable output | `tools/simq_long_run_observation.py` + `docs/simulation_quality/long_run_observations/` |
| `corpus_tier_taxonomy.md` updated if new tier added | Updated (clarifying section, not a new tier value — see investigation.md's own decision) |
| Scoped pytest passes | test_plan.md |
