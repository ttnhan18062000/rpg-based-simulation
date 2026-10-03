---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-DENSITY-METRIC
artifact_type: investigation
tags: [visualization, simulation-quality, world]
---

# Investigation — TCK-20260821-VISUAL-DENSITY-METRIC

## Current Behavior

**No density/clustering/nearest-neighbor function exists in production `src/` today.** Confirmed via
`graphify query` (no match outside unrelated positioning/movement nodes) and `grep -rn "nearest.neighbor\|coefficient.of.variation\|clustering" src/` (zero hits). This is genuinely new production
logic, same shape as the sibling `TCK-20260821-VISUAL-CONNECTIVITY-METRIC` (`DONE`, merged).

**Terrain histogram already exists as a side effect, confirmed by reading
`experiments/spatial_rendering/prototype/render_world.py:90-95, 130-142` in full:**

```python
terrain_histogram: dict[str, int] = {}
for (tx, ty), tval in terrain.items():
    ...
    terrain_histogram[tval] = terrain_histogram.get(tval, 0) + 1
...
return {..., "terrain_histogram": terrain_histogram, ...}
```

It is exactly `dict[str, int]`, one key per distinct raw (non-normalized) terrain string value,
incrementing once per `terrain.items()` entry — so `sum(terrain_histogram.values()) == len(terrain)`
is true by construction, not an approximation. It is **not currently exposed from production code**
— `src/rendering/render.py` (promoted from this same prototype by `TCK-20260821-WORLD-RENDER-CORE`)
was not re-read line-by-line here since its own investigation.md already documents it promotes
`render_world.py`'s stats-dict-returning `render()` function verbatim; confirmed via `grep -n
"terrain_histogram" src/rendering/render.py` that the histogram computation and key name survived
the promotion unchanged. This ticket's job is to **extract** that computation into a standalone,
independently-testable, non-rendering function — not reimplement the counting logic, and not import
`src/rendering/render.py` just to get the histogram as a side effect of an unrelated PNG write.

**The nearest-neighbor CV formula was traced and verified directly, not assumed** — this is the
ticket's central open question and the most load-bearing finding in this investigation.
`experiments/spatial_rendering/PROPOSAL.md` never commits the CV computation to a named script
(confirmed: `grep -rn "coefficient\|nearest.neighbor" experiments/spatial_rendering/` finds only
prose/table references to the *result* — 0.648/0.678 — in `PROPOSAL.md` and
`docs/plans/world_rendering/idea_world_render_validation.md`, never a function body). §399-403 of
`PROPOSAL.md` ("Density: reuse the engine's own spatial index...") and the Related section
(`PROPOSAL.md:470`) both state explicitly this was "one-off verification code, not saved as a named
script," structurally identical to the connectivity BFS that `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`
already had to port from inline prose rather than a committed file (that ticket's own investigation.md
documents the same situation for the BFS, and its `src/rendering/connectivity.py` docstring records
the same provenance pattern this ticket should follow).

**Reproduced the exact formula and numbers directly** (scratchpad-only verification script, not
committed — same discipline as the connectivity ticket's own precedent of citing one-off code without
saving it as a prototype file): loaded `sandbox_world`/`dungeon_crawl` via
`WorldRepository("data/worlds").load_world(world_id)` → `WorldCompiler.compile(spec, seed=42)` (tick 0,
no `Kernel.tick_once()` calls — same invocation shape `tests/unit/rendering/test_connectivity.py`'s
own `test_dungeon_crawl_matches_documented_evidence` uses), then for each active entity
(`ent.lifecycle.active`), computed the Euclidean distance to every other active entity's
`ent.navigation.position` (equivalently `EntityState.position`), took the minimum (nearest-neighbor
distance), and computed `CV = population_stdev(nn_distances) / mean(nn_distances)` (i.e. `stdev`
divided by `n`, not `n-1` — **population** standard deviation, not sample standard deviation):

| World | Formula variant | Result |
|---|---|---|
| `sandbox_world` (seed 42, tick 0, 18 entities) | population std / mean | **0.6478017242079448** → matches documented `≈0.648` |
| `dungeon_crawl` (seed 42, tick 0, 32 entities) | population std / mean | **0.6782405727873148** → matches documented `≈0.678` |
| `sandbox_world` | sample std (n-1) / mean, for comparison | 0.6665824749272415 — does **not** match |
| `dungeon_crawl` | sample std (n-1) / mean, for comparison | 0.6890931110453675 — does **not** match |

This is a clean, unambiguous, exact confirmation: **population standard deviation (ddof=0), Euclidean
distance, nearest-neighbor over active entities only, computed at tick 0 immediately after
`WorldCompiler.compile(spec, seed=42)`, with no `Kernel.tick_once()` calls** reproduces the documented
numbers to 6+ significant figures. The sample-std (n-1) variant is a real, plausible alternative
formula that does **not** match — this rules out an ambiguity that could otherwise have silently
produced a wrong implementation.

**`AuthoritativeState`/`EntityState` fields needed** (all already confirmed by the two prior sibling
investigations, re-verified directly against `src/core/state.py` here, not re-derived):
- `state.entities: Dict[int, EntityState]` (`src/core/state.py:1095`)
- `EntityState.position` (`src/core/state.py:759-761`, a `@property` returning
  `self.navigation.position: tuple[float, float]`)
- `EntityState.active` (`src/core/state.py:771-773`, a `@property` returning
  `self.lifecycle.active: bool`) — used as the same activity filter `render_world.py:70-71` and
  `src/rendering/connectivity.py`'s sibling precedent both use (`getattr(ent.lifecycle, "active",
  True)` in the prototype; the production `EntityState.active` property is the cleaner equivalent)
- `state.terrain: Dict[tuple[int,int], str]` (`src/core/state.py:1126`) for the histogram

No new field or state shape is needed beyond what `TCK-20260821-WORLD-RENDER-CORE`'s and
`TCK-20260821-VISUAL-CONNECTIVITY-METRIC`'s own investigations already documented.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract governs rendering/visualization or this
metric family — same conclusion the connectivity ticket's investigation reached and re-confirmed
here (`docs/plans/world_rendering/idea_world_render_validation.md` frames the whole family as a SimQ
*sibling*, not a mechanics law or a pillar). The one real constraint that *does* apply, directly:
`docs/testing/test_taxonomy.md`'s rule that "metric-correctness tests (fill-ratio, connectivity, CV,
symmetry) are ordinary `tests/unit/` tests, no `tests/parity/` marker required" — quoted verbatim in
the idea doc and already reused by the connectivity ticket's test plan; this ticket's tests must
follow the same classification.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers entity nearest-neighbor CV or the
  standalone terrain-histogram extraction (confirmed via `grep -n "render\|walkable\|density\|histogram\|cluster"` across the file — the only real hits are `INFRA-369` (render determinism) and
  `INFRA-370` (connectivity), neither of which covers this metric). Next available ID is `INFRA-371`.
  Recommend a new entry: "Entity nearest-neighbor coefficient-of-variation (population-std/mean of
  per-entity nearest Euclidean-distance, active entities only) reproduces documented sandbox_world
  (~0.648) and dungeon_crawl (~0.678) values at seed 42, tick 0, deterministically from
  AuthoritativeState.entities" — `priority: P2` (matching `INFRA-370`'s precedent: this ticket's own
  Out of Scope marks the metric report-only/never-CI-gated, so P2 not P0 is the correct precedent to
  follow, not a new judgment call).
- `docs/plans/world_rendering/idea_world_render_validation.md` is **deliberately not listed** — same
  reasoning the connectivity ticket's investigation already established: `SEQUENCE.md` assigns final
  documentation of "the finished system's real implemented contract" to the last ticket in the batch
  (`TCK-20260821-VISUAL-QUALITY-DOCS`), specifically so it isn't written piecemeal. Updating it here
  would be premature and out of this ticket's scope.
- `docs/simulation_quality/quality_scoring_contract.md` is **not** listed — checked directly
  (`grep -n "sibling\|spatial\|rendering\|density"`); the only "density" hits are unrelated
  (`spawn_density`, an event-density remark). This ticket adds no SimQ pillar and touches nothing in
  that contract, matching AC #4 and the architectural boundary both prior sibling tickets already
  established.

## Parity Ledger Overlap

None found pre-existing (see grep above — `infrastructure.yaml` is the only file with any
`render`/`walkable`/`density`/`histogram` hits, and both real matches, `INFRA-369`/`INFRA-370`, cover
different capabilities). No P0 entries are touched. The recommended new entry is P2, consistent with
`INFRA-370`'s precedent for this same metric family.

## Prior Work

- **`stored_artifacts/TCK-20260821-WORLD-RENDER-CORE/`** — the structural prerequisite, `DONE`,
  merged. Its investigation.md's module-placement section (`src/rendering/` recommendation) and its
  documented `AuthoritativeState.terrain`/`entities` shape directly inform this ticket.
- **`stored_artifacts/TCK-20260821-VISUAL-CONNECTIVITY-METRIC/`** — the direct sibling, `DONE`,
  merged, same batch position pattern (depends only on `WORLD-RENDER-CORE`, not on any other metric
  ticket). Its investigation.md documents the exact same "one-off verification code, never a named
  prototype script" situation for the connectivity BFS that this investigation independently confirmed
  for the CV formula — the precedent this ticket should follow for docstring provenance, module
  placement, and test structure.
- **`src/rendering/connectivity.py`** — the actual implemented precedent module (read in full):
  `@dataclass(frozen=True)` result type, a pure `analyze_connectivity(terrain, blocked_tiles) ->
  ConnectivityResult` function taking raw dict/set arguments (not a full `AuthoritativeState`), a
  docstring citing the exact `PROPOSAL.md` line range the algorithm was ported from, and an explicit
  note about why the walkability rule stops at steps 1-2 of `verify_occupancy`. This ticket's
  `src/rendering/density.py` should follow the identical shape: a frozen dataclass result, pure
  functions taking `entities`/`terrain` directly (not `AuthoritativeState`), and a docstring citing
  this investigation's traced provenance for the CV formula.
- **`tests/unit/rendering/test_connectivity.py`** — direct, reusable precedent for the real-corpus
  reproduction test: `WorldRepository("data/worlds").load_world(world_id)` →
  `WorldCompiler.compile(spec, seed=42)`, then asserting exact values (`walkable_count == 15245`,
  `component_count == 1`, `percent_reachable == 100.0`) — **no tolerance band, exact equality**,
  because the pipeline is confirmed fully deterministic. This ticket's own CV reproduction, per the
  finding above, is equally exact-reproducible (float values matched to 6+ significant figures), so
  the same "exact assertion, no tolerance" pattern is the right model — see Test Plan.
- **`src/simulation_quality/scorers/base.py:11`** — `class PillarScorer(ABC)`, the exact class AC #4
  forbids subclassing. `src/simulation_quality/scorers/{combat,economy,social,...}.py` all subclass it
  (`class XScorer(PillarScorer)`) — this ticket's module must not do the same.
- **`src/simulation_quality/quality_hub.py:9`** — `from src.observability.events import
  ObservabilityEventEnvelope`, the exact SimQ event-pipeline import AC #4 forbids. `src/simulation_quality/feed.py:76,98` shows the same import used to translate `ObservabilityEventEnvelope`
  instances into SimQ scoring input — this ticket's module must not import from
  `src.observability.events` or `src.simulation_quality.quality_hub`/`feed` at all; it computes
  directly from `AuthoritativeState.entities`/`terrain`, with no event in the loop, same as
  `connectivity.py`.

## Risks and Open Questions

- **AC #1's tolerance — resolved with evidence, not left open.** The ticket's own Assumptions section
  flags this as unresolved ("must be finalized during implementation"). Investigated directly (see
  Current Behavior above): the formula (population-std/mean of per-entity nearest Euclidean distance,
  active entities, seed 42, tick 0, no ticking) reproduces both documented numbers to 6+ significant
  figures — this is not an approximate match requiring a loose tolerance, it is the same kind of exact,
  deterministic reproduction `INFRA-370`'s connectivity test already established as the norm for this
  metric family. **Recommendation for the planner: assert exact-to-3-decimal-places equality**
  (`round(cv, 3) == 0.648` / `round(cv, 3) == 0.678`, or equivalently `abs(cv - 0.648) < 0.0005`) rather
  than a wide tolerance band — a wide band would under-specify a fully deterministic, exactly
  reproducible computation and could silently hide a formula regression (e.g. an accidental switch to
  sample-std, which produces a clearly different, non-matching number: 0.667/0.689). Do not use a loose
  tolerance (e.g. ±0.05) "to be safe" — the evidence does not support needing one.
- **Formula ambiguity was real and is now closed, not assumed away.** Population-std vs. sample-std
  produce visibly different results (0.648 vs 0.667 for `sandbox_world`) — only population-std matches.
  If the implementer or planner substitutes a different variance formula (e.g. NumPy's default `ddof=0`
  is actually correct here, but a naive `statistics.stdev()` call in the Python standard library
  defaults to **sample** stdev, `ddof=1`, and would silently produce the wrong number) this is a real,
  concrete failure mode to guard against explicitly in the implementation and in a test.
- **O(N²) is confirmed acceptable at current scale, Kernel.get_world_indexes flagged not adopted** (see
  Anti-Drift Hazards below for the full citation) — consistent with Out of Scope.
- **Entity count at tick 0 varies by world** (18 for `sandbox_world`, 32 for `dungeon_crawl`) — both
  well within the ticket's cited 11-32 range, no surprise here.
- **Whether `EntityState.active` (the production property) and the prototype's
  `getattr(ent.lifecycle, "active", True)` filter are exactly equivalent** — they are: `EntityState.active`
  is defined as `return self.lifecycle.active` (`src/core/state.py:772-773`), a direct passthrough, no
  default-True fallback needed since `lifecycle.active` always exists on a constructed `EntityState`.
  The `getattr(..., True)` in the prototype was defensive prototype-code caution, not evidence of a real
  attribute-absence case; production code can use the plain property.

## Anti-Drift Hazards

- **Do not use `statistics.stdev()` (sample std, ddof=1) — it silently produces the wrong number.**
  Confirmed by direct comparison above (0.667/0.689 vs the correct 0.648/0.678). Use population std
  (`statistics.pstdev()`, or a manual `sqrt(sum((d-mean)**2 for d in dists) / n)`) — the `n`, not `n-1`,
  divisor is load-bearing and must be explicit in a code comment given how easy this mistake is to make
  silently.
- **Do not fold in scoring/grading.** Per AC #4/Out of Scope and the exact same precedent
  `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`'s Anti-Drift Hazards already established for this batch:
  the function returns raw structural facts (the CV float, the histogram dict), not a grade/S-A-B-C-D-F
  band or a healthy/unhealthy verdict — `TCK-20260821-VISUAL-GRADE-SCORER` (batch position 6, depends
  on this ticket) owns that.
- **Do not implement `Kernel.get_world_indexes`/`entities_by_tile`-based O(N) scaling.** Out of Scope is
  explicit. `Kernel.get_world_indexes(state, dirty)` (`src/engine/kernel.py:1247-1255`, a thin
  delegation to `WorldIndexService.get_indexes`) and `WorldIndexes.entities_by_tile`
  (`src/engine/world_index.py:64-72`) are real and exist, confirmed by direct read — but reusing them
  for a grid-bucket nearest-neighbor approximation is explicitly deferred, per `PROPOSAL.md:401`'s own
  "flagged as the correct scaling path, not built" framing. `SpatialQueryService.nearby_entities`
  (`src/engine/spatial_query.py`) is the closest existing spatial-query helper but is **not directly
  reusable** even for reference: it requires a bounded `radius` parameter and uses **Manhattan**
  distance (`abs(dx) + abs(dy)`), not the unbounded, all-pairs, **Euclidean** nearest-neighbor query
  this metric needs — confirmed this is genuinely new O(N²) pairwise-distance code, not a
  reuse-in-disguise opportunity.
- **Do not create a `PillarScorer` subclass or import from `src.observability.events` /
  `src.simulation_quality.quality_hub` / `src.simulation_quality.feed`.** AC #4 is explicit; the exact
  base class (`src.simulation_quality.scorers.base.PillarScorer`) and the exact forbidden import
  (`from src.observability.events import ObservabilityEventEnvelope`) are cited above with file:line
  evidence — this module must have zero import from `src.simulation_quality.*` or
  `src.observability.events` at all.
- **Do not mutate `AuthoritativeState` or its `entities`/`terrain` collections.** `entities` values are
  `EntityState` (frozen-component dataclass); `terrain` is a plain mutable `dict`. Read-only access
  only, matching the connectivity ticket's own `test_does_not_mutate_authoritative_state` guard — this
  ticket's test plan should include an equivalent.
- **Do not silently change the histogram's key normalization.** The prototype's `terrain_histogram`
  counts **raw** (non-uppercased) terrain string values — it is built *before* `terrain_color()`'s
  `.upper()` normalization is applied, so `'PLAIN'` and `'plain'` remain distinct histogram keys (the
  real casing-fragmentation bug `TCK-20260821-WORLD-RENDER-CORE`'s investigation documented in detail).
  Extracting this computation must preserve that raw-key behavior exactly — normalizing keys during
  extraction would silently change the histogram's semantics and could make AC #2's sum-invariant test
  pass for the wrong reason while producing a different dict shape than the cited prototype evidence.
