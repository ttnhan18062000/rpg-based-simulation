---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT
phase: open
date: 2026-10-10
tags: []
---

# TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT

## Title
`test_baseline_comparison_and_cli_flow` fails on a loaded machine: the simulation watchdog trips on wall-clock tick time and turns the expected PASS into WARNING

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Reported by perf-planner on 2026-10-10, carried here by lead-planner because rpg-planner, the
owner, is on the other host.

`tests/integration/observability/test_baseline_comparison_flow.py::test_baseline_comparison_and_cli_flow`
depends on the wall clock. On a loaded VM, one tick took 59 ms against the watchdog's 50 ms limit.
The run's `health_score` came out `WARNING` where the test expects `PASS`, so the test failed. It
fails the same way on a clean `origin/main` (`312fbd78c`), so perf's M2 X1 change did not cause it.
See #484 (merged) and #486.

## Scope
- Make the test's expectation independent of real tick timing. Either fix or mock the tick timing
  the watchdog reads, or configure the run so the watchdog cannot affect the asserted health
  result.
- The repo has **no** timing-sensitive pytest marker (`pyproject.toml` `[tool.pytest.ini_options]
  markers`). Do not add a skip or retry in place of a deterministic fix.

## Out of Scope
- Any change to the watchdog's limits or to `health_score` semantics in `src/`.

## Acceptance Criteria
1. The test passes with an artificially slowed tick, injected in the test, that would have
   tripped the watchdog before the fix.
2. The test still fails if the comparison flow it covers regresses: its real assertion is kept.
3. `pytest tests/integration/observability/` passes.

## Related Tickets
- PR #484, PR #486 (perf, where it was observed)

## Related Docs
- `docs/architecture/simulation_watchdog.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tests/integration/observability/test_baseline_comparison_flow.py`, the simulation watchdog
(`src/engine/`)

## Assumptions / Open Questions
- The fixed tick-timing approach versus the watchdog-off approach is the implementer's call. Either
  must keep the test deterministic.

## Implementation Notes
(Open.)

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
