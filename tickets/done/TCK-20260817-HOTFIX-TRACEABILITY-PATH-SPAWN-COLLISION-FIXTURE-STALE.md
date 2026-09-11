---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-TRACEABILITY-PATH-SPAWN-COLLISION-FIXTURE-STALE
phase: done
date: 2026-08-17
tags: [simulation-quality, testing, bug]
---

# TCK-20260817-HOTFIX-TRACEABILITY-PATH-SPAWN-COLLISION-FIXTURE-STALE

## Title
`test_spawn_occupancy_violation_reaches_world_pillar_via_real_kernel_construction` relied on a
now-fixed spawn collision as its test fixture — force the collision instead of relying on it
occurring naturally

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI failure on the "Simulation quality" job (run 32045090041, commit f372e39f). The user
reported "the workflow is running, but the Simulation quality failed." Investigation found the
raw CI log unreachable from this sandbox (network policy blocks the Azure Blob Storage log
delivery domain — confirmed via a "Fortinet Secure DNS Service Portal — Web Page Blocked!" page,
not a TLS certificate issue as `gh`'s own error message misleadingly suggests). Reproduced
locally instead: a naive local repro showed 33 failures, but 32 of those were a local-environment
artifact — `data/calibration/` is git-ignored, so those `test_grade_within_anchor_band` tests
correctly skip on a real fresh CI checkout (confirmed by temporarily moving `data/calibration/`
aside locally: only 1 test failed, matching what a clean CI checkout would see).

The one real failure: `tests/simulation_quality/test_traceability_path.py::
test_spawn_occupancy_violation_reaches_world_pillar_via_real_kernel_construction`. Its own
docstring named its exact fixture dependency — the seed=42 `unit_information_density` entity
6/entity 14 tile (27,38) spawn collision — which
`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` (this session, same day) fixed.
That ticket correctly updated the sibling detection-side test
(`tests/engine/test_hard_law_monitor.py::test_seed42_entity6_entity14_tile_27_38_collision`) to
assert the collision's absence, but did not include `tests/simulation_quality/` in its own
verification scope, so this routing-side sibling test (which relies on the SAME collision
existing, for a different purpose — proving event routing, not detection) was missed.

## Scope
- `tests/simulation_quality/test_traceability_path.py`: force the entity-6/entity-14 collision
  immutably (`dataclasses.replace`) on the compiled state, post-`WorldCompiler.compile()` and
  pre-`Kernel` construction, instead of relying on it occurring naturally. This still exercises
  the full real Kernel construction + event-routing pipeline end-to-end (the test's actual
  purpose) — only the precondition (two entities starting on the same tile) is now deliberately
  constructed. Matches the same-file-family precedent already established by
  `test_hard_law_monitor.py::test_check_initial_placement_full_population_scan_unit`, which
  forces a synthetic collision on a minimal hand-built state for the identical reason.

## Out of Scope
- Any change to `src/worldbuilding/compiler.py` or the spawn-placement fix itself — correct,
  already verified and closed.
- The 32 `test_grade_within_anchor_band` local-only failures — confirmed to be an artifact of
  this dev machine's locally-accumulated, git-ignored `data/calibration/` snapshots, not present
  or reproducible on a real fresh CI checkout. No fix needed.
- Auditing every other test in the repo for a similar stale-collision-fixture dependency —
  `test_hard_law_monitor.py`'s own docstring cross-references this exact regression source, and a
  full-file `tests/simulation_quality` + `tests/engine/test_hard_law_monitor.py` run (both clean,
  post-fix) is sufficient verification for this specific, disclosed gap.

## Acceptance Criteria
- [x] `test_spawn_occupancy_violation_reaches_world_pillar_via_real_kernel_construction` passes.
- [x] Full `pytest tests/simulation_quality -m "not slow and not extra_slow"` passes cleanly with
      `data/calibration/` absent (simulating a real fresh CI checkout).
- [x] `tests/engine/test_hard_law_monitor.py` (the sibling file, already touched by the spawn-fix
      ticket) still passes — no interaction/regression.
- [x] No `src/` file changed.

## Related Tickets
- `TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE` (the fix that made this
  test's old fixture stale)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `tests/simulation_quality/test_traceability_path.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Added `import dataclasses` and, after `WorldCompiler.compile()`, force entity 14 onto entity 6's
exact `navigation.position` via `dataclasses.replace()` (both `NavigationComponent` and the
entity itself are frozen dataclasses, matching this repo's durable-state immutability
architecture — this is test-fixture setup code building the Kernel's initial input state, not a
runtime mutation of live authoritative state) before constructing the real `Kernel`. Updated the
test's docstring to explain why the collision is now forced rather than natural, cross-referencing
both the fixing ticket and the sibling `test_hard_law_monitor.py` precedent for the same pattern.

## Test Summary
- `pytest tests/simulation_quality/test_traceability_path.py::test_spawn_occupancy_violation_reaches_world_pillar_via_real_kernel_construction -v` — 1 passed.
- `pytest tests/simulation_quality -m "not slow and not extra_slow" --tb=short -q` with
  `data/calibration/` temporarily moved aside (simulating a fresh CI checkout) — 461 passed, 64
  skipped, 27 deselected, 0 failed.
- `pytest tests/engine/test_hard_law_monitor.py -q` — 12 passed (no regression).

## Files Changed
- `tests/simulation_quality/test_traceability_path.py`

## Completion Summary
Root-caused the real "Simulation quality" CI failure to a stale test fixture that depended on a
spawn collision this same session's own earlier fix (`TCK-20260817-STANDARD-SPAWN-OCCUPANCY-
COLLISION-RNG-ROOT-CAUSE`) correctly eliminated — a real gap in that ticket's own test-scope
(`tests/simulation_quality/` was not included in its verification). Fixed by forcing the
collision as an explicit fixture precondition instead of relying on it occurring naturally,
following the exact pattern this repo already established for the same reason in the sibling
`test_hard_law_monitor.py` file. Also confirmed the other 32 tests that failed in a naive local
repro are a `data/calibration/`-presence artifact specific to this dev machine, not a real CI
issue and not requiring any fix.
