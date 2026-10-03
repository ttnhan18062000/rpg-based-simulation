---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-SHAPE-METRIC
phase: done
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-SHAPE-METRIC

## Title
Shape validation metric: connected-component fill-ratio and rotation detection

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Shape metric — connected-component-aware fill-ratio plus rotation/repetition detection — into real production code, motivated by a real corpus finding that 78.8% of measured biome components across 18 worlds score >=0.95 fill-ratio (near-perfectly rectangular), including one exact case of a 90-degree-rotated duplicate component pair.

## Scope
- Implement connected_components() over AuthoritativeState.terrain, written fresh from experiments/spatial_rendering/PROPOSAL.md's inline algorithm/prose since no prototype file exists to promote
- Implement per-component fill-ratio scoring
- Implement rotation/repetition detection between components
- Pure visualization/geometry computation only — zero data-lookup checks
- Document the known fill-ratio weakness (composite of unioned rectangles scoring artificially low/organic) as a stated limitation in code/docstrings, not solved in this ticket

## Out of Scope
- Calibrating or tuning the 0.95 threshold (separate ticket, TCK-20260821-VISUAL-QUALITY-CALIBRATION)
- Subclassing PillarScorer or integrating with SimQ's event pipeline — this is an architecturally independent sibling, not a pillar
- Any grade-band/scoring combination logic (TCK-20260821-VISUAL-GRADE-SCORER's scope)

## Acceptance Criteria
- [x] connected_components() run on the dungeon_crawl world's AuthoritativeState.terrain reproduces the documented result of FOREST being 2 components of 1,116 tiles each, not 1
- [x] Per-component fill-ratio reproduces the documented values: CAVE=0.980, FOREST-c0=1.000, FOREST-c1=1.000, RUIN=1.000
- [x] Rotation detection reproduces the documented 90-degree-rotation finding between the two FOREST components
- [x] A corpus-wide run across all 18 worlds reproduces 26/33 components scoring >=0.95, with every sub-0.95 component being FOREST type — reproduced against the *current* 21-world corpus instead (37/46 = 80.4% >=0.95, every sub-0.95 component FOREST type), per plan.md's explicit "Decision: AC #4 Corpus Scope" (option b): a hardcoded 3-world exclusion list to force the stale historical 26/33 figure was rejected as check-vs-substance gaming; the qualitative invariant (high majority >=0.95, every exception FOREST) is what's asserted and holds at any corpus size. See plan.md for full reasoning.
- [x] No PillarScorer subclass is created and no ObservabilityEventEnvelope/QualityHub import exists in this module

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/PROPOSAL.md
- src/core/state.py
- src/simulation_quality/scorers/base.py
- src/simulation_quality/pillars.py
- config/simulation_quality/grade_thresholds.yaml

## Assumptions / Open Questions
- The 0.95 fill-ratio threshold is uncalibrated and provisional until the calibration ticket runs
- No prototype script exists for this logic despite the 'promote' framing — it must be written fresh from PROPOSAL.md
- simulation-quality: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary and mirrors its precedent rather than being part of the SimQ subsystem itself

## Implementation Notes

Implemented per staging_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/plan.md's 8 steps exactly,
with zero deviations:

- **Step 1** — `src/rendering/shape.py` created with the provenance docstring, `ShapeComponent`
  frozen dataclass (`terrain_type`, `tiles`, `size`, `bbox`, `fill_ratio`), and
  `group_terrain_by_type()` keyed on the raw, non-normalized terrain string.
- **Step 2** — `_bfs_component()` (fresh copy of `connectivity.py`'s BFS shape, not imported)
  and `connected_components(terrain, min_size=20, excluded_types=frozenset({"PLAIN","ROAD"}))`,
  looping over `group_terrain_by_type()`'s groups and running BFS once per distinct raw
  terrain-type string, scoped to that type's own tile set. Exclusion test is
  `tval.upper() in excluded_types` (case-insensitive), grouping key stays raw-cased.
- **Step 3** — `compute_bbox()` and `compute_fill_ratio()`, both operating per-component
  (never per-terrain-type aggregate); `connected_components()` calls both before constructing
  each `ShapeComponent`.
- **Step 4** — `_normalize()` and `detect_rotation_match()`, using the CORRECTED rotation
  formula from the plan's revised Step 4 (`(x,y) -> (y, w_a - x)` for CW,
  `(x,y) -> (h_a - y, x)` for CCW, where `w_a`/`h_a` are bbox extents, not tile counts — no
  extra `+1`/`-1`). Docstring includes the solid-rectangle caveat verbatim as required.
- **Step 5/6** — verified, not new code: module imports only `from __future__ import
  annotations`, `collections.deque`, `dataclasses.dataclass`; no `PillarScorer` subclass; no
  `src.simulation_quality.*` / `src.observability.events` / `src.rendering.{png_writer,render,
  incremental}` import; no in-place mutation of the input `terrain` dict (confirmed by
  AST-based static tests and a mutation-guard runtime test).
- **Step 7** — `tests/unit/rendering/test_shape.py` created with all 13 planned tests (Tests
  1-10, 12-14). Test 11 (the hardcoded 26/33 historical-subset reproduction) deliberately NOT
  written, per plan.md's explicit Decision.
- **Step 8** — `docs/parity_ledger/infrastructure.yaml` — re-checked the file's actual tail
  immediately before appending (`INFRA-371` confirmed as the real current max ID, matching the
  plan's own re-check), appended `INFRA-372` (P2, status `verified`) with the same 8-field
  shape as `INFRA-370`/`INFRA-371`. YAML re-parsed successfully after the edit (377 total
  entries).

Corpus-wide sweep against the current, live `data/worlds/` corpus (21 worlds, not the
historical 18) reproduces investigation.md's numbers exactly: 46 measurable components, 37
>=0.95 (80.4%), 9 below 0.95, every single below-threshold component `forest` type with zero
exceptions.

No architectural conflicts encountered; no scope-guard file was touched (verified via `git
status --porcelain` showing only the 4 intended file changes: `src/rendering/shape.py` (new),
`tests/unit/rendering/test_shape.py` (new), `docs/parity_ledger/infrastructure.yaml` (edit),
and this ticket file).

## Test Summary

`PYTHONPATH=. .venv/bin/python3 -m pytest tests/unit/rendering/ -v` — **38 passed** (13 new
`test_shape.py` tests + 25 pre-existing sibling/regression tests, all unmodified and still
green).

`PYTHONPATH=. .venv/bin/python3 -m pytest tests/simulation_quality/ -q` — **41 failed, 499
passed, 12 skipped** — the 41 failures are exactly the pre-existing, documented
`test_grade_regression.py::test_grade_within_anchor_band*` failures (unrelated `PROGRESSION`-
pillar score-tolerance drift, matching both prior sibling tickets' own established baseline and
the plan's Step 7 Verify note verbatim); zero new failures introduced by this ticket's diff.

Real-corpus numbers reproduced exactly (dungeon_crawl, seed 42, tick 0):
`cave=1849 tiles, bbox=(20,60)-(60,105), fill_ratio=0.9804`;
`forest c0=1116 tiles, bbox=(50,30)-(85,60), fill_ratio=1.0000`;
`forest c1=1116 tiles, bbox=(95,20)-(125,55), fill_ratio=1.0000`;
`ruin=1681 tiles, bbox=(60,80)-(100,120), fill_ratio=1.0000`.
Rotation check: the two FOREST components (bboxes 36x31 and 31x36) match via
`detect_rotation_match`.

## Files Changed

- `src/rendering/shape.py` (new) — the metric module itself.
- `tests/unit/rendering/test_shape.py` (new) — 13 tests (Tests 1-10, 12-14 per the plan).
- `docs/parity_ledger/infrastructure.yaml` (edit) — appended `INFRA-372` entry.
- `tickets/inprogress/TCK-20260821-VISUAL-SHAPE-METRIC.md` (this file) — Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary updated.
- `staging_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/investigation.md`,
  `staging_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/plan.md`,
  `staging_artifacts/TCK-20260821-VISUAL-SHAPE-METRIC/test_plan.md` — created earlier this run's
  own Investigate/Plan phases (not by this Implement step, but part of this run's real
  changeset per ticket-hygiene requirements); read and followed exactly, not further edited
  during Implement.

## Completion Summary

Implemented `src/rendering/shape.py`, a new sibling module to `connectivity.py`/`density.py`
providing connected-component-aware fill-ratio (per-terrain-type BFS labeling, never a
terrain-type aggregate) and 90-degree rotation/repetition detection between components, plus
its full test suite (`tests/unit/rendering/test_shape.py`, 13 tests) and a new P2 parity ledger
entry (`INFRA-372`). All 5 acceptance criteria are satisfied against real corpus data — AC #4
specifically against the *current* 21-world corpus rather than the ticket's now-stale
historical "18 worlds" wording, per plan.md's explicit, reasoned Decision. All scope guards (no
`PillarScorer`, no SimQ/observability imports, no render/image dependency, no edits to any
forbidden file) held and are independently enforced by dedicated tests.

**Real bug caught during Review, not silently glossed over.** The first Review pass (plan.md,
Step 4) returned `NEEDS_CHANGES`: the reviewer found and independently verified an off-by-one
bug in the rotate-90-CW/CCW formula (`w_a - 1 - x` / `h_a - 1 - y` instead of `w_a - x` /
`h_a - y`, where `w_a`/`h_a` are bounding-box extents, not tile counts) that produced
negative-coordinate junk and would have silently broken the plan's own Test 7 while AC #3
stayed masked (the transpose test alone already matched the real FOREST pair). The orchestrator
independently reproduced the bug with a synthetic case, applied the fix, and re-dispatched
Review; the fix was independently reverified a second time (against both the real dungeon_crawl
FOREST pair and the Test 7 synthetic scenario) before Review returned `APPROVED`. Full technical
detail lives in `plan.md`'s Step 4 note and `shape.py`'s `detect_rotation_match` docstring — this
is only the process-traceability summary. Implementation itself, once dispatched against the
corrected plan, had zero further deviations.
