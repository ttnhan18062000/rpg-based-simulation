---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-DENSITY-METRIC
artifact_type: plan
tags: [visualization, simulation-quality, world]
---

# Implementation Plan — TCK-20260821-VISUAL-DENSITY-METRIC

## Summary

Add a new sibling module `src/rendering/density.py` that computes two independent, pure,
Tier-0 metrics over raw `entities`/`terrain` dicts — nearest-neighbor coefficient of
variation (CV) and a terrain-type histogram — following `src/rendering/connectivity.py`'s
exact shape (frozen dataclass result, pure functions over raw dicts, docstring citing
provenance). The CV formula and both documented reproduction numbers were already traced
and verified exactly by investigation.md (population std / mean, `statistics.pstdev()`,
not `stdev()`); this plan implements that formula as-is, extracts the terrain-histogram
counting logic verbatim from `experiments/spatial_rendering/prototype/render_world.py:90-95`
without normalizing keys, adds ten new tests mirroring `test_connectivity.py`'s structure,
and records one new P2 parity-ledger entry (`INFRA-371`, confirmed next-available by direct
file read — current max is `INFRA-370`). No SimQ, observability, kernel, or spatial-query
code is touched; all of that is read-only context per the investigation.

## Steps

### Step 1 — Create `src/rendering/density.py` with the CV computation

**Files:** `src/rendering/density.py` (new)

**Change:** Create the module with a module docstring citing the provenance investigation.md
already established: the CV formula was traced from one-off verification code (never
committed to a prototype file — `experiments/spatial_rendering/PROPOSAL.md:399-403` and
`:470` state this explicitly), reproduced directly against `sandbox_world`/`dungeon_crawl`
at seed 42, tick 0, matching `≈0.648`/`≈0.678` to 6+ significant figures using population
standard deviation. Follow `src/rendering/connectivity.py`'s exact shape (read in full,
`/home/u24desktop/Working/rpg-based-simulation/src/rendering/connectivity.py`): a
`@dataclass(frozen=True)` result and a pure function over raw dicts, not `AuthoritativeState`.

Add:

```python
from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class DensityResult:
    cv: float
    entity_count: int
    nn_distances: list[float]


def compute_density_cv(entities: dict) -> DensityResult:
    ...
```

`entities` is `dict[int, EntityState]` — same type as `AuthoritativeState.entities`
(confirmed `src/core/state.py:1095`). Implementation:
1. Filter to active entities only, using `EntityState.active`, a direct passthrough
   property to `self.lifecycle.active` (confirmed by direct read,
   `src/core/state.py:771-773`: `return self.lifecycle.active`, no default-True fallback
   needed — production code uses the plain property, not the prototype's defensive
   `getattr(..., True)`).
2. Read each active entity's position via `EntityState.position` (confirmed
   `src/core/state.py:759-761`, a `@property` returning `self.navigation.position:
   tuple[float, float]`).
3. For each active entity, compute the Euclidean distance
   (`math.dist(a, b)` or `((ax-bx)**2 + (ay-by)**2) ** 0.5`) to every other active entity,
   take the minimum — the nearest-neighbor distance.
4. `cv = statistics.pstdev(nn_distances) / statistics.mean(nn_distances)`. **Do NOT use
   `statistics.stdev()`** — investigation.md confirmed by direct comparison that sample std
   (ddof=1) produces 0.667/0.689 for sandbox_world/dungeon_crawl, which does not match the
   documented values, versus population std (ddof=0) producing 0.6478017.../0.6782405...,
   which matches to 6+ significant figures. Add an inline code comment at the `pstdev` call
   stating exactly this (`# population std (ddof=0), NOT stdev() (ddof=1) — see
   investigation.md, sample-std produces 0.667 not 0.648 for sandbox_world`).
5. Guard the degenerate case (0 or 1 active entities): if `entity_count < 2`, no
   nearest-neighbor distance is defined for any entity — return `DensityResult(cv=0.0,
   entity_count=n, nn_distances=[])` rather than raising, since `statistics.mean`/`pstdev`
   raise on an empty sequence. This is a defensive guard, not exercised by the documented
   real-corpus tests (18/32 entities), but prevents a crash on a legitimately empty or
   single-entity world.

**Do NOT touch:** `src/rendering/connectivity.py`, `src/rendering/render.py`, or any other
file in `src/rendering/`. This step only creates the new file.

**Verify:** `test_sandbox_world_reproduces_documented_cv`,
`test_dungeon_crawl_reproduces_documented_cv`, `test_population_stdev_not_sample_stdev`,
`test_two_entities_minimum_nn_distance`, `test_inactive_entities_excluded_from_cv`.

### Step 2 — Add `compute_terrain_histogram` to the same module

**Files:** `src/rendering/density.py` (same file as Step 1)

**Change:** Add a second pure function to the same module, keeping the two metrics
independently callable/testable per the ticket's own Scope bullet structure (CV and
histogram are listed as two separate implementation items):

```python
def compute_terrain_histogram(terrain: dict) -> dict[str, int]:
    ...
```

Extract the counting logic verbatim from
`experiments/spatial_rendering/prototype/render_world.py:90-95` (confirmed by direct read
in investigation.md, quoted in full there):

```python
histogram: dict[str, int] = {}
for tval in terrain.values():
    histogram[tval] = histogram.get(tval, 0) + 1
return histogram
```

`terrain` is `dict[tuple[int,int], str]` (confirmed `src/core/state.py:1126`,
`AuthoritativeState.terrain`). **Do not call `.upper()` or otherwise normalize `tval`** —
investigation.md's Anti-Drift Hazards section is explicit that the prototype counts raw
values before `terrain_color()`'s `.upper()` normalization is applied, so `'PLAIN'` and
`'plain'` must remain distinct keys. `sum(histogram.values()) == len(terrain)` holds by
construction (one increment per `terrain.values()` entry), matching AC #2 exactly.

**Do NOT touch:** `experiments/spatial_rendering/prototype/render_world.py` itself (this is
an extraction, not a refactor of the source) or `src/rendering/render.py` (which still owns
its own copy of this logic as a rendering side effect — not this ticket's concern to
deduplicate/redirect).

**Verify:** `test_terrain_histogram_sums_to_terrain_tile_count`,
`test_dungeon_crawl_histogram_matches_terrain_tile_count`.

### Step 3 — Write `tests/unit/rendering/test_density.py`

**Files:** `tests/unit/rendering/test_density.py` (new)

**Change:** Create the test file mirroring `tests/unit/rendering/test_connectivity.py`'s
structure and imports (`WorldRepository("data/worlds").load_world(world_id)` →
`WorldCompiler.compile(spec, seed=42)`, tick 0, no `Kernel.tick_once()` calls — same
invocation pattern that file's `test_dungeon_crawl_matches_documented_evidence` already
uses). Implement all 10 tests from test_plan.md's "New Tests Required" section verbatim:

1. `test_sandbox_world_reproduces_documented_cv` — real corpus, `round(result.cv, 3) ==
   0.648`, exact-to-3-decimal-places (per investigation.md's Risks section recommendation;
   not a loose tolerance band).
2. `test_dungeon_crawl_reproduces_documented_cv` — `round(result.cv, 3) == 0.678`.
3. `test_population_stdev_not_sample_stdev` — small synthetic 3-4 entity fixture with
   known, hand-computed coordinates where population-std and sample-std visibly diverge;
   assert the function matches the population-std hand-computation.
4. `test_two_entities_minimum_nn_distance` — 2-entity fixture, each entity's nearest
   neighbor is unambiguously the other.
5. `test_inactive_entities_excluded_from_cv` — one inactive entity (`lifecycle.active ==
   False`) positioned far from the rest; confirm presence/absence doesn't change the
   result.
6. `test_terrain_histogram_sums_to_terrain_tile_count` — synthetic terrain fixture
   including `"PLAIN"`/`"plain"` as a deliberately mixed-case pair; assert sum invariant
   and that the two keys remain distinct.
7. `test_dungeon_crawl_histogram_matches_terrain_tile_count` — real compiled
   `dungeon_crawl` `state.terrain`, same sum invariant.
8. `test_density_module_has_zero_image_or_render_dependency` — AST-parse
   `src/rendering/density.py`'s source and assert no import of
   `src.rendering.png_writer`, `src.rendering.render`, `src.rendering.incremental`,
   `PIL`/`Pillow`, or any other image-writing module.
9. `test_density_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` —
   AST-based static check (not runtime import-and-introspect, to avoid false negatives
   from lazy imports) for (a) any class definition with `PillarScorer` in its base list,
   (b) any import referencing `src.simulation_quality` or `src.observability.events`.
10. `test_does_not_mutate_authoritative_state` — call both functions twice against the
    same `entities`/`terrain` fixture, assert identical results both times and that the
    input collections are byte-for-byte unchanged after the calls (mirrors
    `test_connectivity.py`'s guard of the same name).

Entity fixtures for tests 3-5 should construct minimal `EntityState` instances (or the
project's existing entity-fixture helper, if `test_connectivity.py` or another
`tests/unit/rendering/` file already has one — check before hand-rolling) with controlled
`navigation.position` and `lifecycle.active` values.

**Do NOT touch:** any existing file in `tests/unit/rendering/` (all listed in test_plan.md's
Regression Surface as "must keep passing, no change expected") or
`tests/unit/simulation_quality/` (must stay green as an anti-coupling guard, not modified).

**Verify:** running
`.venv/bin/python3 -m pytest tests/unit/rendering/ -v` and
`.venv/bin/python3 -m pytest tests/unit/simulation_quality/ -v` — both fully green, per
test_plan.md's Scoped Pytest Commands (bare directories, not cherry-picked files).

### Step 4 — Add parity ledger entry `INFRA-371`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed by direct read (`grep -n "^- id:" docs/parity_ledger/
infrastructure.yaml | tail`) that the current maximum id is `INFRA-370` (line 10840), so
`INFRA-371` is genuinely the next available id — not assumed from the investigation's
suggestion alone. Append a new entry at the end of the file (currently 10849 lines),
following `INFRA-370`'s exact field shape (read directly, lines 10840-10849):

```yaml
- id: INFRA-371
  text: Entity nearest-neighbor coefficient of variation (population standard deviation
    divided by mean of per-entity nearest Euclidean distance, active entities only)
    reproduces documented sandbox_world (~0.648) and dungeon_crawl (~0.678) values
    deterministically from AuthoritativeState.entities at seed 42, tick 0.
  status: verified
  priority: P2
  v2_evidence: src/rendering/density.py
  test_path: tests/unit/rendering/test_density.py::test_dungeon_crawl_reproduces_documented_cv
  divergence_note: null
  proof_type: parity
```

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a single YAML
list appended to by every ticket that lands a new infrastructure-layer parity fact — most
recently `INFRA-369` (render determinism, `TCK-20260821-WORLD-RENDER-CORE`) and `INFRA-370`
(connectivity, `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`), both already merged and DONE
before this ticket started, so there is no concurrent-write race with this step — this
ticket is not running in parallel with another ticket that also appends to this file. If a
concurrent session has appended further entries since the read above, re-run the `grep`
before appending to confirm `INFRA-371` is still the next free id; do not hardcode the
number if the file has moved.

**Do NOT touch:** `docs/plans/world_rendering/idea_world_render_validation.md` (deliberately
deferred to the batch's final ticket, `TCK-20260821-VISUAL-QUALITY-DOCS`, per
investigation.md) or `docs/simulation_quality/quality_scoring_contract.md` (investigation.md
confirmed no relevant content, not applicable).

**Verify:** no automated test covers this file directly; `done-checker`'s frontmatter/parity
checks validate it structurally. Manually confirm the new entry parses as valid YAML
(`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`).

## Scope Guards

Must NOT be touched by this ticket, per investigation.md's Anti-Drift Hazards and the
ticket's Out of Scope:

- `src/simulation_quality/` (entire directory) — no `PillarScorer` subclass, no import.
- `src/observability/events.py` — no import of `ObservabilityEventEnvelope` or anything
  else from this module.
- `src/engine/kernel.py` — read-only context; `Kernel.get_world_indexes`/
  `entities_by_tile`-based O(N) scaling is explicitly deferred (Out of Scope), flagged only
  in a code comment in `density.py`, never implemented.
- `src/engine/spatial_query.py` — read-only context; `SpatialQueryService.nearby_entities`
  is confirmed not reusable (bounded radius, Manhattan distance) and must not be imported
  or adapted.
- `src/rendering/connectivity.py` — sibling module, must remain byte-for-byte unchanged.
- `src/rendering/render.py` — still owns its own copy of the terrain-histogram logic as a
  rendering side effect; this ticket extracts the logic into a new standalone function, it
  does not redirect `render.py` to call the new function.
- `experiments/spatial_rendering/prototype/render_world.py` — source of the extracted
  histogram logic, read-only reference, not modified.
- Any grade-band/scoring/healthy-band-threshold logic — explicitly out of scope
  (`TCK-20260821-VISUAL-GRADE-SCORER`, `TCK-20260821-VISUAL-QUALITY-CALIBRATION`).
- `docs/plans/world_rendering/idea_world_render_validation.md` and
  `docs/simulation_quality/quality_scoring_contract.md` — deferred/not applicable, per
  investigation.md's Docs Requiring Update section.

## Dependency Map

- Step 1 (CV) and Step 2 (histogram) are independent of each other — both are additions to
  the same new file but touch disjoint functions with no shared state; either could be
  implemented first.
- Step 3 (tests) depends on both Step 1 and Step 2 being complete, since
  `test_density.py` exercises both functions.
- Step 4 (parity ledger) depends on Step 3 passing, since the new entry's `test_path`
  cites a specific test (`test_dungeon_crawl_reproduces_documented_cv`) that must exist and
  pass before the entry can honestly claim `status: verified`.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: Nearest-neighbor CV function reproduces sandbox_world≈0.648 and dungeon_crawl≈0.678 within a stated tolerance | Step 1 | `test_sandbox_world_reproduces_documented_cv`, `test_dungeon_crawl_reproduces_documented_cv`, `test_population_stdev_not_sample_stdev` |
| AC #2: Terrain histogram dict values sum exactly to len(state.terrain) | Step 2 | `test_terrain_histogram_sums_to_terrain_tile_count`, `test_dungeon_crawl_histogram_matches_terrain_tile_count` |
| AC #3: Both metrics are computed via a Tier-0 pure-data path with zero image/render dependency | Step 1, Step 2 (both functions take raw dicts, no image import anywhere in the module) | `test_density_module_has_zero_image_or_render_dependency` |
| AC #4: No PillarScorer subclass is created and no SimQ event-pipeline import exists in this module | Step 1, Step 2 (module contains zero `src.simulation_quality.*`/`src.observability.events` imports and no `PillarScorer` subclass by construction) | `test_density_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline` |

## Anti-Drift Notes

- **Population std vs. sample std is the single most load-bearing detail in this plan.**
  `statistics.pstdev()` (ddof=0), not `statistics.stdev()` (ddof=1) — investigation.md
  confirmed by direct numeric comparison that the sample-std variant produces a plausible
  but wrong number (0.667/0.689 vs the correct 0.648/0.678). Step 1 requires an explicit
  inline code comment on this exact point; Step 3's test 3 is the dedicated regression
  guard.
- **Do not normalize terrain histogram keys.** `'PLAIN'` and `'plain'` must remain distinct
  — this is a deliberate preservation of an existing casing-fragmentation characteristic
  documented by `TCK-20260821-WORLD-RENDER-CORE`'s investigation, not a bug this ticket is
  meant to fix.
- **O(N²) is intentional and acceptable at current entity counts (11-32).** Do not reach
  for `Kernel.get_world_indexes`/`WorldIndexes.entities_by_tile` or
  `SpatialQueryService.nearby_entities` — both were checked directly by investigation.md
  and are either not adopted-yet (out of scope) or not actually compatible (bounded radius,
  Manhattan distance, not Euclidean all-pairs).
- **`EntityState.active` and `EntityState.position` are direct property passthroughs**
  (confirmed `src/core/state.py:771-773` and `:759-761`) — no defensive `getattr` fallback
  is needed in production code, unlike the prototype's `getattr(ent.lifecycle, "active",
  True)`.
- **This module must have zero imports from `src.simulation_quality.*` or
  `src.observability.events`**, and zero `PillarScorer` subclass — enforced by a static
  AST-based test (test 9), not just by omission, per CLAUDE.md's Architecture Rule test-
  guard requirement.
- **No grading/scoring/healthy-band logic belongs in this module.** The functions return
  raw structural facts (`DensityResult.cv`, the histogram `dict`), not a grade or
  healthy/unhealthy verdict — that is `TCK-20260821-VISUAL-GRADE-SCORER`'s scope, a later
  ticket in the same batch that depends on this one.
