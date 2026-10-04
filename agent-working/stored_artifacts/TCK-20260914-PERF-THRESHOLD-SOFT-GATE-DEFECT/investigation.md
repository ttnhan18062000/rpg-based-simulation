---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT
date: 2026-10-04
tags: [performance, testing]
---

# Investigation: TCK-20260914-PERF-THRESHOLD-SOFT-GATE-DEFECT

## Current call-site inventory (regenerated 2026-10-04 with `tools/perf/perf_threshold_inventory.py`)

- 55 call sites: 49 `assert_perf_threshold`, 6 `perf_check`. This is the inventory the ticket's Scope asked for;
  it already exists as `docs/performance/performance_clause_inventory.md` §7, checked in CI by
  `tests/tools/test_perf_inventories_committed_in_sync.py`.
- 0 pass a literal `hard=True`; 0 write an explicit `hard=False`; 52 leave `hard` absent (soft default).
- 3 pass `hard` through a variable: `tests/perf/conftest.py` (2, `PerfBudget.assert_within_budget`) and
  `tests/perf/test_perf_regression_baseline.py:40`. Their callers leave it at the default, so they are soft too.
- 45 of 55 carry a `slow` marker, so the PR job deselects them.

## The live evidence the ticket cites

`test_perf_metropolis_stress` (1000) and `test_perf_metropolis_longevity` (500) breach their own soft limits and
report green. Re-measured today for longevity: avg TPS 1.84 against the 5.0 limit, `BREACHED`, test passed.
(Note: `build_metropolis_state` had a spawn-collision defect until `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION`
closed today; avg TPS was 1.84 before and after that fix, so the breach does not come from it.)

## Disposition evidence

1. Owner's gate rule, `performance_optimization_roadmap.md`, "Gate definition and partial lift", item 2: "no soft
   check becomes blocking". AC2 (harden stable call sites) cannot be met without breaking it.
2. M4 owns the migration (`performance_m4_baseline_gate_a_epic.md`): gap-table row for
   `tests/tools/perf_assertions.py` ("Calibrate stable PR tripwires, make selected checks hard, and retain
   controlled confirmation for noisy capacity claims"); candidates PERF-M4-T02 (PR-fast performance tripwire:
   "Blocking deterministic smoke comparison"), PERF-M4-T07 (evidence-bundle contract), and PERF-M4-T10 (benchmark
   manifest and preflight validation, "no-silent-skip rules"). Authority is PERF-D4 (performance-contract authority).
3. Open question handed to M4: keep `hard=False` as the default, or require every call site to choose. Keep soft
   default: fewest edits, but a new call site is silently non-blocking. Require explicit: new sites must declare
   intent, but touches all 55 sites and the helper signature (a `tests/` edit, out of this ticket).
