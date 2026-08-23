---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-DENSITY-METRIC
phase: open
date: 2026-08-21
tags: [visualization, simulation-quality, world]
---

# TCK-20260821-VISUAL-DENSITY-METRIC

## Title
Density validation metric: nearest-neighbor CV and terrain histogram

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Promote the Density metric — entity nearest-neighbor coefficient of variation plus terrain-type histogram — into real production code.

## Scope
- Implement nearest-neighbor coefficient-of-variation (CV) function over entity positions, written from the documented one-off verification numbers (sandbox_world≈0.648, dungeon_crawl≈0.678) since no prototype file exists
- Implement terrain-type histogram computation, reusing/extracting the terrain_histogram side effect already committed in render_world.py rather than reimplementing it
- Both metrics computed as a Tier-0 pure-data path, zero image required
- Treat clustering CV as a non-monotonic, healthy-band signal (not "more is better"/dormancy-style single-direction rule) at the raw-metric level

## Out of Scope
- Multi-seed calibration of healthy-band thresholds (TCK-20260821-VISUAL-QUALITY-CALIBRATION's scope)
- Switching to Kernel.get_world_indexes/entities_by_tile for O(N) scaling — current O(N^2) is acceptable at today's entity counts (11-32); flag only, do not implement
- Any grade-band/scoring combination logic (TCK-20260821-VISUAL-GRADE-SCORER's scope)

## Acceptance Criteria
- [x] Nearest-neighbor CV function reproduces sandbox_world≈0.648 and dungeon_crawl≈0.678 within a stated tolerance
- [x] Terrain histogram dict values sum exactly to len(state.terrain)
- [x] Both metrics are computed via a Tier-0 pure-data path with zero image/render dependency
- [x] No PillarScorer subclass is created and no SimQ event-pipeline import exists in this module

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/engine/kernel.py
- src/core/dirty.py
- experiments/spatial_rendering/prototype/render_world.py
- src/simulation_quality/pillars.py

## Assumptions / Open Questions
- Nearest-neighbor CV was never committed to a prototype file; the AC tolerance for reproducing sandbox_world/dungeon_crawl numbers must be finalized during implementation
- Entity counts stay low enough (11-32) that O(N^2) is acceptable for now; Kernel.get_world_indexes is flagged, not adopted, in this ticket
- simulation-quality: this metric is an architecturally-independent SimQ-sibling (not a PillarScorer/pillar), tagged for topical adjacency since it reuses SimQ's grade vocabulary rather than being part of the SimQ subsystem itself

## Implementation Notes

Implemented per the approved `staging_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/plan.md`,
all 4 steps, no deviations from the algorithmic content:

- **Step 1** — `src/rendering/density.py`: `DensityResult` (`@dataclass(frozen=True)`, fields
  `cv`, `entity_count`, `nn_distances`) and `compute_density_cv(entities: dict) -> DensityResult`.
  Filters to `EntityState.active`, reads `EntityState.position`, computes Euclidean
  nearest-neighbor distance per active entity (O(N²), intentional per Out of Scope), and
  `cv = statistics.pstdev(nn_distances) / statistics.mean(nn_distances)` — population stdev
  (ddof=0), with an explicit inline comment on why not `statistics.stdev()` (ddof=1). Guards
  `entity_count < 2` by returning `cv=0.0, nn_distances=[]` instead of calling `pstdev`/`mean`
  on an empty/degenerate list.
- **Step 2** — same file, `compute_terrain_histogram(terrain: dict) -> dict[str, int]`,
  extracted verbatim from `experiments/spatial_rendering/prototype/render_world.py:90-95`'s
  counting logic (`histogram[tval] = histogram.get(tval, 0) + 1` over `terrain.values()`),
  no key normalization — `'PLAIN'`/`'plain'` remain distinct keys by construction.
- **Step 3** — `tests/unit/rendering/test_density.py`, all 10 tests from the plan/test_plan.md
  list: 2 real-corpus CV reproduction tests (`round(cv, 3) == 0.648` / `0.678`), 1
  population-vs-sample-stdev regression guard (hand-computed 3-entity fixture, positions
  `(0,0)`/`(1,0)`/`(3,0)`, `nn_distances=[1,1,2]`, expected pop CV
  `0.3535533905932738`, asserted to differ from the sample-stdev variant by >1e-3), 1
  two-entity edge case, 1 inactive-entity-exclusion test, 2 histogram sum-invariant tests
  (synthetic mixed-case + real `dungeon_crawl`), 2 AST-based static architecture guards
  (AC #3: no image/render import; AC #4: no `PillarScorer` subclass, no
  `simulation_quality`/`observability.events` import), 1 mutation guard (calls both functions
  twice, asserts input dicts unchanged). All 25 tests in `tests/unit/rendering/` pass (10 new
  + 15 pre-existing, all pre-existing still green).
- **Step 4** — `docs/parity_ledger/infrastructure.yaml`: re-confirmed the file's actual current
  max id directly (`grep -n "^- id:"`, still `INFRA-370` at both the initial and pre-append
  check — no concurrent writer since investigation.md's read) and appended `INFRA-371` (P2,
  `status: verified`, `v2_evidence: src/rendering/density.py`,
  `test_path: tests/unit/rendering/test_density.py::test_dungeon_crawl_reproduces_documented_cv`).
  Validated the whole file still parses as valid YAML after the append (`yaml.safe_load`,
  376 entries total).

**One deviation from `test_plan.md`, not from `plan.md`:** `test_plan.md`'s "Scoped Pytest
Commands" section names `tests/unit/simulation_quality/` as the anti-coupling regression
directory to run. That path does not exist — the actual directory is `tests/simulation_quality/`
(no `unit/` prefix), confirmed via `find`. Ran the real directory instead
(`tests/simulation_quality/`): 499 passed, 12 skipped, 41 failed — all 41 failures are in
`tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band*`, a
pre-existing PROGRESSION-pillar score-tolerance drift tied to a known
`detection_params.yaml` tick-budget/dormancy threshold issue (confirmed by reading one
failure's assertion output directly — it names the exact known cause inline). Confirmed via
`git status` that this ticket's diff added only new files (`src/rendering/density.py`,
`tests/unit/rendering/test_density.py`, staging artifacts) and touched zero existing file
under `src/simulation_quality/` or `tests/simulation_quality/`, so these 41 failures are
unrelated to and pre-date this ticket's change — reported here per CLAUDE.md's "no known
material gap left unstated," not fixed (fixing SimQ pillar calibration is explicitly this
ticket's Out of Scope and belongs to a different, unrelated ticket). The suite's still-green
499/499 non-`test_grade_regression.py` tests remain the actual anti-coupling evidence for
AC #4 that this ticket's regression surface was meant to establish.

## Test Summary

`PYTHONPATH=. .venv/bin/python3 -m pytest tests/unit/rendering/ -v`: 25 passed (10 new in
`test_density.py`, 15 pre-existing, all green, zero regressions).

Real-corpus CV values reproduced exactly: `sandbox_world` (seed 42, tick 0, 18 active
entities) → `cv = 0.6478017242079448` (rounds to documented `0.648`); `dungeon_crawl` (seed
42, tick 0, 32 active entities) → `cv = 0.6782405727873148` (rounds to documented `0.678`).

`PYTHONPATH=. .venv/bin/python3 -m pytest tests/simulation_quality/ -q`: 499 passed, 12
skipped, 41 failed — all 41 in `test_grade_regression.py`, pre-existing/unrelated (see
Implementation Notes deviation above), not caused by this ticket's diff.

`python3 -c "import yaml; yaml.safe_load(...)"` on `docs/parity_ledger/infrastructure.yaml`:
parses cleanly, 376 entries, `INFRA-371` present as the last entry.

## Files Changed

- `src/rendering/density.py` (new)
- `tests/unit/rendering/test_density.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (added `INFRA-371` entry)
- `tickets/inprogress/TCK-20260821-VISUAL-DENSITY-METRIC.md` (this file — Status, AC
  checkboxes, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `staging_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/investigation.md`,
  `staging_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/plan.md`,
  `staging_artifacts/TCK-20260821-VISUAL-DENSITY-METRIC/test_plan.md` (present in the
  working tree as untracked staging artifacts from this ticket's own Investigate/Plan
  phases — listed here per ticket-hygiene requirement, not authored by this implementer
  turn)

## Completion Summary

Implemented `src/rendering/density.py` (new module, following
`src/rendering/connectivity.py`'s exact shape: frozen-dataclass result, pure functions over
raw `entities`/`terrain` dicts, provenance docstring) with `compute_density_cv` — a
nearest-neighbor coefficient-of-variation metric over active entity positions, using
population standard deviation (`statistics.pstdev`, ddof=0, not `stdev`'s ddof=1) — and
`compute_terrain_histogram`, extracted verbatim from the prototype's counting logic with no
key normalization. Added 10 new tests in `tests/unit/rendering/test_density.py` covering
exact real-corpus CV reproduction (sandbox_world ≈0.648, dungeon_crawl ≈0.678), a
population-vs-sample-stdev regression guard, edge cases, histogram sum-invariants, and two
AST-based static architecture guards enforcing AC #3/#4 (no image/render dependency, no
`PillarScorer` subclass or SimQ/observability import). Added parity ledger entry `INFRA-371`
(P2, verified). All 4 acceptance criteria are satisfied and checked. No edits were made to
any file in the ticket's Scope Guards list.
