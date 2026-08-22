---
status: active
layer: world
authority: P1
audience: developer
tags: [rendering, visualization, simulation-quality, documentation]
---

# Visual Quality Scoring Contract

This document is the `docs/visual_quality/` equivalent of
`docs/simulation_quality/quality_scoring_contract.md` — the same kind of authoritative
contract, scaled to the visual-quality system's genuinely smaller real scope. It
describes `src/rendering/`'s structural/geometric quality-scoring mechanism: four raw
metric modules, a grading module that turns their facts into an S/A/B/C/D/F grade, and
a two-tier escalation pipeline that decides when an agent needs to look at an image.

## 1. Purpose & Scope

This module scores the structural/geometric quality of a rendered world state —
connectivity, entity density, terrain shape, and content-variant diversity — turning raw
facts about a compiled `AuthoritativeState` into an S/A/B/C/D/F grade and an escalation
decision for agent review.

It does **not** score simulation *behavioral* health (goal pursuit, social cohesion,
economic activity, combat balance, etc.) — that is `src.simulation_quality`'s job, a
structurally separate 10-pillar system. It also does not score render-pixel correctness
(byte-for-byte PNG output fidelity) — that is the golden-hash incremental-render test
(`tests/unit/rendering/test_render_incremental.py`), a different concern entirely.

## 2. Architectural Position

Data flow, raw facts to escalation decision:

```
render.py / connectivity.py / density.py / shape.py / variants.py   (raw metric facts)
        |
        v
grading.py
  load_grade_config, evaluate_hard_rule, evaluate_soft_rule,
  combine_rule_deltas, assign_grade, average_scores
        |
        v
review_pipeline.py :: run_tier0_tier1_pipeline  ->  Tier1Digest
        |
        v
.claude/agents/world-render-reviewer.md   (reads the digest; escalates to an image only when told to)
```

**Architectural-independence boundary (deliberate, enforced in code, not just by
convention):** `src/rendering/` never imports `src.simulation_quality.*` or
`src.observability.events`, never subclasses `PillarScorer`, and never registers a
`PillarId`. This is enforced by
`tests/architecture/test_rendering_zero_new_dependency_guard.py` and recorded as
`INFRA-374` (`docs/parity_ledger/infrastructure.yaml:10896-10911`). Visual-quality is a
SimQ-*sibling* system that reuses SimQ's grade-threshold ladder by value, not a SimQ
subsystem or an 11th pillar.

## 3. The Four Metric Families

One module per family. Each states its real function signature and the one behavioral
fact worth documenting.

- **Connectivity (`connectivity.py`)** — `analyze_connectivity(terrain, blocked_tiles) ->
  ConnectivityResult`. A BFS flood-fill over exactly the same walkability test as the
  first two checks of `LegalityServiceV2.verify_occupancy`
  (`src/engine/legality.py:71-77`): a tile is walkable iff `terrain.get(pos) != "WALL"`
  and `pos not in blocked_tiles`. Membership is checked against a precomputed
  `walkable_tiles` set, never a live re-check.

- **Density (`density.py`)** — `compute_density_cv(entities) -> DensityResult`.
  Population-stdev (`statistics.pstdev`, **not** sample-stdev) of per-entity
  nearest-Euclidean-distance, divided by the mean, over active entities only. Cite the
  two verified anchors verbatim, uncomputed: `sandbox_world` CV =
  `0.6478017242079448`, `dungeon_crawl` CV = `0.6782405727873148`.

- **Shape (`shape.py`)** — `connected_components(terrain, min_size=20,
  excluded_types={"PLAIN","ROAD"}) -> list[ShapeComponent]`. BFS is run once per
  distinct raw terrain-type string (a different question from connectivity's single
  global BFS). `fill_ratio = len(tiles) / bbox_area` is computed **per connected
  component**, not one aggregated bounding box — this replaced a real pre-fix bug that
  aggregated all same-type tiles into one bounding box with no connectivity check,
  producing a meaningless FOREST fill-ratio of 0.716 instead of the correct
  1.000/1.000 pair.

- **Variants (`variants.py`)** — `total_variation_distance(h1, h2) -> float`
  (`0.5 * sum(abs(h1[k] - h2[k]) for k in ...)`). Cite the verified anchor verbatim,
  uncomputed: `TVD(sandbox_world, dungeon_crawl) = 0.23161981243456373`; same-spec/
  different-seed TVD is exactly `0.0` for `dungeon_crawl`. `select_trail_entity`
  deliberately uses `hashlib.sha256(f"{world_id}:{seed}")` over a sorted active-entity
  list, **not** `DeterministicRNG`/`Domain` — a read-only QA selection must not touch
  the replay-critical authoritative-randomness mechanism.

## 4. Grade Model

Two rule shapes, additively combined:

- **Hard rules** — binary pass/fail. A fixed delta on pass, a fixed (typically
  negative) delta on fail. E.g. `fully_connected`.
- **Soft rules** — trapezoidal, healthy-band-shaped, non-monotonic in the raw metric:
  `peak_delta` inside `[healthy_low, healthy_high]`, ramping linearly down to
  `min_delta` across `[low, healthy_low]` and `[healthy_high, high]`, held at
  `min_delta` at and beyond `low`/`high`. E.g. `fill_ratio_healthy_band`.

`combine_rule_deltas` sums all hard- and soft-rule deltas additively. `assign_grade`
applies a strict-`>` ladder against the combined score. Cite the ladder verbatim,
uncomputed: `S > 2.0`, `A > 0.5`, `B > 0.0`, `C > -0.5`, `D > -1.0`, `F` otherwise —
copied **by value**, not imported, from
`config/simulation_quality/grade_thresholds.yaml` (confirmed identical by direct read of
`config/rendering/grade_thresholds.toml:3-8`). `average_scores` is a plain arithmetic
mean over `list[float]`, with no N=1 special case.

## 5. Escalation Pipeline

`run_tier0_tier1_pipeline(state, world_id, base_dir, run_id, grade_config=None) ->
Tier1Digest` composes connectivity, density, shape, and grading into one deterministic,
JSON-serializable digest (`digest_to_json`, `json.dumps(..., sort_keys=True)`).

`should_escalate(hard_results, grade) -> bool` is the single call site for the
escalation cutoff: any hard-rule failure, or a grade in `{D, F}`.

The structural enforcement point for "zero image is ever fetched when Tier 0 does not
flag an anomaly" is the `if escalate:` gate at `review_pipeline.py:112-117` —
`render_annotated(...)` and the annotated PNG write to disk happen **only** inside that
branch. This is enforced in code, not left to agent-prompt discipline alone.

## 6. Testing Contract

Real test files covering this system:

- `tests/unit/rendering/test_connectivity.py`
- `tests/unit/rendering/test_density.py`
- `tests/unit/rendering/test_shape.py`
- `tests/unit/rendering/test_variants.py`
- `tests/unit/rendering/test_grading.py`
- `tests/unit/rendering/test_review_pipeline.py`
- `tests/architecture/test_rendering_zero_new_dependency_guard.py`
- `tests/tools/test_calibrate_rendering.py`

## 7. Non-Goals

To prevent a future reader assuming SimQ-parity feature-for-feature, this system
explicitly does **not** have:

- A REST API surface (no route exposes visual-quality data).
- A persistence/`QualityHub`-equivalent event-driven scoring layer.
- A `PillarScorer` registry or a `PillarId` registration mechanism.
- A dual-feed broker mode (no `QualityFeedAdapter`/Redis consumer exists for
  rendering).
- CI-gating of grade thresholds — see `docs/visual_quality/current_state.md` for why
  the threshold *values* are not yet calibrated enough to gate on.
