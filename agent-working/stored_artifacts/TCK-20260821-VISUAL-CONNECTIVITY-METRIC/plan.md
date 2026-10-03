---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-VISUAL-CONNECTIVITY-METRIC
artifact_type: plan
tags: [visualization, simulation-quality, world]
---

# Implementation Plan — TCK-20260821-VISUAL-CONNECTIVITY-METRIC

## Summary

Add a new pure-function module, `src/rendering/connectivity.py`, implementing whole-map
walkable-region connectivity as a deque-based 4-directional BFS flood-fill over
`terrain`/`blocked_tiles`, ported from the cited algorithm shape in
`experiments/spatial_rendering/PROPOSAL.md:362-380` and adapted to (a) walk a walkability
predicate instead of a `tiles_of_type` set, and (b) return a richer structured result
(walkable tile count, connected-component count, per-component sizes, and a derived
`percent_reachable`) instead of a bare list of components. The walkability rule is fixed
exactly to `LegalityServiceV2.verify_occupancy`'s first two checks
(`src/engine/legality.py:71-77`): a tile is walkable iff `terrain.get(pos) != "WALL"` AND
`pos not in blocked_tiles`. The function takes `terrain: dict` and `blocked_tiles: set`
directly as plain-typed parameters — not a full `AuthoritativeState` — to keep it a
narrowly-scoped, independently-testable pure geometry function, consistent with the
ticket's "Pure geometry computation, no data-lookup checks" scope line. `percent_reachable`
is defined as `(size of the largest connected component / total walkable tile count) * 100`
(dominant-region reachability), which reduces to 100.0 in the single-component case and is
the definition both new multi-component tests must assert. Five new tests land in
`tests/unit/rendering/test_connectivity.py`, plus one new P2 parity-ledger entry,
`INFRA-370`, in `docs/parity_ledger/infrastructure.yaml`.

## Steps

### Step 1 — Implement the connectivity module

**Files:** `src/rendering/connectivity.py` (new file)

**Change:**
Create the module with this exact public signature:

```python
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectivityResult:
    walkable_count: int
    component_count: int
    component_sizes: list[int]
    percent_reachable: float


def is_walkable(pos: tuple[int, int], terrain: dict, blocked_tiles: set) -> bool:
    ...


def analyze_connectivity(
    terrain: dict[tuple[int, int], str],
    blocked_tiles: set[tuple[int, int]],
) -> ConnectivityResult:
    ...
```

- `is_walkable(pos, terrain, blocked_tiles)`: returns `False` if
  `terrain.get(pos) == "WALL"`, else `False` if `pos in blocked_tiles`, else `True`. This is
  exactly `LegalityServiceV2.verify_occupancy`'s first two checks, read directly at
  `src/engine/legality.py:71-77` ("1. Static Terrain (WALL / blocked_tiles)": `if
  terrain_map.get(target_grid_pos) == "WALL": return False, ...` then `if target_grid_pos in
  blocked_tiles: return False, ...`). Steps 3-5 of `verify_occupancy` (buildings, transient
  claims, live entity occupancy — `legality.py:79-114`) are deliberately NOT ported; they are
  data-lookups against mutable per-tick state, explicitly excluded by the ticket's Scope
  bullet 3.
- `analyze_connectivity(terrain, blocked_tiles)`: builds the walkable tile set by iterating
  `terrain.keys()` (the only source of candidate tile coordinates — `terrain` is the full
  static tile-truth map per `src/core/state.py:1126`, `Dict[tuple[int, int], str]`, "Local
  tile truth (WALL, FOREST, etc)") and filtering with `is_walkable`. Then runs the
  deque-based 4-directional BFS flood-fill ported from
  `experiments/spatial_rendering/PROPOSAL.md:362-380` (verbatim shape: `visited: set`,
  `components: list`, outer loop over unvisited walkable tiles, inner `deque` BFS over the 4
  cardinal neighbors `[(1,0),(-1,0),(0,1),(0,-1)]`, each neighbor accepted only if it is
  itself walkable and unvisited), adapted so the membership test used inside the BFS loop is
  `is_walkable(nb, terrain, blocked_tiles)` instead of `nb in tiles_of_type`. Collects each
  component's tile list, computes `walkable_count = len(walkable_tiles)`,
  `component_count = len(components)`, `component_sizes = [len(c) for c in components]`
  sorted descending, and `percent_reachable = (max(component_sizes) / walkable_count) * 100.0`
  if `walkable_count > 0` else `0.0`. Returns a `ConnectivityResult`.
- **Read-only guarantee**: the function must never write into the caller's `terrain` dict or
  `blocked_tiles` set. Only local `visited`/`components`/`walkable_tiles` containers are
  mutated internally; the two input containers are only read (`.get`, `in`, `.keys()`).
- Module docstring should follow the promotion-attribution convention seen in
  `src/rendering/render.py:1-13` ("Promoted from experiments/spatial_rendering/prototype/...
  (TCK-...)")  but adapted for the fact there is no committed prototype script to point to —
  state instead that the algorithm is ported from the inline example at
  `experiments/spatial_rendering/PROPOSAL.md:362-380` (TCK-20260821-VISUAL-CONNECTIVITY-METRIC),
  since `PROPOSAL.md:470` explicitly confirms this ran as one-off verification code, never
  saved as a named prototype script.

**Do NOT touch:** `src/engine/legality.py` (read-only reference for the walkability rule —
do not import from it or modify it; re-implement the two checks locally per above),
`src/core/state.py` (read-only reference for field shapes — do not modify
`AuthoritativeState`), `src/rendering/__init__.py` (currently empty/0 lines — no import
wiring needed; leave it empty, matching the existing convention that `png_writer.py`,
`render.py`, and `incremental.py` are also not re-exported through `__init__.py`).

**Verify:** `test_connected_map_is_one_component_fully_reachable`,
`test_two_disconnected_islands_reports_correct_component_count`,
`test_blocked_tiles_alone_can_fragment_connectivity`,
`test_does_not_mutate_authoritative_state` (test_plan.md items 1-4).

### Step 2 — Synthetic-fixture unit tests

**Files:** `tests/unit/rendering/test_connectivity.py` (new file)

**Change:** Add four tests, all using plain synthetic `terrain`/`blocked_tiles`
dict/set fixtures (no `AuthoritativeState` construction needed, per the ticket's own scope
line that this is pure geometry over just those two fields, and per test_plan.md item 1's
explicit note that a full `AuthoritativeState` is unnecessary here):

1. `test_connected_map_is_one_component_fully_reachable` — build a small fully-connected
   grid (e.g. all tiles in a 5x5 block, all non-`"WALL"` values, empty `blocked_tiles`).
   Assert `result.walkable_count == 25`, `result.component_count == 1`,
   `result.percent_reachable == 100.0`.
2. `test_two_disconnected_islands_reports_correct_component_count` — build two separate
   walkable regions (e.g. two 3x3 blocks) separated by a row/column of `"WALL"` tiles with no
   shared cardinal-adjacent walkable tile between them. Assert `component_count == 2`,
   `walkable_count == 18` (sum of both islands), and
   `percent_reachable == (9 / 18) * 100.0 == 50.0` (equal-size islands, so this exercises the
   dominant-region formula's tie case explicitly — the largest of two equal components is
   still well-defined via `max()`). Add a variant, `test_three_disconnected_islands_reports_correct_component_count`,
   with 3 islands of unequal size (e.g. 9, 6, 3 tiles; `walkable_count == 18`,
   `component_count == 3`, `percent_reachable == (9 / 18) * 100.0 == 50.0`, i.e. the largest
   island's share) to catch an off-by-one in the BFS/visited-set loop beyond the 2-component
   case, per test_plan.md item 2's recommended extra coverage.
3. `test_blocked_tiles_alone_can_fragment_connectivity` — build a grid with **no** `"WALL"`
   terrain value anywhere, but a `blocked_tiles` set forming a complete barrier row/column
   between two regions. Assert `component_count >= 2`, proving `blocked_tiles` alone (not
   just `terrain`) is consulted by `is_walkable`.
4. `test_does_not_mutate_authoritative_state` — build a `terrain`/`blocked_tiles` fixture,
   snapshot copies (`terrain_before = dict(terrain)`, `blocked_before = set(blocked_tiles)`),
   call `analyze_connectivity(terrain, blocked_tiles)` twice, and assert (a) both calls
   return identical `ConnectivityResult` values, and (b) `terrain == terrain_before` and
   `blocked_tiles == blocked_before` after both calls — confirming no in-place mutation of
   the mutable dict/set containers, per the architecture guard in CLAUDE.md's Testing Rule
   ("Architecture tests: verify read-only logic did not mutate live state").

Each test comment should cite which `percent_reachable` definition is being asserted
(dominant-largest-component formula) so the choice is not silently ambiguous in the test
suite itself, per test_plan.md item 2's explicit instruction.

**Do NOT touch:** any other file under `tests/unit/rendering/` (existing renderer tests must
keep passing unmodified — this step is purely additive).

**Verify:** `pytest tests/unit/rendering/test_connectivity.py -v` (all 5 tests, including the
Step 3 real-corpus test added below, pass).

### Step 3 — Real-corpus reproduction test (AC #1)

**Files:** `tests/unit/rendering/test_connectivity.py` (same file as Step 2, appended)

**Change:** Add `test_dungeon_crawl_matches_documented_evidence`, following the exact
load/compile pattern confirmed at `tests/unit/rendering/test_render_incremental.py:29-32`:

```python
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

def test_dungeon_crawl_matches_documented_evidence():
    repo = WorldRepository("data/worlds")
    spec = repo.load_world("dungeon_crawl")
    state, _report = WorldCompiler.compile(spec, seed=42)
    result = analyze_connectivity(state.terrain, state.blocked_tiles)
    assert result.walkable_count == 15245
    assert result.component_count == 1
    assert result.percent_reachable == 100.0
```

Per investigation.md's Risk section and test_plan.md item 5: if this does not reproduce
exactly `15245 / 1 / 100.0` on first run, treat it as a real finding to report honestly (the
one-off source that originally produced these numbers was never a committed, fixed-seed
script) — do NOT adjust the walkability rule or silently change the expected numbers to
force a match. Report the actual observed numbers instead and flag the discrepancy in the
ticket's Implementation Notes.

**Do NOT touch:** `data/worlds/dungeon_crawl/` (read-only corpus fixture — do not regenerate
or edit).

**Verify:** `test_dungeon_crawl_matches_documented_evidence` (test_plan.md item 5) —
reproduces 15,245 walkable tiles / 1 component / 100.0% reachable, OR is reported as a
finding if it does not.

### Step 4 — Parity ledger entry

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Confirmed via direct read that the current highest ID in the file is
`INFRA-369` (`docs/parity_ledger/infrastructure.yaml:10831`, "Batch world rendering to PNG
from AuthoritativeState is deterministic", `status: verified`, `priority: P0`,
`v2_evidence: src/rendering/render.py`). No ticket has landed a higher ID since the
investigation was written (grep re-confirmed at plan time). Append a new entry directly
after `INFRA-369` (after line 10839, the `proof_type: parity` line closing that entry):

```yaml
- id: INFRA-370
  text: BFS whole-map walkable-region connectivity (terrain != WALL minus blocked_tiles)
    reproduces documented walkable-tile count, connected-component count, and
    percent-reachable deterministically from AuthoritativeState.terrain + blocked_tiles.
  status: verified
  priority: P2
  v2_evidence: src/rendering/connectivity.py
  test_path: tests/unit/rendering/test_connectivity.py::test_dungeon_crawl_matches_documented_evidence
  divergence_note: null
  proof_type: parity
```

Only set `status: verified` if Step 3's test actually passes with the documented numbers; if
Step 3 surfaces a real drift finding instead, use `status: divergent` and fill
`divergence_note` with the observed vs. documented numbers instead of forcing `verified`.
Priority is `P2` (not `P0`), matching the investigation's recommendation, because this
metric is explicitly report-only and never CI-gated (ticket Out of Scope).

**Do NOT touch:** any other entry in `infrastructure.yaml`, in particular `INFRA-369` itself
(read-only sibling precedent, do not modify). Do NOT touch
`docs/plans/world_rendering/idea_world_render_validation.md` — deliberately deferred to the
batch's final ticket, `TCK-20260821-VISUAL-QUALITY-DOCS`, per `SEQUENCE.md`.

**Verify:** no automated test covers the parity ledger entry directly; verified by visual
diff review during Verify phase and by `docs/REGISTRY.yaml` regeneration at ticket close
picking up the new entry without validation errors.

## Scope Guards

Must NOT be touched by this ticket:

- `src/engine/legality.py` — read-only reference for the walkability rule. The two checks
  are re-implemented locally in `connectivity.py`'s `is_walkable`, not imported, since
  `verify_occupancy` bundles building/claim/entity checks this ticket must not pull in.
- `src/core/state.py` — read-only reference for `AuthoritativeState.terrain` /
  `.blocked_tiles` field shapes. No changes to the dataclass.
- `src/simulation_quality/pillars.py` and any other `src/simulation_quality/` file — this
  metric is an architecturally-independent SimQ-sibling, not a pillar; no scoring/grading
  integration here (that is `TCK-20260821-VISUAL-GRADE-SCORER`'s scope).
- `docs/plans/world_rendering/idea_world_render_validation.md` — deferred to
  `TCK-20260821-VISUAL-QUALITY-DOCS`.
- Any `data/worlds/*` other than `dungeon_crawl` — no corpus-sweep test; broader coverage is
  `TCK-20260821-VISUAL-QUALITY-CALIBRATION`'s scope.
- `tests/parity/` — no test in this ticket carries a `@pytest.mark.parity` marker or lives
  under that directory (AC #5).
- Any CI/regression-baseline/gate script (e.g. `tests/tools/test_parity_index_baseline.py`)
  — this metric is never CI-gated (Out of Scope).
- `src/rendering/render.py`, `src/rendering/png_writer.py`, `src/rendering/incremental.py`,
  and their existing tests — purely additive sibling module, no edits to existing renderer
  files.

## Dependency Map

All four steps are largely independent and can be implemented/verified in any order, with
one soft ordering preference: Step 1 (the module) should land before Steps 2-3 (its tests)
since the tests import `analyze_connectivity`/`ConnectivityResult` from it. Step 4 (docs) is
fully independent of the other three and can be done last, after Step 3's real-corpus test
result is known (so `status: verified` vs `status: divergent` can be set correctly).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| BFS connectivity function using exactly `verify_occupancy`'s walkability rule reproduces dungeon_crawl: 15,245 walkable tiles, 1 component, 100% reachable | Step 1 (rule + BFS), Step 3 (real-corpus test) | `test_dungeon_crawl_matches_documented_evidence` |
| Function returns raw structural facts (walkable count, component count) plus derived percent-reachable, not just pass/fail | Step 1 (`ConnectivityResult` dataclass) | `test_connected_map_is_one_component_fully_reachable`, `test_two_disconnected_islands_reports_correct_component_count` |
| New test covers a fully-connected map case | Step 2 | `test_connected_map_is_one_component_fully_reachable` |
| New test covers a constructed map with >=2 disconnected islands | Step 2 | `test_two_disconnected_islands_reports_correct_component_count`, `test_three_disconnected_islands_reports_correct_component_count` |
| Tests live under `tests/unit/`, no `tests/parity/` marker | Step 2, Step 3 | all tests in `tests/unit/rendering/test_connectivity.py`; confirmed by file location and absence of `@pytest.mark.parity` |

## Anti-Drift Notes

- **Walkability rule is fixed, not negotiable.** Exactly `terrain.get(pos) == "WALL"` OR
  `pos in blocked_tiles` → not walkable, per `legality.py:71-77`. Do not add
  building/claim/entity checks even though `verify_occupancy` itself has them
  (`legality.py:79-114`) — that would violate the ticket's "Pure geometry computation, no
  data-lookup checks" scope line.
- **`percent_reachable` definition is now settled by this plan**: `(largest component size /
  total walkable count) * 100`. This resolves the investigation's flagged open question.
  Both multi-island tests in Step 2 must assert this exact formula's numeric result, not
  `100.0` and not a `component_count == 1` boolean-style check.
- **No mutation of `terrain`/`blocked_tiles`.** Both are mutable containers (`dict`/`set`) on
  an otherwise-frozen `AuthoritativeState`; `analyze_connectivity` must only read them. Step
  2's `test_does_not_mutate_authoritative_state` is the concrete guard — do not treat it as
  optional filler.
- **AC #1 numbers are real but were produced by uncommitted one-off code.** If Step 3's test
  does not reproduce 15,245/1/100.0% exactly, report the actual observed numbers as a real
  finding in the ticket's Implementation Notes — do not adjust the algorithm or the expected
  test values to force a match.
- **No grading, scoring, or threshold logic anywhere in this module or its tests.** AC #2 is
  explicit: raw structural facts + a derived ratio, nothing else. Grade-band integration
  belongs to `TCK-20260821-VISUAL-GRADE-SCORER`.
- **`src/rendering/__init__.py` is empty (0 lines) and stays that way** — confirmed by direct
  read at plan time; the existing renderer siblings (`png_writer.py`, `render.py`,
  `incremental.py`) are not re-exported through it either, so `connectivity.py` should follow
  the same pattern (imported directly by its full module path in tests, not via package
  `__init__`).

## Deviations

Recorded during implementation (see `tickets/inprogress/TCK-20260821-VISUAL-CONNECTIVITY-METRIC.md`'s
Implementation Notes for the full account).

- **Step 1's BFS neighbor-membership test.** This plan's Step 1 (line ~87) instructed: "the
  membership test used inside the BFS loop is `is_walkable(nb, terrain, blocked_tiles)`
  instead of `nb in tiles_of_type`." Implemented literally, this hangs on any synthetic
  fixture with an open boundary: `is_walkable` calls `terrain.get(pos)`, which returns `None`
  (not `"WALL"`) for any coordinate absent from `terrain`, so an unbounded re-check inside the
  BFS loop treats the entire infinite 2D plane outside the fixture as walkable and the BFS
  never terminates. Confirmed via a hard timeout on the very first, simplest synthetic test
  (a plain 5x5 open grid, no boundary walls) — not a corner case.

  **Fix:** check `nb in walkable_tiles` (the precomputed, closed set of walkable coordinates,
  already filtered by `is_walkable` from `terrain.keys()`) instead of re-calling
  `is_walkable(nb, ...)` inside the BFS loop. This restores the original
  `PROPOSAL.md:362-380` algorithm's bounded-membership structure (`nb in tiles_of_type`) while
  still deriving that set via the walkability predicate, as this plan intended. `is_walkable`
  itself is unchanged and still implements exactly `verify_occupancy`'s first two checks —
  only the BFS neighbor-acceptance test inside `analyze_connectivity` changed. This does not
  affect the real `dungeon_crawl` corpus result (Step 3 reproduced 15,245/1/100.0% exactly, no
  drift), since that world's terrain dict is effectively wall-enclosed; it matters for the
  synthetic fixtures in Step 2 and for `analyze_connectivity`'s general-purpose correctness on
  any terrain dict that isn't perfectly wall-enclosed. No other part of the plan changed.
