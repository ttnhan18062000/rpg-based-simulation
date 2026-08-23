---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-SHAPE-METRIC
artifact_type: plan
tags: [visualization, simulation-quality, world]
---

# Implementation Plan — TCK-20260821-VISUAL-SHAPE-METRIC

## Summary

Add a new sibling module `src/rendering/shape.py` implementing connected-component-aware
fill-ratio and 90-degree rotation/repetition detection over `AuthoritativeState.terrain`,
following the exact structural precedent of `src/rendering/connectivity.py` and
`src/rendering/density.py` (frozen dataclass results, pure functions over raw dicts,
provenance docstring citing `PROPOSAL.md` line ranges, no `PillarScorer`/SimQ coupling). The
critical correctness requirement — verified directly against real corpus data in
investigation.md, not assumed — is that connected-component labeling must run once per
distinct raw terrain-type string value, grouped first, each within its own tile set; this is
the exact fix for the "per-terrain-type aggregate bounding box with no connectivity check"
bug `PROPOSAL.md §5c` documents. Fill-ratio is computed per component, never per
terrain-type aggregate. Rotation detection normalizes each component to its own origin and
tests three transforms (transpose, rotate-90-CW, rotate-90-CCW) gated on a bounding-box
dimension swap, with an explicit caveat documented in the docstring that solid
(fill_ratio == 1.0) rectangles cannot distinguish "true rotation" from other
dimension-swapping symmetries. AC #4's corpus-wide sweep is implemented against the *current*
21-world corpus (Test 10 only, per this plan's resolution of the open question below), not a
hardcoded 18-world historical subset. A new P2 entry `INFRA-372` is added to
`docs/parity_ledger/infrastructure.yaml`.

## Unresolved Questions

None. The one open question flagged by investigation.md (AC #4 corpus-drift, option a vs. b)
is resolved below in "Decision: AC #4 Corpus Scope" — this plan adopts investigation's
recommended option (b) and gives the explicit reasoning. No other decision in this ticket is
left ambiguous for the implementer.

## Decision: AC #4 Corpus Scope (Option b — confirmed, not overridden)

Investigation verified two real numbers: the full current 21-world corpus gives 37/46 (80.4%)
components ≥0.95 fill-ratio, every sub-0.95 component being `forest`/`FOREST` type with zero
exceptions; the historical 18-world subset (excluding `lifecycle_full_coverage_world`,
`quest_dense_frontier`, `simq_scale_stress_seed42`, which did not exist when `PROPOSAL.md`'s
sweep was performed) gives exactly 26/33 (78.8%), matching AC #4's literal cited figure.

This plan adopts option (b): implement only **Test 10**
(`test_corpus_wide_sweep_every_below_threshold_component_is_forest`), which asserts the
qualitative, corpus-size-independent invariant — every sub-0.95 component across whatever the
*current* `WorldRepository("data/worlds").list_worlds()` corpus is, is `forest` type — and
**do not implement Test 11** (the literal `26/33` historical reproduction via a hardcoded
3-world exclusion list).

Reasoning: a hardcoded exclusion list of 3 specific world IDs, whose only purpose is to force
an old, now-stale headline number to keep matching, is exactly the "editing an artifact to
make a check pass instead of fixing the underlying substance" pattern CLAUDE.md's Hard Rules
prohibit — here the "check" is the ticket's own AC #4 wording, and the "substance" is the real
structural finding (FOREST's generation mechanism is the one biome type that produces organic,
sub-rectangular shapes). That finding holds identically at 18, 21, or any future corpus size;
hardcoding world IDs to preserve a stale percentage would silently break, without any visible
failure, the next time a world is added or removed — precisely the drift CLAUDE.md's
Architecture Rule test-guard discipline exists to prevent. AC #4's acceptance criterion is
therefore satisfied by its *invariant content* (a high majority ≥0.95, and every exception is
FOREST), not its literal historical fraction; Step 8 below documents this explicitly in the
test's own docstring/comment so a future reader understands why 26/33 is not asserted.

## Steps

### Step 1 — Module skeleton, result dataclass, and terrain grouping

**Files:** `src/rendering/shape.py` (new)

**Change:** Create the module with the standard provenance docstring (mirroring
`connectivity.py:1-17` and `density.py:1-19`, cited above) explaining: (a) this ports
`PROPOSAL.md:365-380`'s BFS shape but must invoke it once per terrain-type string, not once
globally, per investigation.md's documented `PROPOSAL.md §5c` bug-fix finding; (b) no
prototype script exists to promote (investigation.md, confirmed via
`find experiments/spatial_rendering/prototype/ -iname "*shape*"` → no hits); (c) cites
`experiments/spatial_rendering/PROPOSAL.md:204` for the fill-ratio formula and
`PROPOSAL.md:431` plus investigation.md's reconstruction for the rotation heuristic.

Define:

```python
@dataclass(frozen=True)
class ShapeComponent:
    terrain_type: str
    tiles: frozenset[tuple[int, int]]
    size: int
    bbox: tuple[int, int, int, int]  # (min_x, min_y, max_x, max_y)
    fill_ratio: float


def group_terrain_by_type(terrain: dict[tuple[int, int], str]) -> dict[str, set[tuple[int, int]]]:
    """Groups tile positions by their raw, non-normalized terrain-type string value."""
```

`group_terrain_by_type` groups `terrain.items()` by the raw string value exactly as it
appears in the dict (no `.upper()`/`.lower()` normalization on the grouping key itself) — this
is the density sibling's Anti-Drift Hazard (`density.py:58-62`, `compute_terrain_histogram`,
cited above) applied identically here: grouping stays keyed on raw casing, only the
PLAIN/ROAD *exclusion test* in Step 3 is case-insensitive.

**Do NOT touch:** `connectivity.py`, `density.py`, `render.py`, `png_writer.py`,
`incremental.py`, `__init__.py` (confirmed empty via direct read — leave it empty, matching
both siblings, neither of which added an export there).

**Verify:** No standalone test for this step alone; covered transitively by Steps 2-3's tests
once `connected_components()` is built on top of it. (Test Plan does not list a dedicated
grouping-only test — grouping correctness is proven by Test 1's disjoint-patch assertion.)

### Step 2 — `connected_components()`: per-terrain-type BFS labeling with min-size filter

**Files:** `src/rendering/shape.py`

**Change:** Add:

```python
def _bfs_component(start, tile_set, visited) -> list[tuple[int, int]]:
    """Single BFS flood-fill over one pre-scoped tile_set, 4-connectivity."""


def connected_components(
    terrain: dict[tuple[int, int], str],
    min_size: int = 20,
    excluded_types: frozenset[str] = frozenset({"PLAIN", "ROAD"}),
) -> list[ShapeComponent]:
    """Groups terrain by raw type string (group_terrain_by_type), then runs BFS
    flood-fill labeling ONCE PER DISTINCT TYPE, scoped to that type's own tile set —
    never one global BFS across all terrain (that is connectivity.py's walkability
    question, a different question). Components smaller than min_size are dropped.
    Types whose UPPERCASED value is in excluded_types are skipped entirely (case-
    insensitive on the exclusion test only, per investigation.md; grouping itself
    stays keyed on raw casing)."""
```

The BFS body is a fresh copy of `connectivity.py:52-73`'s literal shape (4-directional
neighbor deque flood-fill, membership checked against the precomputed type-scoped tile set,
not by a live predicate call — reproducing `connectivity.py:65-69`'s documented reason for
that exact discipline: an unbounded live-predicate re-check would flood-fill past any tile
absent from the dict). Unlike `connectivity.py`, which builds exactly one `walkable_tiles`
set and calls BFS once (`connectivity.py:48-73`, `analyze_connectivity`), this function loops
over `group_terrain_by_type(terrain)`'s keys and calls the BFS helper fresh within each
type's own tile set — this is the load-bearing distinction investigation.md verified against
real corpus data (dungeon_crawl's `forest` key produces 2 components of 1,116 tiles each, not
1 aggregate blob).

`bbox` and `size`/`fill_ratio` are NOT computed in this step (deferred to Step 3, kept as a
separate pure function so fill-ratio's formula is independently unit-testable) — but since
`ShapeComponent` is frozen and fill_ratio is a required field, this step's `connected_components`
must call the Step 3 helper internally before constructing each `ShapeComponent`. Order Steps
2 and 3 as one coherent code unit; the split is for planning/verification granularity, not a
literal two-pass implementation.

**Do NOT touch:** `connectivity.py`'s BFS body itself — copy the shape, do not import or
refactor it into a shared helper (per investigation.md's Prior Work note: "the connectivity
module does not export a reusable `connected_components` helper — it inlines its own BFS body
directly... there is nothing today to import instead of writing a fresh copy").

**Verify:** Test 1 (`test_connected_component_labeling_splits_disjoint_same_type_patches`) —
the single most important guard, proves per-type BFS labeling splits disjoint same-type
patches into separate components rather than one aggregate. Test 2
(`test_dungeon_crawl_forest_is_two_components_of_1116_tiles_each`, AC #1) — real corpus,
exact equality. Test 8 (`test_min_component_size_filter_excludes_small_fragments`) — synthetic,
proves the `min_size=20` filter. Test 9
(`test_plain_and_road_excluded_case_insensitively`) — synthetic, proves the
`tval.upper() in {"PLAIN","ROAD"}` exclusion across all 4 real-corpus casing variants
(`'PLAIN'`, `'plain'`, `'ROAD'`, `'road'`, per investigation.md's confirmed corpus dump).

### Step 3 — `compute_fill_ratio()`: per-component bounding-box fill ratio

**Files:** `src/rendering/shape.py`

**Change:** Add:

```python
def compute_bbox(tiles: frozenset[tuple[int, int]]) -> tuple[int, int, int, int]:
    """(min_x, min_y, max_x, max_y) over this component's own tile coordinates only —
    never the terrain-type's aggregate bounding box (that was the pre-fix bug,
    PROPOSAL.md §5c)."""


def compute_fill_ratio(tiles: frozenset[tuple[int, int]]) -> float:
    """len(tiles) / bounding_box_area, where bounding_box_area =
    (max_x - min_x + 1) * (max_y - min_y + 1), computed per connected component.
    Formula: PROPOSAL.md:204 ('tiles_of_type / bounding_box_area'), applied per
    component per PROPOSAL.md:383-385's correction, verified against real running
    code in investigation.md (dungeon_crawl: CAVE=0.9804, FOREST-c0=1.0000,
    FOREST-c1=1.0000, RUIN=1.0000)."""
```

`connected_components()` (Step 2) calls both of these per raw BFS component before
constructing each `ShapeComponent(bbox=..., fill_ratio=...)`.

**Do NOT touch:** Do not compute or expose any terrain-type-level aggregate fill-ratio
anywhere in this module — no function may sum `len(tiles)` or bounding boxes across multiple
components of the same type. This is the single hazard investigation.md calls out most
explicitly (re-introducing it silently reproduces `FOREST`'s wrong `0.716`).

**Verify:** Test 3
(`test_dungeon_crawl_per_component_fill_ratios_match_documented_evidence`, AC #2) — real
corpus, exact-to-3dp: CAVE=0.980, FOREST-c0=1.000, FOREST-c1=1.000, RUIN=1.000. Test 4
(`test_fill_ratio_formula_on_synthetic_shapes`) — synthetic 4x4 square, L-shape, single tile,
independent of corpus data.

### Step 4 — Rotation/repetition detection between two components

**Files:** `src/rendering/shape.py`

**Change:** Add:

```python
def _normalize(tiles: frozenset[tuple[int, int]], min_x: int, min_y: int) -> frozenset[tuple[int, int]]:
    """{(x - min_x, y - min_y) for x, y in tiles} -- shift a component's tiles to its own origin."""


def detect_rotation_match(a: ShapeComponent, b: ShapeComponent) -> bool:
    """Tests whether component b's tile pattern matches a 90-degree rotation (or
    transpose) of component a's tile pattern.

    Gated first on bounding-box dimension swap: w_a == h_b and h_a == w_b, where
    w = max_x - min_x, h = max_y - min_y (using the un-normalized bbox from Step 3).
    If the dimensions do not swap, returns False immediately -- no tile comparison
    needed.

    If gated, normalizes both components' tiles to their own origin (_normalize) and
    tests three transforms of a's normalized set against b's normalized set:
      - transpose:      (x, y) -> (y, x)
      - rotate-90-CW:    (x, y) -> (y, w_a - x)
      - rotate-90-CCW:   (x, y) -> (h_a - y, x)
    Returns True if ANY of the three transformed sets equals b's normalized tile set.

    NOTE (fixed during Review, TCK-20260821-VISUAL-SHAPE-METRIC): w_a/h_a here are
    bounding-box EXTENTS (max_x - min_x, max_y - min_y), not tile-count widths/heights
    -- the formula must NOT subtract an additional 1, since that offset is only correct
    if w_a/h_a were counts (max_x - min_x + 1). Verified directly: for a 3-wide x 2-tall
    rectangle (w_a=2, h_a=1), (x,y) -> (y, w_a - x) correctly produces a 2-wide x 3-tall
    rotated shape with all-non-negative coordinates; the "- 1" variant produces negative
    coordinates and never matches any real rotated pair, which would silently break
    Test 7 (test_rotation_detection_on_solid_rectangles_is_not_over_claimed) while AC #3
    itself still passes (transpose alone already matches the real FOREST pair, masking
    the bug). Implementer: use (y, w_a - x) and (h_a - y, x) exactly as corrected here.

    CAVEAT (do not remove or soften this docstring paragraph): for solid
    (fill_ratio == 1.0) rectangular components, all three transforms coincide
    identically -- a filled rectangle's tile set is invariant under any of them once
    the bounding-box dimensions swap correctly. This function's True result does NOT
    by itself distinguish "true 90-degree rotation" from any other dimension-swapping
    symmetry for such shapes; it is diagnostic only for non-rectangular, textured
    components (investigation.md, TCK-20260821-VISUAL-SHAPE-METRIC)."""
```

**Do NOT touch:** Do not add a 180-degree or reflection/mirror transform — out of scope; the
ticket and investigation only establish transpose + two 90-degree rotations, gated on the
real documented FOREST-pair finding.

**Verify:** Test 5 (`test_forest_components_detected_as_90_degree_rotation`, AC #3) — real
corpus, dungeon_crawl's two FOREST components (bboxes 36×31 and 31×36) return a positive
match. Test 6 (`test_rotation_detection_rejects_non_rotated_shapes`) — synthetic negative
case, an L-shape vs. its non-matching mirror with swapped bbox dims, proves the function
actually compares tile-set contents and does not just check the bbox dimension swap. Test 7
(`test_rotation_detection_on_solid_rectangles_is_not_over_claimed`) — synthetic, proves all
three transforms independently match for two solid same-area rectangles, documenting the
caveat above as executable behavior, not just prose.

### Step 5 — Architecture guards: no PillarScorer, no SimQ/observability import, no render/image dependency

**Files:** `src/rendering/shape.py` (verify only — no new production code required beyond
Steps 1-4's already-clean imports)

**Change:** Confirm `shape.py`'s only imports are `from __future__ import annotations`,
`collections.deque`, `dataclasses.dataclass` (mirroring `connectivity.py:18-21` and
`density.py:20-23`'s minimal import lists exactly) — no `src.simulation_quality.*`, no
`src.observability.events` (the exact forbidden import is
`from src.observability.events import ObservabilityEventEnvelope`, re-verified by
investigation at `src/simulation_quality/quality_hub.py:9`), no `src.rendering.png_writer` /
`src.rendering.render` / `src.rendering.incremental`, and no class in the module has
`PillarScorer` (`src/simulation_quality/scorers/base.py:11`) in its base-class list. This step
is a checklist against Steps 1-4's actual output, not new code — if any step above
accidentally introduced one of these imports, remove it here.

**Do NOT touch:** `src/simulation_quality/scorers/base.py`, `src/simulation_quality/quality_hub.py`,
`src/observability/events.py` — read-only citation sources only, never edited by this ticket.

**Verify:** Test 12
(`test_shape_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`, AC #5),
Test 13 (`test_shape_module_has_zero_image_or_render_dependency`).

### Step 6 — Read-only / non-mutation guard

**Files:** `src/rendering/shape.py` (verify only)

**Change:** Confirm no function in the module mutates its `terrain` dict argument in place
(no `del`, no `terrain[...] = ...`, no `.pop()`/`.clear()` on the input). All internal working
sets/lists are freshly constructed (`group_terrain_by_type` builds new `set()` objects per
key; `ShapeComponent.tiles` is a `frozenset` copy, never a live view into the input). This
mirrors both siblings' `test_does_not_mutate_authoritative_state`-shaped guard, per
investigation.md's Anti-Drift Hazards.

**Do NOT touch:** `src/core/state.py`'s `AuthoritativeState` definition — this module only
consumes `terrain: dict[tuple[int,int], str]` as a raw argument (matching both siblings'
convention of taking raw dicts, not a full `AuthoritativeState`), never imports or constructs
`AuthoritativeState` itself.

**Verify:** Test 14 (`test_does_not_mutate_authoritative_state`) — calling shape functions
twice against the same fixture produces identical results, and the input dict is byte-for-byte
unchanged after the calls.

### Step 7 — New test file `tests/unit/rendering/test_shape.py`

**Files:** `tests/unit/rendering/test_shape.py` (new)

**Change:** Implement all 13 tests from test_plan.md (Tests 1-10, 12-14 — Test 11 explicitly
NOT written, per the Decision above) as a single new test module, mirroring
`tests/unit/rendering/test_connectivity.py`'s and `test_density.py`'s structure: real-corpus
tests use `WorldRepository("data/worlds").load_world(world_id)` →
`WorldCompiler.compile(spec, seed=42)` (tick 0, no `Kernel.tick_once()` calls), synthetic
tests build small hand-constructed `terrain: dict[tuple[int,int], str]` fixtures directly.
Test 10 iterates `WorldRepository("data/worlds").list_worlds()` (the full current corpus,
whatever size it is at test-run time — do not hardcode `21`) and asserts every fill-ratio
result below 0.95 has `terrain_type.upper() == "FOREST"`.

**Do NOT touch:** `tests/unit/rendering/test_connectivity.py`,
`tests/unit/rendering/test_density.py`, or any other file listed in test_plan.md's
Regression Surface — those must keep passing unmodified as regression evidence, not be edited
to accommodate this ticket.

**Verify:** `.venv/bin/python3 -m pytest tests/unit/rendering/ -v` — full new file plus
unmodified regression surface all green. `.venv/bin/python3 -m pytest tests/simulation_quality/ -q`
— still green modulo the documented 41 pre-existing `test_grade_regression.py` failures
(unrelated `PROGRESSION`-pillar score-tolerance drift, not caused by this ticket's diff, do
not attempt to fix).

### Step 8 — Parity ledger entry `INFRA-372`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Verified directly this session (`grep -n "^- id:" docs/parity_ledger/infrastructure.yaml | tail`)
that `INFRA-371` (lines 10850-10860, the density sibling's entry) is the real current max ID —
confirming investigation.md's claim, not assuming it. Append a new entry after `INFRA-371`
(after line 10860), following its exact field shape:

```yaml
- id: INFRA-372
  text: Connected-component-aware fill-ratio (per-terrain-type BFS labeling, tiles /
    bounding_box_area per component) plus 90-degree rotation/repetition detection
    (transposed-coordinate set match) reproduces documented dungeon_crawl evidence
    (FOREST=2 components of 1,116 tiles each; CAVE=0.980, FOREST-c0/c1=1.000,
    RUIN=1.000; FOREST component 1 is component 0 rotated 90 degrees) deterministically
    from AuthoritativeState.terrain at seed 42, tick 0. A corpus-wide sweep across the
    current data/worlds corpus confirms every component scoring below the 0.95
    reference threshold is FOREST type -- the 0.95 threshold itself is uncalibrated
    and provisional, tracked separately (TCK-20260821-VISUAL-QUALITY-CALIBRATION).
  status: verified
  priority: P2
  v2_evidence: src/rendering/shape.py
  test_path: tests/unit/rendering/test_shape.py::test_dungeon_crawl_forest_is_two_components_of_1116_tiles_each
  divergence_note: null
  proof_type: parity
```

**Do NOT touch:** Any other entry in `infrastructure.yaml` (`INFRA-369`/`INFRA-370`/`INFRA-371`
stay exactly as-is); do not touch `docs/simulation_quality/quality_scoring_contract.md` or
`docs/plans/world_rendering/idea_world_render_validation.md` (investigation.md explicitly
confirms both are out of scope — the idea doc's final-contract documentation belongs to the
batch's last ticket, `TCK-20260821-VISUAL-QUALITY-DOCS`).

**Verify:** No automated test covers ledger prose directly; `done-checker`'s
`frontmatter_valid`/ledger-consistency checks and manual review confirm the entry's shape
matches `INFRA-370`/`INFRA-371`'s precedent exactly (same 8 fields, same field order).

## Scope Guards

The following are explicitly read-only context for this ticket and must not be modified:

- `src/simulation_quality/` (entire directory, including `scorers/base.py`, `quality_hub.py`,
  `pillars.py`, `feed.py`) — this module is an architecturally independent sibling, not a
  pillar (AC #5, Out of Scope).
- `src/observability/events.py` — no import, no edit.
- `src/rendering/connectivity.py` — direct structural precedent, cited/copied-from but never
  imported or edited.
- `src/rendering/density.py` — direct structural precedent, cited but never imported or
  edited.
- `src/rendering/render.py` — no image/render dependency permitted in this module (Test 13).
- `experiments/spatial_rendering/` (entire directory, including `PROPOSAL.md` and
  `prototype/`) — read-only source for porting the algorithm's shape; nothing under
  `experiments/` is written to.
- `config/simulation_quality/grade_thresholds.yaml` — threshold calibration is
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s scope, not this ticket's.
- `docs/simulation_quality/quality_scoring_contract.md` and
  `docs/plans/world_rendering/idea_world_render_validation.md` — investigation.md confirms
  both are out of scope for this ticket.
- Any rectangle-decomposition fix to the "composite of unioned rectangles scores artificially
  low" fill-ratio weakness (`PROPOSAL.md:393`) — must be documented as a stated limitation in
  `shape.py`'s docstring only, never solved.
- `src/rendering/__init__.py` — confirmed empty; leave empty (neither sibling added an
  export).

## Dependency Map

Steps 1-4 are sequential within `shape.py` (Step 2 depends on Step 1's grouping helper; Step 2
depends on Step 3's fill-ratio helper to populate `ShapeComponent`; Step 4 depends on Step
2/3's `ShapeComponent` type). Steps 5 and 6 are verification-only checklist passes over Steps
1-4's output and can be done in either order once Steps 1-4 are complete. Step 7 (test file)
depends on Steps 1-6 being complete (tests exercise the finished module). Step 8 (parity
ledger) is independent of all code steps and can be done at any point, but logically follows
Step 7 since its `test_path` citation must point at a real, passing test.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: `connected_components()` on dungeon_crawl's FOREST reproduces 2 components of 1,116 tiles each, not 1 | Step 2 | Test 2 (`test_dungeon_crawl_forest_is_two_components_of_1116_tiles_each`) |
| AC #2: Per-component fill-ratio reproduces CAVE=0.980, FOREST-c0=1.000, FOREST-c1=1.000, RUIN=1.000 | Step 3 | Test 3 (`test_dungeon_crawl_per_component_fill_ratios_match_documented_evidence`) |
| AC #3: Rotation detection reproduces the documented 90-degree-rotation finding between the two FOREST components | Step 4 | Test 5 (`test_forest_components_detected_as_90_degree_rotation`) |
| AC #4: Corpus-wide run reproduces the "high majority ≥0.95, every sub-0.95 is FOREST" finding — implemented against the CURRENT full corpus (Decision above), not the literal historical 18-world/26-33 figure | Step 2 (min-size + exclusion filters), Step 3 (fill-ratio) | Test 10 (`test_corpus_wide_sweep_every_below_threshold_component_is_forest`) only; Test 11 deliberately not implemented, per Decision section |
| AC #5: No PillarScorer subclass, no ObservabilityEventEnvelope/QualityHub import | Step 5 | Test 12 (`test_shape_module_does_not_subclass_pillar_scorer_or_import_simq_event_pipeline`), plus a still-green `tests/simulation_quality/` run |

## Anti-Drift Notes

- **Test 1 is the single most important test in this plan.** It is the direct regression
  guard for the exact bug `PROPOSAL.md §5c` found and fixed — per-terrain-type aggregation
  without per-component connectivity labeling. A well-intentioned "simplification" back to one
  global bounding box per terrain type would silently reproduce FOREST's wrong `0.716` while
  still passing a naive fill-ratio-formula-only test (Test 4). Do not let any refactor collapse
  Step 2's per-type BFS loop into a single aggregate pass.
- **Do not conflate this module's per-terrain-type BFS with `connectivity.py`'s single
  walkability-based BFS.** They answer different questions ("how many patches does each biome
  type form" vs. "is the whole map one reachable region") and must never be merged or share a
  code path beyond the copied BFS shape.
- **Rotation detection's docstring caveat (Step 4) must not be softened or removed.** For
  solid rectangular components, transpose/rotate-CW/rotate-CCW all coincide trivially — Test 7
  exists specifically to keep this honest as executable behavior, not just prose. Do not let a
  future edit claim "true rotation detected" as a blanket description of what `detect_rotation_match`
  proves.
- **PLAIN/ROAD exclusion is case-insensitive on the exclusion test only** (`tval.upper() in
  {"PLAIN", "ROAD"}`) — the grouping key in `group_terrain_by_type` must stay keyed on the raw,
  non-normalized string exactly as it appears in `terrain.values()`, per the density sibling's
  established Anti-Drift Hazard. Do not normalize casing at the grouping stage.
- **The `min_size=20` filter is currently untested against real corpus data** (smallest real
  component is 310 tiles, per investigation.md) — its only coverage is Test 8's synthetic
  fixture. Do not treat its absence of real-corpus test failures as proof it works; do not
  delete it as apparently-dead code.
- **AC #4's literal `26/33`/`78.8%` figures are historical, not asserted by this plan's tests**
  — see the Decision section above. If a future reviewer expects to find a test reproducing
  `26/33` exactly, point them to this plan's explicit reasoning, not a silent omission.
- **This module returns raw structural facts only** — `ShapeComponent`, floats, and booleans,
  never a grade/S-A-B-C-D-F band or healthy/unhealthy verdict. `TCK-20260821-VISUAL-GRADE-SCORER`
  (depends on this ticket) and `TCK-20260821-VISUAL-QUALITY-CALIBRATION` own scoring/grading and
  threshold calibration respectively — do not fold either in here.
