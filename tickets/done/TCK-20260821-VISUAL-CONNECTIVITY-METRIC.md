---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-CONNECTIVITY-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-CONNECTIVITY-METRIC

## Title
Connectivity validation metric: whole-map walkable-region reachability

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Connectivity metric — whole-map walkable-region reachability via BFS — into real production code.

## Scope
- Implement a BFS connectivity function over AuthoritativeState.terrain/blocked_tiles, reusing LegalityServiceV2.verify_occupancy's exact walkability rule (terrain != "WALL" minus blocked_tiles) rather than re-deriving it
- Return raw structural facts (walkable tile count, connected-component count) plus a derived percent-reachable value, not just a boolean
- Pure geometry computation, no data-lookup checks
- New tests covering both a fully-connected case and a constructed >=2-disconnected-island fixture

## Out of Scope
- Grade-band/scoring integration (TCK-20260821-VISUAL-GRADE-SCORER's scope)
- CI-gating this metric — report-only, never CI-gated
- Expanding evidence beyond dungeon_crawl to other worlds (single-world/single-seed evidence is accepted here; broader multi-world coverage is TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope)

## Acceptance Criteria
- [x] BFS connectivity function using exactly LegalityServiceV2.verify_occupancy's walkability rule reproduces the documented dungeon_crawl result: 15,245 walkable tiles, 1 connected component, 100% reachable
- [x] Function returns raw structural facts (walkable count, component count) plus derived percent-reachable, not just a pass/fail boolean
- [x] New test covers a fully-connected map case
- [x] New test covers a constructed map with >=2 disconnected islands
- [x] Tests live under tests/unit/, with no tests/parity/ marker applied

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/legality.py
- src/core/state.py
- src/simulation_quality/pillars.py
- experiments/spatial_rendering/PROPOSAL.md

## Assumptions / Open Questions
- Evidence base is currently single-world/single-seed (dungeon_crawl only); broader coverage is deferred to the calibration ticket
- The dependency on the renderer ticket is structural/sequencing per epic ordering — the metric itself only needs AuthoritativeState.terrain/blocked_tiles, not actual rendered pixels
- simulation-quality tag: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary rather than being part of the SimQ subsystem itself

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260821-VISUAL-CONNECTIVITY-METRIC/plan.md`'s four
steps, with one necessary bug fix discovered during Step 2/3 testing (see Deviations below,
mirrored into `plan.md`).

- **Step 1** (`src/rendering/connectivity.py`): `ConnectivityResult` dataclass,
  `is_walkable(pos, terrain, blocked_tiles)` implementing exactly
  `LegalityServiceV2.verify_occupancy`'s first two checks (`terrain.get(pos) == "WALL"` then
  `pos in blocked_tiles`, `src/engine/legality.py:71-77`), and `analyze_connectivity(terrain,
  blocked_tiles)` running a deque-based 4-directional BFS flood-fill over the precomputed
  `walkable_tiles` set. `percent_reachable = (largest component size / total walkable count) *
  100`, `0.0` if no walkable tiles exist.
- **Step 2/3** (`tests/unit/rendering/test_connectivity.py`): 6 tests total — 5 synthetic
  (fully-connected 5x5, 2-island 9/9=50%, 3-island 9/6/3=50%, blocked-tiles-only barrier,
  mutation guard calling `analyze_connectivity` twice and diffing pre/post snapshots) plus the
  real-corpus test.
- **Step 4** (`docs/parity_ledger/infrastructure.yaml`): appended `INFRA-370` directly after
  `INFRA-369`, `status: verified`, `priority: P2`, since Step 3's real-corpus test reproduced
  the documented numbers exactly on first run after the bug fix below.

**Real-corpus result (Step 3, AC #1):** `test_dungeon_crawl_matches_documented_evidence`
loaded `data/worlds/dungeon_crawl` via `WorldRepository.load_world` + `WorldCompiler.compile(seed=42)`
and reproduced **walkable_count == 15245, component_count == 1, percent_reachable == 100.0**
— an exact match to the documented evidence in `PROPOSAL.md:429` /
`idea_world_render_validation.md:42`. No drift found; `INFRA-370` is `status: verified`, not
`divergent`.

**Deviation from plan (bug found and fixed during testing, not an architecture re-litigation):**
The plan's Step 1 instructed adapting the ported BFS so "the membership test used inside the
BFS loop is `is_walkable(nb, terrain, blocked_tiles)` instead of `nb in tiles_of_type`."
Implemented literally, this hangs/times out on every synthetic fixture with an open boundary
(any grid not fully enclosed by explicit `"WALL"` terrain entries): `is_walkable` calls
`terrain.get(pos)`, which returns `None` (not `"WALL"`) for any coordinate absent from the
`terrain` dict, so an unbounded neighbor re-check treats the entire infinite 2D plane outside
the fixture as walkable and BFS never terminates. Caught immediately by the test suite (a
120s sandbox timeout on the first synthetic test, `tests/conftest.py`'s
`TimeoutError("Test execution exceeded the resource time limit.")`) — not a corner case, it
reproduces on the very first, simplest test (`test_connected_map_is_one_component_fully_reachable`,
a plain 5x5 open grid). Fixed by checking `nb in walkable_tiles` (the precomputed, closed set
of walkable coordinates already filtered by `is_walkable` from `terrain.keys()`) instead of
re-calling `is_walkable(nb, ...)` directly inside the BFS loop — this restores the original
`PROPOSAL.md:362-380` algorithm's bounded-membership structure (`nb in tiles_of_type`) while
still deriving that set via the walkability predicate. `is_walkable` itself is unchanged and
still matches `verify_occupancy`'s rule exactly; only the BFS neighbor-acceptance test changed.
This does not affect the real `dungeon_crawl` corpus result (that world's terrain dict is
presumably wall-enclosed, so the two formulations would have agreed there), but it is required
for the synthetic fixtures' correctness and, more importantly, for `analyze_connectivity` to be
safe to call on any terrain dict that isn't perfectly wall-enclosed — a reasonable expectation
for a general-purpose pure function. Full explanation recorded as a code comment at the fix
site (`src/rendering/connectivity.py`) since it is a non-obvious constraint. Mirrored into
`staging_artifacts/TCK-20260821-VISUAL-CONNECTIVITY-METRIC/plan.md`'s new "Deviations" section.

**Informational notes (from architecture review, not required to act on):**
1. No automated drift detector exists between `legality.py`'s two static-terrain checks and
   `connectivity.py`'s local re-implementation — only the code comment/docstring citing exact
   line numbers (`src/engine/legality.py:71-77`) ties them together. If `verify_occupancy`'s
   first two checks change shape in the future, `connectivity.py` will not automatically be
   flagged; re-confirmed manually this session via `tests/unit/world/test_local_environment_semantics.py`
   and `tests/unit/domains/optimization/test_occupancy_snapshot.py` (both pass, walkability
   rule unchanged since the investigation was written).
2. The organic-terrain noise-fill batch (commit `eba0db48`) is opt-in via `terrain_variant`
   and none of `dungeon_crawl`'s 4 world modules use it — confirmed it did not affect this
   ticket's real-corpus test (exact match, no drift).

## Test Summary

Ran (via `PYTHONPATH=. .venv/bin/python3 -m pytest ...`, since bare `python3`/`pytest` in this
sandbox lacks `pydantic`):

- `pytest tests/unit/rendering/ -v` — **15 passed** (6 new connectivity tests + 9 pre-existing
  renderer tests, all still green, confirming the new sibling module didn't disturb
  `src/rendering/`'s existing surface).
- `pytest tests/unit/world/test_local_environment_semantics.py tests/unit/domains/optimization/test_occupancy_snapshot.py -v`
  — **10 passed** (confirms `LegalityServiceV2.verify_occupancy`'s walkability rule this
  ticket reuses is unchanged since the investigation was written).

No `tests/parity/` marker used anywhere; no grading/scoring/threshold assertions added; no
corpus-sweep beyond `dungeon_crawl`; nothing wired into any CI-gating/baseline script.

## Files Changed
- `src/rendering/connectivity.py` (new) — `ConnectivityResult`, `is_walkable`, `analyze_connectivity`
- `tests/unit/rendering/test_connectivity.py` (new) — 6 tests (5 synthetic + 1 real-corpus)
- `docs/parity_ledger/infrastructure.yaml` (modified) — new `INFRA-370` entry, `status: verified`
- `staging_artifacts/TCK-20260821-VISUAL-CONNECTIVITY-METRIC/plan.md` (modified) — added
  "Deviations" section documenting the BFS neighbor-membership bug fix
- `tickets/inprogress/TCK-20260821-VISUAL-CONNECTIVITY-METRIC.md` (this file, modified) —
  Implementation Notes, Test Summary, Files Changed, Completion Summary, Acceptance Criteria
  checkboxes, Status

## Completion Summary
Implemented `src/rendering/connectivity.py` (BFS whole-map walkable-region connectivity,
reusing `verify_occupancy`'s static-terrain walkability rule exactly) and its full test
coverage (`tests/unit/rendering/test_connectivity.py`, 6 tests: fully-connected,
2-island 50/50, 3-island 9/6/3, blocked-tiles-only barrier, mutation guard, and a real
`dungeon_crawl` corpus reproduction). The real-corpus test reproduced the documented evidence
exactly (15,245 walkable tiles, 1 component, 100.0% reachable), so `docs/parity_ledger/infrastructure.yaml`
gained `INFRA-370` at `status: verified`, `priority: P2`. One real bug was found and fixed
during implementation: literally following the plan's BFS-neighbor-adaptation instruction
caused unbounded flood-fill on any non-wall-enclosed grid; fixed by checking neighbor
membership against the precomputed `walkable_tiles` set instead of re-calling `is_walkable`
on arbitrary coordinates. All scope guards (no edits to `legality.py`, `state.py`,
`simulation_quality/`, other `data/worlds/*`, existing renderer files, or the deferred idea
doc) were respected.
