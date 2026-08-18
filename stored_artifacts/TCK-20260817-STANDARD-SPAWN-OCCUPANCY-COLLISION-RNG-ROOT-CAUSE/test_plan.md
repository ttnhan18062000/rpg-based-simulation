---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE
artifact_type: test_plan
tags: [world, bug, determinism, root-cause, debugging, testing]
---

# Test Plan

## Normal flow
- `tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision`
  (updated) — real compile of `unit_information_density` seed=42, asserts zero
  `LAW-SPAWN-OCCUPANCY` violations, entity 6 at (27, 38), entity 14 elsewhere.
- `tests/engine/test_hard_law_monitor.py::test_check_initial_placement_full_population_scan_unit`
  — synthetic two-entity collision fixture, unchanged, continues to prove the detection mechanism
  itself still works independent of any real-world case being fixed.
- `tests/engine/test_hard_law_monitor.py::test_seed137_and_seed999_no_initial_placement_violations`
  — negative control (`wilderness_survival`), unchanged, still passes.

## Edge cases
- Fully-packed region fallback path in `_resolve_entity_spawn_tile()` (raster scan, then
  last-resort collision-tolerant return) — not exercised by any real corpus world (none is densely
  packed enough), covered only by code inspection/reasoning in this ticket, not a dedicated unit
  test. Documented as a known gap in Assumptions/Open Questions rather than silently asserted safe.
- Entity placement order: verified the earlier-placed entity of a colliding pair (entity 6, lower
  ID) is never perturbed, only the later one (entity 14) — checked directly via the real
  `unit_selfmodel_pilot` seed=42 reproduction, not just reasoned about.

## Failure modes
- Determinism: 3x repeated `WorldCompiler.compile()` of the same world/seed must produce an
  identical `report["state_hash"]` and identical full entity-position map — checked directly.
- Non-regression on non-colliding entities: full 63-combo (18 worlds × 3 seeds) before/after
  position diff must show zero changed positions for any entity that wasn't part of a collision
  before the fix — checked directly via a scripted sweep, not sampled.
- Live-run confirmation: a real 20-tick `Kernel` run on the exact `unit_selfmodel_pilot` seed=42
  reproduction from the ticket must produce zero `hard_law_violations.jsonl` records (both
  `LAW-SPAWN-OCCUPANCY` at init and the downstream `LAW-OCCUPANCY-COLLISION` at tick 7 from the
  original alert log must both be gone, not just the init-time one).

## Regression-prone paths (existing test suites re-run, not just the new/changed test)
- `tests/engine/test_hard_law_monitor.py` (full file) — 14/14 passed.
- `tests/integration/observability/test_initial_placement_check.py` — 2/2 passed.
- `tests/unit/worldbuilding/` (full dir) — 122/122 passed.
- `tests/unit/worldassembly/ -m "not slow"` — 120 passed, 33 deselected (slow-marked, out of
  scope for this pass per repo testing rule — not exhaustively run, see ticket Out of Scope).
- `tests/unit/worldmodules/` + `tests/integration/kernel/` — 145 passed, 1 pre-existing failure
  (`test_long_run_determinism.py::test_1000_tick_determinism`, wall-clock watchdog timeout,
  independently reproduced on the unmodified base branch via `git stash` before being ruled
  unrelated to this change).

## Result
All planned checks executed and passed except the one pre-existing, independently-confirmed
unrelated failure noted above. No test was skipped without an explicit reason recorded here.
