---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT
phase: done
date: 2026-10-10
tags: []
---

# TCK-20261010-BASELINE-COMPARISON-FLOW-TEST-WALL-CLOCK-DEPENDENT

## Title
`test_baseline_comparison_and_cli_flow` fails on a loaded machine: the simulation watchdog trips on wall-clock tick time and turns the expected PASS into WARNING

## Status
DONE

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
1. [x] The test passes with an artificially slowed tick, injected in the test, that would have
   tripped the watchdog before the fix.
2. [x] The test still fails if the comparison flow it covers regresses: its real assertion is kept.
3. [x] (CI integration job, read from the PR) `pytest tests/integration/observability/` passes.

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

### Triage 2026-10-20 (testing-implementer, read-only)
- STILL REAL on main b753a9b08. One local run failed at tests/integration/observability/test_baseline_comparison_flow.py:55, `assert res_run.status == "PASS"`, which came back 'WARNING'. The test runs a real ScenarioSweeper sweep (L15-30); the watchdog's wall-clock tick time feeds health_score, and nothing pins timing. A loaded host reproduces it deterministically (a good AC1 reproducer).
- The file routes to rpg (tests/**). **rpg-planner OK'd it, 2026-10-20: testing-implementer fixes it test-only.** Conditions:
  - the comparison assertion stays unchanged;
  - timing is pinned or injected through an EXISTING seam (a fixture or monkeypatch on the watchdog clock); a new seam in src/ needs rpg-planner first;
  - fold in rpg's sibling TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100 (the generation-flow health_score mean is 99, not 100; likely the same wall-clock cause) if one injection fixes both. rpg hands over the ticket text, and the PR closes it.
  - Not sim behaviour, so it can go before or after v1.

## Implementation Notes
- Cause (measured, not assumed): in the sweep the first run's first ticks are slow (seed 1: tick_compute_ms_avg 108.6, p95 199.9; seeds 2 and 3: about 8-9). The metric window feeds BasicRuntimeAnalyzer's HighCPULatencyRule (avg > 50 ms), a WARNING that scores the run 95; the baseline then has health mean 99 / threshold 96, and the compared run's 95 is `Metric envelope degraded: actual 95.0 < baseline threshold 96.0`, so WARNING.
- Fix, test only: `tests/integration/observability/conftest.py` fixture `tick_cost_ms`, a monkeypatch on the existing seam `LiveSignalSource.tick_end_signals` (the one place a measured tick cost becomes PressureSignals) that records a fixed compute cost. No src/ change. The flow tests pin 5 ms; the L55 comparison assertion and the rest of the test are unchanged.
- AC1: `test_a_slow_tick_is_what_trips_the_cpu_latency_rule` injects 59 ms ticks (the figure observed on a loaded VM) and shows every run's average compute is over the 50 ms limit, so the injection is real; the flow test passes on this loaded host, 2 of 2 runs, where it failed before.
- Folded in: TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100 (rpg-planner's sibling). Same cause (the 95 is one HighCPULatencyRule WARNING on the slow first run, so it is wall clock, not an engine change); `test_baseline_generation_and_cli_flow` uses the same fixture and passes with its mean 100.0 assertion unchanged.

## Test Summary
tests/integration/observability/test_baseline_comparison_flow.py and test_baseline_generation_flow.py: 4 passed, twice, on a loaded host. CI read from the PR.

## Files Changed
- tests/integration/observability/conftest.py (new fixture)
- tests/integration/observability/test_baseline_comparison_flow.py
- tests/integration/observability/test_baseline_generation_flow.py

## Completion Summary
The two baseline flow tests no longer depend on the host's tick speed; the cause was a HighCPULatencyRule WARNING on a slow first run.
