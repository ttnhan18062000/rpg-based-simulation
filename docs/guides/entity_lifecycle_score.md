---
status: active
layer: simulation
authority: P2
audience: developer
title: Entity Lifecycle Score — Practitioner Guide
tags: [simulation-quality, observability, world]
---

# Entity Lifecycle Score — Practitioner Guide

**Companion doc:** [`docs/simulation_quality/entity_lifecycle_score.md`](../simulation_quality/entity_lifecycle_score.md)
(formulas, bucket mapping, the real observability-mode/run-driver findings — read that first if
you haven't). This guide is the practical "how do I actually use this" counterpart.
**Ticket:** TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS

---

## Running it on a fresh simulation

```bash
python3 tools/entity_lifecycle_score.py --world sandbox_world --seed 42 --ticks 800
```

This drives a real, short-lived Kernel run at `SIM_OBS_MODE=NORMAL` (the config's own
`default_obs_mode` — see the technical doc for why `NORMAL`, not the real production default
`LIGHT`, is required to see anything meaningful), scores it, prints a JSON report, and cleans up
its own `data/runs/` scratch directory afterward — it never leaves run data behind.

Add `--group-by role,faction,kind,region` (the default) to control which dimensions get
per-group aggregation, or narrow it: `--group-by faction` for just faction-level breakdowns.

## Scoring an existing run

If you already have a `simulation_events.jsonl` (e.g. from `tools/calibrate_simq.py`), score it
directly without driving a new simulation:

```bash
python3 tools/entity_lifecycle_score.py --run-dir data/runs/run_XXXXXXX_XXXX --world sandbox_world --seed 42
```

`--world`/`--seed` are still required even with `--run-dir` — they're used to load the compiled
world state for real entity metadata (role/faction/kind/region), not to drive a simulation.

## Reading the report

The JSON has 4 top-level sections:

- **`run_metadata`**: `ticks`, and `stall_detector_reachable`/`life_arc_detector_reachable` —
  whether the run was even long enough for `capability_growth_stalled` (needs 300+ ticks) or
  `life_arc_incoherent` (needs Hero generation 2+, no fixed tick proxy, reported `null`) to have
  fired at all. **Always check this before reading a "0% stalled" figure as good news** — at
  200 ticks, `stall_detector_reachable` is `false`, meaning the detector structurally could not
  have fired yet, a different claim from "confirmed not stalling."
- **`entity_metrics`**: per-entity, the 7 metrics plus `metadata` (role/faction/kind/region) and
  `confidence` markers on entropy/loop_score below the minimum-sample threshold.
  **`metadata.role: None`** (grouped as `"None"` in `aggregation.groups`/`clustering.groups`)
  should now be rare when driving a fresh run (`TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-
  METADATA-GAP` resolves it for any entity present in the real post-run state) — if you still see
  it, either the entity was born *and* removed entirely within the observed window (a real,
  disclosed residual case), or you're scoring via `--run-dir` (no live Kernel to resolve post-run
  metadata from, pre-run-only by design).
- **`aggregation`**: `global` (mean+stdev per metric across the whole population),
  `zscores` (per entity, per metric, relative to the run's own population), and `groups` (same
  mean+stdev breakdown per role/faction/kind/region value).
- **`clustering`**: `global` and per-group `distinct_shapes`/`dominant_shape`/
  `dominant_shape_share` — the most direct "are entities repeating each other" signal.

## Interpreting a value: what's normal?

There is still no universal pass/fail threshold — but `TCK-20260808-ENTITY-LIFECYCLE-SCORE-
CALIBRATION` has now run the tool across real worlds and tick-lengths and found real, usable
context. Reference points from `sandbox_world`, seed 42, 800 ticks, `NORMAL` mode:

- `dominant_shape_share`: **0.52** (21 entities, 7 distinct shapes) — over half the population
  shared one exact event-type set. Compare a new run's own figure against this, not an assumed
  "0 is perfect" bar — some convergence is expected (entities in the same role doing similar
  things is not automatically bad); the question is whether it's *this* extreme.
- `phase_coverage` mean: **0.46** (up from 0.35 under an earlier, incomplete bucket mapping) —
  under half the 9 real lifecycle buckets touched on average.
- `growth_trajectory` mean: **-0.008** (near zero, slightly negative) — the population is not, on
  net, growing more than it's stalling.

**Before trusting a `dominant_shape_share`/`distinct_shapes` figure, check
`run_metadata.clustering_reliable` first.** Calibration found this metric is genuinely inflated
at short tick-lengths (0.61 at 500 ticks vs. 0.19 at 1000+ ticks on the same world/seed) — a
short run mechanically looks more clustered simply because paths are too short to differentiate,
not because the population is actually less diverse. `clustering_reliable` is `false` below
1000 ticks; read `dominant_shape_share` as a soft signal, not a verdict, when it is.

**Density context**: calibration found a real, moderately strong negative correlation between a
world's own `entity_density_per_area` (see `docs/world/density_metrics.md`) and
`dominant_shape_share` (r ≈ -0.73 across 6 worlds) — denser worlds tend to show less population-
wide clustering. A high `dominant_shape_share` in an already-sparse world is less surprising than
the same figure in a dense one; weigh accordingly, though n=6 isn't large enough to treat this as
a hard rule.

**Archetype context** (`TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS`): a real,
corpus-wide survey found 3 worlds — `wilderness_survival`, `dungeon_crawl`,
`quest_dense_frontier` — have zero civilian-service population (no `worker`/`guard`/`merchant`/
`blacksmith`, only monster/hostile content); every other corpus world has all 4. When
`clustering.global.diversity_context` is present in the tool's own output (pass `--world` on the
CLI, or `world_name=` when calling `cluster_paths()`/`score_run()` directly, to enable the
lookup), a low `dominant_shape_share` for that world is **expected by its own design archetype**,
not a defect — `config/simulation_quality/corpus_registry.yaml`'s `_worlds.<name>.archetype`
field (`"monster_only_gauntlet"` vs `"civilian_settlement"`) is the real, computed source; the raw
`dominant_shape_share` number itself is never adjusted, only its interpretation gets this
annotation.

## Worked example: spotting a real diversity failure

```bash
python3 tools/entity_lifecycle_score.py --world sandbox_world --seed 42 --ticks 800 | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(json.dumps(d['clustering']['global'], indent=2))"
```

If `dominant_shape_share` is high (e.g. > 0.5) and `dominant_shape` is a short list dominated by
stall/dormancy tags (`capability_growth_stalled`, `progression_plateau_detected`) rather than
real activity, that's the same failure class this ticket's own investigation found — check
`run_metadata.stall_detector_reachable` first (rule out "too short to matter"), then look at
`aggregation.groups` broken down by role/faction to see if the collapse is population-wide or
concentrated in one group.

## What this guide does NOT cover

- **Establishing real pass/fail thresholds** for any of the 7 metrics — that's the sibling
  calibration ticket's own scope, not decided here.
- **Wiring these scores into SimQ pillar grading** (`QualityHub`/`grade_anchors.json`) — a
  separate, later decision, not assumed by this tool.
- **Fixing the underlying causes** this tool surfaces (LIGHT-mode suppression as a real
  production concern, sparse growth-mechanic activity) — this is a diagnostic instrument, not
  the fix for what it measures.
